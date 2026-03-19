# Prioridades Tecnicas Para Volver Deployable El MVP

## Objetivo

Este documento convierte la auditoria en una lista de issues concretos, priorizados y cerrables.

Meta realista: pasar de MVP funcional a despliegue confiable sin reescribir el producto.

## Avance actual

Implementado el 2026-03-19:

- P0.1 Eliminar `makemigrations` del runtime de produccion.
- P0.2 Cerrar permisos inseguros por defecto en DRF.
- P0.3 Endurecer el webhook de Mercado Pago.

Estado actual resumido:

- La base funcional existe y no esta rota: 153 tests pasan.
- El mayor problema no es feature gap sino disciplina operativa, seguridad perimetral y consistencia de despliegue.
- El repo esta mas cerca de un MVP serio que de una app production-ready.

## Criterio de Priorizacion

- P0: te puede romper produccion, abrir superficie de abuso o dejarte operar a ciegas.
- P1: no rompe hoy, pero frena confiabilidad, velocidad de cambio o monetizacion.
- P2: mejora estructura, costo operativo y expansion futura.

## P0

### 1. Eliminar makemigrations del runtime de produccion

Impacto:

Generar migraciones en runtime es una practica de bajo nivel. Hace el deploy no determinista y puede introducir drift entre codigo, base y artefactos desplegados.

Evidencia:

- Procfile ejecuta makemigrations en produccion.
- El entrypoint ya corre migrate, asi que hoy hay duplicacion de responsabilidades.

Archivos afectados:

