# 📋 Auditoría 360 + Plan de Mejora — Billetera Virtual (MoneyFlow Mirror)

> Fecha de la auditoría: 2026-06-29
> Alcance: estado técnico + producto + innovación + monetización de `billetera/`
> Base de evidencia: `settings.py`, `requirements.txt`, `Readme.md`, `CHANGELOG.md`, `AUDITORIA_PRIORIDADES_TECNICAS.md`, `docker-compose.yml`, `Dockerfile`, `entrypoint.sh`, `urls.py`, `models.py` de `usuarios` y `gastos`.

---

## 1. Veredicto Ejecutivo

Billetera Virtual es un **MVP serio, ya endurecido**, no un prototipo. Tiene dominio financiero real (gastos, ingresos, cuentas, transferencias, deudas, monedas, compras globales), aislamiento por usuario, JWT + Google OIDC con PKCE, webhook de Mercado Pago firmado, backups cifrados a R2, CI, health checks y ~159-165 tests. La parte interesante: ya existe un modelo `Plan`/`Suscripcion` (`FREE/PRO/PREMIUM`) **sembrado pero sin monetización activa** — el upside estratégico está ahí, no implementado.

**Madurez: MVP avanzado / beta cerrada.** No es production-hardened, pero ya pasó la fase de "demo que sobrevive a un demo". Le faltan observabilidad, rate limiting, un esquema claro de tests en zonas sensibles y, sobre todo, **decisión de producto**: es un SaaS multiusuario, una app personal, o ambos.

---

## 2. Snapshot de Evidencia

### Stack y arquitectura
- Django 4.2 + DRF + SimpleJWT + django-allauth + dj-rest-auth (Google OIDC/PKCE).
- PostgreSQL en prod, SQLite en dev. `conn_max_age=600` (pooling básico).
- Media en Cloudflare R2 vía `django-storages`. Static vía WhiteNoise.
- WeasyPrint para PDFs. Docker slim con `postgresql-client` y libs Cairo/Pango.
- Railway (Procfile) como plataforma principal; Coolify como alternativa Docker.

### Señales concretas de madurez
| Señal | Evidencia |
|---|---|
| Deploy determinista | `entrypoint.sh` hace `makemigrations --check --dry-run` antes de migrar |
| Política de permisos invertida | `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES = IsAuthenticated` |
| Webhook firmado | `MERCADOPAGO_WEBHOOK_SECRET` + idempotencia por `payment_id` |
| Backups seguros | Fernet + R2, token **solo por header**, retención configurable |
| CI obligatoria | `.github/workflows/ci.yml` corre `check` + `test` en push/PR |
| Health checks | `/health/` y `/healthz` validan DB activa |
| Hardening HTTP | HSTS, SSL redirect, cookies Secure, X-Frame DENY en prod |
| Suite de tests | ~159-165 tests, cubren privacidad, webhook, backup, API |
| Modelos de monetización | `Plan` y `Suscripcion` ya existen como campos en DB |

### Señales de fragilidad / deuda
- `settings.py` deriva URLs desde múltiples plataformas (`RAILWAY_STATIC_URL`, `EXTERNAL_URL`, fallbacks ya limpiados pero la lógica sigue complicada).
- `entrypoint.sh` mezcla check, migración con retry, collectstatic y `bootstrap_google_socialapp` en un solo arranque — no hay separación build/release/run.
- `db.sqlite3` commiteado en el repo (`billetera/db.sqlite3`).
- `Dockerfile` usa Python 3.11 pero README e instructions dicen 3.12.
- `urllib3==1.26.20` anclado — relativamente viejo frente a `boto3==1.40.1`.
- `Procfile` y `entrypoint.sh` coexisten como dos entrypaths — riesgo de drift.
- `DEBUG` se lee independientemente de `ENV` (declarado en el comentario del settings) — significa que alguien podría setear `DEBUG=1` en producción por accidente.

---

## 3. Auditoría Técnica

