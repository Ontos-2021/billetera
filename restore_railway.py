"""\
Restaura un backup cifrado (.sql.enc) generado por backup_postgres_local.py
hacia una base PostgreSQL (p.ej. Railway).

Requiere:
- BACKUP_FERNET_KEY en variables de entorno
- psql accesible en PATH (o pasar --psql)

Uso típico (REEMPLAZAR TODO):
  python restore_railway.py --db-url "%DATABASE_URL%" --enc backups_db_...sql.enc --drop-public

Nota: --drop-public elimina TODO el contenido actual del esquema public.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from dotenv import load_dotenv


def _mask_db_url(db_url: str) -> str:
    try:
        u = urlparse(db_url)
        if not u.scheme or not u.netloc:
            return "<db-url>"
        # netloc: user:pass@host:port
        masked_netloc = re.sub(r":([^@]+)@", ":***@", u.netloc)
        return u._replace(netloc=masked_netloc).geturl()
    except Exception:
        return "<db-url>"


def _get_fernet() -> Fernet:
    key = os.getenv("BACKUP_FERNET_KEY")
    if not key:
        raise RuntimeError("BACKUP_FERNET_KEY no está definido en el entorno.")
    try:
        return Fernet(key)
    except Exception:
        return Fernet(key.encode())


def _find_psql(psql_arg: str | None) -> str:
    if psql_arg:
        p = Path(psql_arg)
        if p.exists():
            return str(p)
        raise RuntimeError(f"No existe el ejecutable psql: {psql_arg}")

    psql = shutil.which("psql")
    if psql:
        return psql

    raise RuntimeError(
        "No se encontró 'psql' en PATH. Instala el cliente de PostgreSQL (PostgreSQL tools) "
        "o pasa la ruta con --psql (ej: C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe)."
    )


def _psql_env() -> dict[str, str]:
    """Environment overrides for psql.

    En Windows, si la consola está en cp1252/win1252, psql puede asumir un
    client encoding distinto y producir mojibake (ej: CafÃ©). Forzamos UTF-8.
    """

    env = dict(os.environ)
    env.setdefault("PGCLIENTENCODING", "UTF8")
    return env


def _decrypt_to_sql(enc_path: Path, sql_out: Path) -> None:
    fernet = _get_fernet()
    encrypted = enc_path.read_bytes()
    decrypted = fernet.decrypt(encrypted)
    sql_out.write_bytes(decrypted)


def _dump_has_schema(sql_text: str) -> bool:
    return bool(re.search(r"^\s*CREATE\s+TABLE\b", sql_text, flags=re.IGNORECASE | re.MULTILINE))


def _quote_ident_chain(ident: str) -> str:
    """Quote a possibly-qualified identifier like schema.table or just table."""
    ident = ident.strip()
    if not ident:
        return ident
    # If it's already quoted, keep as-is.
    if ident.startswith('"') and ident.endswith('"'):
        return ident
    parts = [p.strip() for p in ident.split('.') if p.strip()]
    if not parts:
        return ident

    def quote_part(part: str) -> str:
        if part.startswith('"') and part.endswith('"'):
            return part
        return '"' + part.replace('"', '""') + '"'

    return '.'.join(quote_part(p) for p in parts)


_INSERT_RE = re.compile(
    r'^(?P<prefix>INSERT\s+INTO\s+)(?P<table>[^\s(]+)\s*\((?P<cols>[^)]*)\)(?P<suffix>\s+VALUES\s*\()?',
    flags=re.IGNORECASE | re.MULTILINE,
)


_TS_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
)


_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _quote_unquoted_temporals_in_insert_line(line: str) -> str:
    """Quote unquoted timestamp/date literals in a single INSERT line.

    The manual dump generator writes non-strings via str(val). For datetime/date
    objects, this yields tokens like `2025-11-16 03:55:41.8123+00:00` without
    quotes, which Postgres rejects. We only touch content *outside* of single
    quoted strings.
    """

    if not line.lstrip().upper().startswith("INSERT INTO"):
        return line

    out: list[str] = []
    i = 0
    in_str = False
    n = len(line)

    while i < n:
        ch = line[i]

        if in_str:
            out.append(ch)
            if ch == "'":
                # Handle escaped quote in SQL string: ''
                if i + 1 < n and line[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_str = False
            i += 1
            continue

        # Not in string
        if ch == "'":
            in_str = True
            out.append(ch)
            i += 1
            continue

        # Try timestamp match at this position
        m = _TS_RE.match(line, i)
        if m:
            token = m.group(0)
            out.append("'")
            out.append(token)
            out.append("'")
            i = m.end()
            continue

        # Common JSONField empty containers from Python str(dict/list)
        # - dict -> {}
        # - list -> []
        if ch == '{' and i + 1 < n and line[i + 1] == '}':
            out.append("'{}'")
            i += 2
            continue
        if ch == '[' and i + 1 < n and line[i + 1] == ']':
            out.append("'[]'")
            i += 2
            continue

        # Try date-only match at this position, but avoid double-quoting timestamps
        m2 = _DATE_RE.match(line, i)
        if m2:
            token = m2.group(0)
            # If it's followed by space/T and time, _TS_RE would have matched.
            out.append("'")
            out.append(token)
            out.append("'")
            i = m2.end()
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _quote_unquoted_temporals_in_inserts(sql_text: str) -> str:
    changed = False
    lines: list[str] = []
    for line in sql_text.splitlines(keepends=True):
        if line.lstrip().upper().startswith("INSERT INTO"):
            fixed = _quote_unquoted_temporals_in_insert_line(line)
            if fixed != line:
                changed = True
            lines.append(fixed)
        else:
            lines.append(line)
    return "".join(lines) if changed else sql_text


def _quote_insert_columns(sql_text: str) -> str:
    """Quote column identifiers in INSERT statements.

    The manual dump generator writes INSERT columns without quoting. Some columns
    (e.g. "primary") are reserved keywords in Postgres and cause syntax errors.
    """

    def repl(match: re.Match) -> str:
        prefix = match.group('prefix')
        table = match.group('table')
        cols = match.group('cols')
        suffix = match.group('suffix') or ''

        quoted_table = _quote_ident_chain(table)

        col_items = [c.strip() for c in cols.split(',') if c.strip()]
        quoted_cols: list[str] = []
        for col in col_items:
            # Already quoted?
            if col.startswith('"') and col.endswith('"'):
                quoted_cols.append(col)
            else:
                quoted_cols.append('"' + col.replace('"', '""') + '"')

        return f"{prefix}{quoted_table} ({', '.join(quoted_cols)}){suffix}"

    return _INSERT_RE.sub(repl, sql_text)


def _list_public_tables(psql: str, db_url: str) -> list[str]:
    # -A unaligned, -t tuples-only
    out = subprocess.check_output(
        [psql, db_url, "-A", "-t", "-c", "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"],
        text=True,
        env=_psql_env(),
    )
    tables = [line.strip() for line in out.splitlines() if line.strip()]
    return tables


def _terminate_other_connections(psql: str, db_url: str) -> None:
    """Termina otras conexiones a la misma DB.

    En Railway suele haber conexiones del servicio web; TRUNCATE/DROP puede
    quedarse esperando locks. Intentamos liberar el lock matando sesiones.
    """
    sql = (
        "SELECT pg_terminate_backend(pid) "
        "FROM pg_stat_activity "
        "WHERE datname = current_database() "
        "AND pid <> pg_backend_pid();"
    )
    print("🔌 Terminando otras conexiones activas...")
    subprocess.check_call([psql, db_url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql], env=_psql_env())


def _truncate_all_tables(psql: str, db_url: str, *, lock_timeout_seconds: int) -> None:
    tables = _list_public_tables(psql, db_url)
    if not tables:
        raise RuntimeError(
            "No se encontraron tablas en el esquema public. "
            "Si acabas de crear la DB, primero ejecuta migrations (Django manage.py migrate) para crear el esquema."
        )

    quoted = ", ".join('"' + t.replace('"', '""') + '"' for t in tables)
    sql = f"SET lock_timeout = '{int(lock_timeout_seconds)}s'; TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"
    print(f"🧹 Vaciando {len(tables)} tablas (TRUNCATE ... CASCADE)")
    subprocess.check_call([psql, db_url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", sql], env=_psql_env())


def _fix_sequences(psql: str, db_url: str) -> None:
        """Ajusta secuencias (SERIAL/IDENTITY) al MAX(pk) tras INSERT explícitos.

        El dump manual inserta IDs pero no corre setval(), lo que puede dejar las
        secuencias apuntando a valores antiguos y provocar colisiones.
        """

        do_block = r"""