- [Procfile](Procfile#L1)
- [entrypoint.sh](entrypoint.sh#L1)

Definicion de cierre:

- El deploy solo ejecuta migraciones ya versionadas.
- Si faltan migraciones, el pipeline falla antes de desplegar.
- Queda un unico punto de arranque para migrar y levantar la app.

Issue sugerido:

Quitar makemigrations de produccion y hacer fail-fast si el arbol de migraciones no esta alineado.

### 2. Cerrar permisos inseguros por defecto en DRF

Impacto:

Hoy el permiso global por defecto permite acceso abierto salvo que cada endpoint lo cierre manualmente. Eso es una trampa de seguridad clasica: el proximo endpoint puede nacer expuesto.

Evidencia:

- DEFAULT_PERMISSION_CLASSES esta en AllowAny.
- Algunos endpoints ya sobreescriben permisos, pero la base sigue siendo insegura.

Archivos afectados:

- [billetera/billetera/settings.py](billetera/billetera/settings.py#L120)
- [billetera/gastos/api_views.py](billetera/gastos/api_views.py#L8)

Definicion de cierre:

- El default pasa a IsAuthenticated o equivalente seguro.
- Los endpoints publicos quedan declarados explicitamente, no por accidente.
- Se agregan tests de acceso para endpoints API.

Issue sugerido:

Invertir la politica de permisos: todo cerrado por defecto, publico solo donde este justificado.

### 3. Endurecer el webhook de Mercado Pago

Impacto:

El flujo de cobro es la parte mas sensible del negocio. Hoy el webhook acepta POST sin validacion criptografica fuerte ni proteccion razonable contra replay.

Evidencia:

- El endpoint esta csrf_exempt.
- Existe MERCADOPAGO_WEBHOOK_SECRET en settings pero no se usa en la validacion del webhook.
- El codigo activa suscripciones tras consultar el pago, pero no verifica firma entrante.

Archivos afectados:

- [billetera/usuarios/views.py](billetera/usuarios/views.py#L631)
- [billetera/billetera/settings.py](billetera/billetera/settings.py#L324)

Definicion de cierre:

- Se valida firma o esquema oficial del proveedor.
- Se registra y deduplica el evento recibido.
- Se cubren pagos approved, eventos invalidos y reintentos.

Issue sugerido:

Implementar validacion del webhook de Mercado Pago con firma, idempotencia y tests.

### 4. Endurecer el endpoint de backup remoto

Impacto:

El endpoint de backup expone una operacion altamente sensible. Aceptar token por query string es mala practica porque filtra credenciales en logs, proxies e historiales.

Evidencia:

- El endpoint esta csrf_exempt.
- Acepta token por header, query string y POST.

Archivos afectados:

- [billetera/usuarios/views.py](billetera/usuarios/views.py#L425)

Definicion de cierre:

- El token solo se acepta por header.
- Se registra auditoria minima de ejecucion.
- Hay rate limiting o al menos endurecimiento por metodo y origen.
- El endpoint devuelve errores claros sin filtrar detalles sensibles.

Issue sugerido:

Reducir superficie del backup webhook y dejarlo apto para operacion automatizada segura.

### 5. Agregar CI minima obligatoria

Impacto:

Hoy la calidad depende de que alguien recuerde correr tests. Eso no escala ni protege merges malos.

Evidencia:

- No hay workflows en .github/workflows.
- La suite existe y pasa, pero no esta automatizada.

Definicion de cierre:

- Cada push o PR ejecuta manage.py check y manage.py test.
- Si se quiere mantener liviano, el workflow puede correr sobre SQLite para validacion basica.
- El estado del pipeline debe ser requisito de merge.

Issue sugerido:

Crear CI minima para checks y tests antes de cualquier deploy.

## P1

### 6. Unificar estrategia de despliegue

Impacto:

Koyeb, Railway y Render aparecen mezclados en settings, README y deploy scripts. Esa ambiguedad sube errores de configuracion, troubleshooting y documentacion.

Evidencia:

- settings deriva URLs desde varias plataformas.
- Hay config y scripts de Koyeb, defaults de Railway y referencias a Render.

Archivos afectados:

- [billetera/billetera/settings.py](billetera/billetera/settings.py#L145)
- [billetera/billetera/settings.py](billetera/billetera/settings.py#L282)
- [.koye.yaml](.koye.yaml#L1)
- [deploy-koyeb.sh](deploy-koyeb.sh#L1)
- [Readme.md](Readme.md#L1)

Definicion de cierre:

- Se elige una plataforma principal.
- La documentacion y scripts quedan alineados con esa decision.
- Las variables de entorno necesarias quedan definidas una sola vez.

Issue sugerido:

Elegir un target de deploy y podar configuraciones heredadas de otras plataformas.

### 7. Agregar observabilidad minima

Impacto:

Sin trazas, errores centralizados ni health checks, cualquier incidente te obliga a adivinar. Eso destruye tiempo de respuesta y confianza en produccion.

Evidencia:

- No hay observability stack, health endpoint ni integracion con error tracking.
- Solo aparece un logger aislado en signals.

Archivos afectados:

- [billetera/gastos/signals.py](billetera/gastos/signals.py#L1)

Definicion de cierre:

- Existe endpoint de health basico.
- Hay logging estructurado para errores criticos.
- Los errores de produccion se centralizan en una herramienta tipo Sentry o equivalente.

Issue sugerido:

Montar observabilidad minima antes de llamar a esto deployable.

### 8. Agregar tests en zonas sin red de seguridad suficiente

Impacto:

La suite es buena para dominio, pero sigue floja justo donde mas duele: pagos, login social y permisos de API.

Evidencia:

- Si hay tests de backup y mucho dominio financiero.
- No aparecen tests relevantes de webhook Mercado Pago, flujo Google social ni JWT custom.

Archivos afectados:

- [billetera/usuarios/views.py](billetera/usuarios/views.py#L576)
- [billetera/usuarios/social.py](billetera/usuarios/social.py#L1)
- [billetera/usuarios/jwt_views.py](billetera/usuarios/jwt_views.py#L1)

Definicion de cierre:

- Tests de happy path y failure path para cobros.
- Tests de acceso y claims para login social.
- Tests de permisos sobre endpoints API.

Issue sugerido:

Cerrar las zonas ciegas de autenticacion, cobros y API antes de seguir agregando features.

### 9. Ordenar el arranque del contenedor y el proceso de release

Impacto:

Hoy el contenedor mezcla check, retries de base, migrate, collectstatic y bootstrap de social app en el mismo arranque. Funciona, pero es fragil y poco limpio.

Evidencia:

- El entrypoint hace demasiadas cosas operativas.
- bootstrap_google_socialapp corre durante startup.

Archivos afectados:

- [entrypoint.sh](entrypoint.sh#L1)
- [Dockerfile](Dockerfile#L1)

Definicion de cierre:

- Separar build, release y runtime.