### Riesgos de ingeniería más grandes
1. **`DEBUG` desacoplado de `ENV`.** El settings lo dice explícitamente: "Independiente del entorno para permitir debugging en producción". Eso es una pistola cargada. Un `DEBUG=1` olvidado en Railway expone trazas y rutas. **Cerrar urgentemente**: forzar `DEBUG = False` cuando `IS_PRODUCTION`.
2. **`db.sqlite3` versionado.** Contiene datos de desarrollo y viaja en el repo. Posible leak de datos y ruido en diffs. Borrar y `.gitignore`.
3. **Arranque monolítico.** `entrypoint.sh` es build + release + runtime en uno. Si `bootstrap_google_socialapp` falla, arranca igual (con `|| echo` que silencia errores). Hay que separar release-step del runtime.
4. **Sin rate limiting.** `/admin/tools/backup`, `/api/token/`, `/auth/social/google/` y el webhook de Mercado Pago no tienen throttle. Un ataque de fuerza bruta sobre el login social o el JWT es trivial hoy.
5. **No hay Sentry/error tracking.** El `AUDITORIA_PRIORIDADES_TECNICAS.md` lo marca como P1.7 aún abierto — el cambio de 2026-06-13 sólo subió health endpoint, no centralización de errores.
6. **Webhook sin replay protection más allá de `payment_id` approved.** Cubre approved, pero no está claro el manejo de `pending/rejected/cancelled` ni reintentos fuera de orden.
7. **`bootstrap_google_socialapp` silenciado.** `|| echo "Bootstrap command skipped"` oculta fallas reales de configuración OAuth en prod.
8. **Inconsistencia de versión Python.** Dockerfile=3.11, README/instructions=3.12. Django 4.2 + WeasyPrint 66 corren en 3.12 pero el contenedor no lo garantiza.

### Production-readiness gaps
- No hay logging estructurado (JSON logs para Railway/Datadog).
- No hay métricas (latencia, errores por endpoint, jobs de backup).
- No hay feature flags ni ambiente staging documentado.
- `restore_railway.py` existe pero no está probado en pipeline — restaurar backup es un músculo que nadie ha ejercitado.

### Code quality / maintainability
- Apps son razonablemente modulares (una por dominio).
- Hay muchos archivos `tests_*.py` por feature — bueno, pero fragmentado (12+ archivos de tests solo en `gastos`). Consolidar marcadores ayuda a onboarding.
- `usuarios/views.py` es el cajón de sastre (webhook MP, backup, perfil, PDF, inicio, health check). 4 concerns distintos en un módulo — candidato a split.

### Seguridad
- ✅ JWT con rotación + blacklist, cookies seguras, HSTS, CSRF origins explícitos.
- ✅ DRF cerrado por defecto.
- ⚠️ Sin rate limiting.
- ⚠️ `DEBUG` desbloqueado en prod.
- ⚠️ `db.sqlite3` en repo.
- ⚠️ Sin CSP headers.
- ⚠️ `bootstrap_google_socialapp` silencioso permite arrancar OAuth roto sin alertar.

### Performance
- `conn_max_age=600` bien, pero no hay pool real (pgbouncer) — en free tier Railway esto puede ahogarse bajo carga.
- Compras globales calculan `total` con `aggregate` en cada render — sin cache. A escala, el dashboard será lento.
- WeasyPrint PDF sincrónico — bajo concurrencia, bloquea workers.

---

## 4. Auditoría de Producto

**Qué parece ser:** Una app de finanzas personales multiusuario hecha en español (es-ar), centrada en el usuario argentino (Mercado Pago, ARS, etiquetado de tiendas tipo Carrefour/kiosco). Features de "compra global" con xN y tienda autocompletable son un detalle de UX que pocos apps de tracking personal tienen bien.

**Quién podría usarla:** Usuario argentino/latam que quiere tracking granular de gastos diarios, manejo de cuentas en múltiples monedas, control de deudas entre personas y reportes PDF imprimibles. No es para contadores ni empresas — es personal/hogar.

**Por qué alguien la usaría:**
- Compras globales (ticket con varios ítems) — la mayoría de apps lo mal-responden.
- Deudas Peer-to-Peer integradas al balance.
- Multi-moneda sin fricción.
- Login con Google + dashboard decente.

**Qué falta para que sea compelling (producto):**
1. **No hay app móvil.** Tracking de gastos ocurre cuando uno está en el kiosco. Una webapp responsive no gana retención frente a YNAB/MoneyLover/GV. Esta es la barrera #1.
2. **No hay importación automática** desde bancos/Mercado Pago. El modelo es "ingreso manual" — el dropoff más grande en fintech personal.
3. **No hay categorización inteligente** (ML). Hay `openai` en requirements pero no se ve uso visible — plausiblemente aspiracional.
4. **No hay consumo del `Plan/Suscripcion` real** — el gated feature no está definido. Hoy todo es FREE, presumiblemente.
5. **Onboarding cold start:** usuario nuevo enfrenta una pizarra vacía. Sin categorías sugeridas ni importe histórica, abandona.