DO $$
DECLARE
    r RECORD;
    max_id BIGINT;
BEGIN
    FOR r IN
        SELECT
            ns.nspname AS schema_name,
            seq.relname AS seq_name,
            tbl.relname AS table_name,
            col.attname AS column_name
        FROM pg_class seq
        JOIN pg_namespace ns ON ns.oid = seq.relnamespace
        JOIN pg_depend dep ON dep.objid = seq.oid
        JOIN pg_class tbl ON tbl.oid = dep.refobjid
        JOIN pg_attribute col ON col.attrelid = tbl.oid AND col.attnum = dep.refobjsubid
        WHERE seq.relkind = 'S'
            AND ns.nspname = 'public'
    LOOP
        EXECUTE format('SELECT COALESCE(MAX(%I), 1) FROM %I.%I', r.column_name, 'public', r.table_name) INTO max_id;
        EXECUTE format('SELECT setval(%L, %s, true)', r.schema_name || '.' || r.seq_name, max_id);
    END LOOP;
END $$;
"""

        print("🔧 Ajustando secuencias (setval)")
        subprocess.check_call([psql, db_url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", do_block], env=_psql_env())


def _build_wrapper_sql(wrapper_path: Path, inner_sql_path: Path) -> None:
        """Genera un wrapper para ejecutar el SQL con checks relajados y rollback seguro."""

        # Usamos meta-comandos de psql (\i) para incluir el SQL real.
        # session_replication_role=replica evita fallos por FK/orden de inserts.
        content = """\\set ON_ERROR_STOP on
    \\encoding UTF8
    BEGIN;
    SET session_replication_role = replica;
    \\i {inner}
    SET session_replication_role = origin;
    COMMIT;
    """.format(inner=str(inner_sql_path).replace('\\', '/'))

        wrapper_path.write_text(content, encoding="utf-8")


def _run_with_heartbeat(cmd: list[str], *, every_seconds: int, label: str) -> None:
    """Run a subprocess and print periodic heartbeats while it executes."""
    start = time.time()
    next_tick = start + max(1, int(every_seconds))
    proc = subprocess.Popen(cmd, env=_psql_env())
    try:
        while True:
            rc = proc.poll()
            if rc is not None:
                if rc != 0:
                    raise subprocess.CalledProcessError(rc, cmd)
                return

            now = time.time()
            if now >= next_tick:
                elapsed = int(now - start)
                print(f"⏳ {label}... ({elapsed}s)")
                next_tick = now + max(1, int(every_seconds))

            time.sleep(0.5)
    except KeyboardInterrupt:
        proc.terminate()
        raise


def _run_psql(
    psql: str,
    db_url: str,
    sql_path: Path,
    *,
    drop_public: bool,
    truncate_all: bool,
    lock_timeout_seconds: int,
    terminate_connections: bool,
) -> None:
    masked = _mask_db_url(db_url)
    print(f"\n📡 Conectando a: {masked}")

    if drop_public:
        print("⚠️  --drop-public ACTIVADO: se eliminará el esquema public (TODO el contenido actual).")
        if terminate_connections:
            _terminate_other_connections(psql, db_url)
        ddl = f"SET lock_timeout = '{int(lock_timeout_seconds)}s'; DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
        subprocess.check_call([psql, db_url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", ddl], env=_psql_env())

    if truncate_all:
        if terminate_connections:
            _terminate_other_connections(psql, db_url)
        _truncate_all_tables(psql, db_url, lock_timeout_seconds=lock_timeout_seconds)

    print(f"📥 Restaurando SQL: {sql_path.name}")
    wrapper_path = sql_path.with_suffix(sql_path.suffix + ".wrapper.sql")
    _build_wrapper_sql(wrapper_path, sql_path)
    _run_with_heartbeat(
        [psql, db_url, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-f", str(wrapper_path)],
        every_seconds=15,
        label="Restaurando SQL",
    )

    _fix_sequences(psql, db_url)


def main() -> int:
    # Cargar variables desde .env si existe (DB URL, BACKUP_FERNET_KEY, etc.)
    load_dotenv()

    parser = argparse.ArgumentParser(description="Descifra y restaura un backup .sql.enc a PostgreSQL (Railway).")
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL") or os.getenv("RAILWAY_DATABASE_URL"),
        help="URL de conexión PostgreSQL del destino (Railway). También puede venir de DATABASE_URL.",
    )
    parser.add_argument(
        "--enc",
        default="backups_db_development_postgres-20251208-200445.sql.enc",
        help="Ruta al archivo .sql.enc en disco.",
    )
    parser.add_argument(
        "--psql",
        default=None,
        help="Ruta explícita a psql.exe si no está en PATH.",
    )
    wipe = parser.add_mutually_exclusive_group()
    wipe.add_argument(
        "--truncate-all",
        action="store_true",
        help="Vacía todas las tablas del esquema public y reinicia IDs (recomendado para dumps solo INSERT).",
    )
    wipe.add_argument(
        "--drop-public",
        action="store_true",
        help="Elimina el esquema public antes de restaurar (solo útil si el dump incluye CREATE TABLE).",
    )

    parser.add_argument(
        "--lock-timeout",
        type=int,
        default=15,
        help="Timeout (segundos) para locks durante TRUNCATE/DROP. Evita que se quede colgado esperando.",
    )
    parser.add_argument(
        "--no-terminate-connections",
        action="store_true",
        help="No intenta terminar otras conexiones activas antes de TRUNCATE/DROP.",
    )

    args = parser.parse_args()

    if not args.db_url:
        print("❌ Falta --db-url (o variable DATABASE_URL/RAILWAY_DATABASE_URL)", file=sys.stderr)
        return 2

    enc_path = Path(args.enc)
    if not enc_path.exists():
        print(f"❌ No existe el archivo: {enc_path}", file=sys.stderr)
        return 2

    psql = _find_psql(args.psql)

    print("🔐 Descifrando backup...")
    with tempfile.TemporaryDirectory() as tmp:
        sql_path = Path(tmp) / (enc_path.stem + ".sql")
        _decrypt_to_sql(enc_path, sql_path)
        # Post-proceso: este dump es "solo INSERT" (no incluye DDL) y además no cita columnas.
        try:
            text = sql_path.read_text(encoding="utf-8")

            if args.drop_public and not _dump_has_schema(text):
                raise RuntimeError(
                    "Este backup no contiene CREATE TABLE (solo INSERT). "
                    "No se puede usar --drop-public porque dejaría la DB sin tablas. "
                    "Usa --truncate-all (y asegúrate de haber ejecutado migrations para crear el esquema)."
                )

            text2 = _quote_insert_columns(text)
            text3 = _quote_unquoted_temporals_in_inserts(text2)

            if text3 != text:
                sql_path.write_text(text3, encoding="utf-8")
        except UnicodeDecodeError:
            # Si por alguna razón no es UTF-8, dejamos el archivo tal cual.
            pass
        print("✅ Backup descifrado")
        _run_psql(
            psql,
            args.db_url,
            sql_path,
            drop_public=args.drop_public,
            truncate_all=args.truncate_all,
            lock_timeout_seconds=args.lock_timeout,
            terminate_connections=not args.no_terminate_connections,
        )

    print("\n✅ Restore completado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