---

## 5. Ángulo de Innovación

### Ideas no-obvias, rankeadas por leverage

1. **Alimentación automática desde Mercado Pago (account-linking, no solo webhook de cobros)**
   Hoy el webhook existe para **cobros salientes** (cobrar suscripciones). Pero Mercado Pago/BBVA/Brubank tienen APIs de **transacciones entrantes**. Si Billetera puede hacer pull de movimientos reales del usuario, deja de ser "otro app de tracking manual" y se vuelve "tus finanzas en vivo". *Leverage:* alto — ataca el abandon rate principal de todos los apps del segmento.

2. **"Deuda social" como feature viral — shared ledgers**
   El modelo de `Deuda` ya soporta deudor/acreedor. Si se convierte en **entidad compartida entre dos usuarios de Billetera** (invitar a tu amigo, ambos ven la misma deuda, ambos la pueden saldar), se convierte en un feature tipo Splitwise embebido — **adquisición orgánica**: cada deuda compartida es una invitación. *Leverage:* alto — distribuye el producto solo.

3. **Categorización LLM-driven + insights financieros conversacionales**
   `openai` ya está en requirements. Si se usa para (a) auto-categorizar compras a partir de la descripción del ticket y (b) generar un "diagnóstico financiero del mes" en lenguaje natural ("Gastaste 34% más en delivery vs abril, tu mayor riesgo es el rubro transporte"), el producto gana un upsell claro para el plan Premium. *Leverage:* medio-alto — completa el modelo de monetización.

4. **Reportes PDF como producto B2B vertical**
   El PDF con WeasyPrint ya funciona. Exportarlo a un nivel de "presupuesto mensual presentable para freelancer/monotributista" abre un niche: usuarios que necesitan reportar gastos a un contador. *Leverage:* medio — feature aspiracional pero diferenciado.

---

## 6. Caminos de Monetización

**Camino A — Freemium con suscripción mensual (PRO/PREMIUM)**
- *Por qué encaja:* `Plan`/`Suscripcion`/Mercado Pago webhook ya existen. Es el camino ortopédico, hay 90% del plumbing listo.
- *Qué cambiar:* definir gated features. Sugerencia libre: FREE = tracking manual hasta 50 movim./mes; PRO = sincronización Mercado Pago + reportes PDF + multi-moneda avanzada; PREMIUM = insights LLM + categorización automática + cuenta compartida.
- *Downside:* pricing en ARS es difícil por la inflación; en USD choca con la capacidad de pago del segmento. Otros apps gratuitos ejercen presión bajando WTP.

**Camino B — Afiliación / revenue share con Mercado Pago crédito**
- *Por qué encaja:* ya estás integrado con MP. MP tiene programa de referidos para créditos y cuentas. Si un usuario está visualizando su deuda y ve "préstame a tasa X desde Mercado Pago", clic → comisión.
- *Qué cambiar:* añadir un módulo "ofertas financieras" contextuales basadas en el análisis de deuda del usuario (cash flow negativo → oferta de préstamo; saldo ocioso → oferta de inversiones MP Invest).
- *Downside:* friction regulatoria + UX invasiva si se hace mal. Requiere trust del usuario que apenas estás construyendo.

**Camino C — B2B white-label para contadores / monotributistas**
- *Por qué encaja:* el motor de reportes PDF + multi-moneda ya está. Contadores en AR gestionan decenas de clientes cada uno — pagarían una suscripción para generar informes mensuales automatizados por cliente.
- *Qué cambiar:* multi-cliente por sesión de contador, plantillas de reporte configurables, firma/descarga batch.
- *Downside:* pivote de target — ya no es "personal", es "pro accountant tool". Distribución muy distinta (canales gremiales, charlas de CPCE). Costoso de landear.

**Camino D — Donaciones / "Buy me a mate" + plan PRO opcional**
- Para el usuario ARG, una app gratuita de tracking ya es valiosa. Capturar WTP puramente por suscripción es difícil. Combinar free total + propina opcional (Mercado Pago) + un plan PRO ultra-nichado (solo insights LLM y PDF branded) captura el segmento que paga por cariño y el que paga por valor agregado.
- *Qué cambiar:* muy poco — agregar botón de propina y restringir 2 features. *Downside:* ceiling de revenue bajo.

---

## 7. Estrategia IA — Movimiento de Diferenciación

### Objetivo real
No es "agregarle IA". Es **matar el cuello de botella que mata retención en toda app de finanzas personales: la fricción de entrada de datos**. Hoy Billetera Virtual exige que el usuario teclee cada gasto. Eso es la causa #1 de abandono en este segmento — y es exactamente el lugar donde IA genera asimetría real, no como chatbot decorativo sino como motor que elimina tipeo.

La pregunta correcta no es "¿le pongo IA?" sino "¿qué feature, hecho solo con IA, vuelve obscena la idea de hacerlo manual?". Esa es la única IA que vende.

### Movimientos de más alto apalancamiento (en orden)

**1. OCR de boletas/tickets con vision LLM — el wedge**
Foto del ticket → modelo de visión → `Gasto` ya creado, multi-ítem mapeado a `Compra` (que ya existe), categoría inferida, moneda detectada, tienda normalizada contra `Tienda`. **Esto es lo único que justifica pagar por la app.**
- Costo: GPT-4o-mini vision ~$0.01-0.015 por boleta. Sprint de 3-5 días.
- El modelo `Compra` con `items` y `cantidad` ya es la estructura ideal para un ticket multi-ítem.
- Diferencial local defendible: prompts para Coto, Carrefour, ChangoMas, "promo con tarjeta", "cuotas", "Mercado Pago" como método Y como wallet, ARS vs USD blue. **Esa es la fosa**, no el dashboard.

**2. Entrada por voz / screenshot de notificación**
"Gasté 3500 en el chino" → Whisper + NLU simple → `Gasto` creado. Screenshot de la push de MP "te pagaron X" → parsed → `Ingreso`. El usuario ya genera estos datos en WhatsApp todo el día; el move es interceptarlos en el canal donde ya viven. Telegram bot es el MVP más barato (vos nativa y el user ya lo tiene abierto). **2 días de MVP.**

**3. Consejos financieros proactivos, no reactivos**
El error clásico: poner IA como una pestaña "Preguntá a tu asistente". Cero adopción. Lo correcto: la app **te escribe primero**.
- "Vas a exceder el presupuesto en $8.000 si seguís este ritmo en delivery."
- "Detecté una suscripción de Netflix que subió de $4.000 a $7.000 este mes."
- "Tu gasto en nafta subió 30% vs junio — ¿cambiaste rutina o subió el preço?"

Job semanal + push via Telegram/WhatsApp. **La IA no es un botón, es un cron.** Convierte "veo un gráfico" en "la app me avisa" — delta entre retención de 2 meses y de 12.

**4. "Diagnóstico de fin de mes" conversacional**
Reemplazar el dashboard estático por una conversación: "¿Cómo voy?" → respuesta en lenguaje natural con 3 números puntuales y 1 recomendación. El dashboard queda como herramienta; la charla queda como default. La gente no quiere leer charts, quiere que le digan si está bien o mal.

### Diferenciación real vs competencia
| Quién | Lo que ya tienen | Lo que Billetera puede hacer que ellos no |
|---|---|---|
| Mercado Pago Cuentas | Los datos, fricción cero | **Interpretación + predicción**. MP te dice que gastaste X. Billetera te dice que vas a excederte y por qué. MP no va a hacer esto — no es su producto. |
| Splitwise | Deudas compartidas | Lo mismo + tracking personal completo. El modelo `Deuda` ya está. Extendelo a entidad compartida entre usuarios = viral. |
| YNAB / Fennel | Manual, US-céntrico, rígido | Contexto AR/latam: MP cuotas, ARS/USD blue, inflación como input, receipts en español. Eso ellos no lo van a hacer nunca. |
| ChatGPT puro | Gente ya pega receipts ahí | Persistencia + historial + automatización. ChatGPT no recuerda tu presupuesto ni te avisa el 15 del mes. |

La fosa no es "IA", es **IA + contexto local + memoria del usuario**. Cualquiera de los tres solo es clonable; los tres juntos compuestos es tu ventaja.

---

## 8. Plan de Mejora Provisorio

### Now (esta semana) — hardening crítico
1. **Forzar `DEBUG = False` en producción** desacoplándolo de la bandera manual. Una línea. Cierra la pistola cargada más obvia.
2. **Borrar `db.sqlite3` del repo** y meterlo en `.gitignore`. Posible leak de datos + ruido en diffs.
3. **Alinear Python 3.12 en Dockerfile** (sincronizar con README/instructions). Evita drift de runtime vs docs.
4. **Subir rate limiting** mínimo en `/api/token/`, `/admin/tools/backup`, `/auth/social/google/` (DRF Throttling, gratis). Cierra fuerza bruta trivial.
5. **Quitar el `|| echo` silencioso** del `bootstrap_google_socialapp` — debe fallar ruidosamente en prod si OAuth está mal configurado.

### Next (este mes / MVP strength)
6. **Integrar Sentry** (free tier 5K errores/mes, setup < 30 min). Cierra P1.7 aún abierto.
7. **Probar `restore_railway.py`** en un ambiente staging real — un backup que nunca se restorea es un backup que no existe.
8. **Definir el plan FREE/PRO feature gating** y consumir el modelo `Suscripcion.es_valida` en al menos un endpoint de pago (ej: PDF report). Hoy el modelo está tirado en el piso.
9. **Prototipar lectura de transacciones desde Mercado Pago** (no webhook de cobros, sino backoffice pull). Es el feature de retención cuello-de-botella.
10. **Split `usuarios/views.py`** en `usuarios/views_auth.py`, `views_webhook.py`, `views_backup.py`, `views_profile.py`.

### Later (trimestre / escala)
11. **PWA + offline-first** como puente a móvil sin coste de native — el tracking ocurre fuera de casa.
12. **Deuda compartida (Splitwise-like)** para adquisición viral.
13. **Insights LLM** consumiendo `openai` ya listado en requirements.
14. **pgbouncer** o pool real para no ahogar PostgreSQL en free tier.

### Wedge IA — el plan paralelo que decide el upside de producto

**Ahora (2 semanas):**
1. Endpoint `POST /api/gastos/ocr/` → recibe imagen, llama GPT-4o-mini vision, devuelve JSON estructurado, crea `Compra` con `items`. Usá el modelo `Compra` que ya existe.
2. Afirmar `openai` (ya en `requirements.txt` pero sin uso visible) — confirmar si hay aspiración o código muerto.
3. Prompts específicos para 5 cadenas locales (Coto, Carrefour, ChangoMas, Dia, kiosco genérico). Este dataset sí es el moat.

**Próximo (1 mes):**
4. Bot Telegram con voz + screenshot → `Gasto`/`Ingreso`. Sin clawback de UI.
5. Job semanal LLM de diagnóstico → mensaje proactivo.
6. Cerrar el modelo `Suscripcion`: el plan PRO = OCR ilimitado + insights. FREE = 5 OCRs/mes. **Hoy `Plan/Suscripcion` existe en DB pero no se consume en ninguna vista** — la monetización es la pieza tirada en el piso.

**Después (trimestre):**
7. PWA con acceso a cámara — el OCR requiere móvil, una web responsive no alcanza porque nadie abre la notebook en el kiosco.
8. `Deuda` compartida multiusuario (Splitwise embebido) = adquisición viral.
9. Categorización automática con few-shot del histórico del propio usuario.

### Métricas que tienen que mover si el plan es correcto
- **Inputs por semana por usuario activo** (el North Star). Hoy manual ≈ bajo. OCR/voz tiene que llevarlo a 5-10×.
- **% de gastos creados SIN teclado.** Meta inicial: 60%.
- **Retention W4.** Si no pasa de 25% con OCR, el wedge no es tan wedge.
- **Conversión FREE→PRO.** Si el OCR no empuja esto, no hay pricing power.
- **Costo LLM por usuario activo/mes.** Vigilar. GPT-4o-mini debe mantenerlo bajo $0.30/user/mes o el unit economics se rompe.

---

## 9. Hard Truth — Por qué muere si nada cambia

### Auditoría técnica
El mayor problema NO es un feature gap. Es **disciplina operativa, seguridad perimetral y consistencia de despliegue**. La base funcional existe y no está rota. El repo está más cerca de un MVP serio que de una app production-ready. Los cheats de hardening ya pasaron (P0-P1 de `AUDITORIA_PRIORIDADES_TECNICAS.md` están hechos), pero quedan grietas: `DEBUG` desacoplado, `db.sqlite3` en repo, sin rate limiting, `bootstrap_google_socialapp` silencioso, sin Sentry, sin restore probado.

### Auditoría de producto
La razón más probable de que este proyecto muera si nada cambia no es técnica — el código está por encima del promedio de un side project Django. Es **de producto**: Billetera Virtual compite en un mercado saturado de apps de finanzas personales, sin móvil, sin importación bancaria automática, y con un techo de monetización en ARS muy bajo. Una web app responsive de tracking manual **no retiene** frente a Mercado Pago "cuentas", Splitwise, Fennel, YNAB o incluso Google Sheets. El esfuerzo de hardening técnico se gasta en una superficie de producto que ya está commodity.

El modelo `Plan/Suscripcion` es **la columna vertebral olvidada**: existe en DB pero no se consume en ninguna vista. Hasta que no se decida **para qué se cobra y a quién**, todo el hardening es elegante pero estéril: estás endureciendo un puente hacia ninguna parte.

La jugada que tiene asimetría real es **deuda compartida + importación MP**. Es lo único que activa distribución viral Y stickiness a la vez. El resto es mantenimiento de una app más.

### Sobre la IA
"AI-native" como etiqueta es marketing muerto. **IA-native como UX** significa "nunca tecleás, nunca categorizás, nunca interpretás un chart — la app lo hace y te lo dice". Si solo le pegás un chatbot a un dashboard, estás en la misma tumba que Notion AI, Doordash AI y los cien "Copilot para X" que nadie usa.

El riesgo real no es que no funcione OCR. Es que lo construís, funciona, y **sigue siendo opcional** — el usuario todavía puede entrar por el form de "crear gasto" y lo sigue haciendo. Forzá el camino IA: el form legacy queda solo para edge cases, el flujo default es foto o voz. Si dejás ambos como first-class, todo el mundo terminará en el path de mayor fricción y el OCR será una curiosidad.

Segunda hard truth: el OCR en web responsive es película. La gente no fotografía boletas desde una notebook. **Sin PWA/cámara o app, este play no despega.** Eso es el costo real de tener el upside, no el modelo de IA.

Tercera hard truth: el modelo `Plan`/`Suscripcion` tirado en el piso significa que llevás semanas construyendo features sin tener quién pague por ellos. Cerrá el círculo FREE/PRO en paralelo al OCR, no después. Si no, otra vez estás endureciendo un puente a ninguna parte.

---

## 10. Checklist de Cierre Inmediato (acciones concretas)

```
[ ] settings.py: forzar DEBUG = False cuando IS_PRODUCTION (1 línea)
[ ] .gitignore: agregar `billetera/db.sqlite3` y borrar el archivo del repo
[ ] Dockerfile: FROM python:3.12-slim (alinear con README/instructions)
[ ] settings.py: agregar DRF DEFAULT_THROTTLE_CLASSES/rates
      - throttle en /api/token/, /admin/tools/backup, /auth/social/google/
[ ] entrypoint.sh: quitar `|| echo` del bootstrap_google_socialapp
[ ] integrar sentry-sdk (free tier) + DSN en env
[ ] documento runbook: cómo restorear un backup en staging (probar 1 vez real)
[ ] definir gated features FREE/PRO/PREMIUM y consumir Suscripcion.es_valida
[ ] spike: POST /api/gastos/ocr/ con GPT-4o-mini vision + modelo Compra existente
[ ] split usuarios/views.py en views_auth / views_webhook / views_backup / views_profile
```

---

## 11. Riesgos y Pruebas

- **Riesgo de despliegue** tras el cambio de `DEBUG`/rate limiting: deberán testearse en staging que no bloquea legítimamente los webhooks de MP (el throttle no debe tocar el webhook firmado — excluirlo por path).
- **Riesgo de OCR**: costo LLM sin techo. Meter budget guard por usuario en el modelo `Suscripcion` (FREE=5/mes, PRO=ilimitado con soft cap).
- **Riesgo de privacy**: la imagen del ticket contiene datos del usuario y del comercio. Política de retención: no almacenar la imagen, solo el JSON parseado, salvo feature opt-in "memoria de comprobante".
- **Pruebas automáticas a sumar:**
  - Test de `DEBUG=False` forzado en prod via settings override.
  - Test de throttle activo en `/api/token/` (N+1 requests → 429).
  - Test de `bootstrap_google_socialapp` fallando ruidosamente (no silenciado).
  - Test de OCR endpoint con stub de OpenAI (mock de respuesta vision).
  - Test de gated feature: usuario FREE bloqueado en PDF report, PRO permitido.

---

*Documento generado como consolidación de las dos auditorías (técnica + producto/IA) y plan de mejora provisorio. Revisar y re-priorizar tras cada sprint.*