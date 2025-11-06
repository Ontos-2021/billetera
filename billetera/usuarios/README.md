Autenticación Google OIDC + PKCE (cliente SPA)

1) Flujo (resumen):
  - El frontend inicia el flujo de autorización OIDC con Google usando PKCE (code flow).
  - Google devuelve un authorization code al redirect_uri del cliente.
  - El cliente envía al backend (esta app) el JSON:
      { "code": "<AUTH_CODE>", "code_verifier": "<PKCE_VERIFIER>", "redirect_uri": "<REDIRECT_URI>" }
  - Backend en `/auth/social/google/` usa `dj-rest-auth` + `django-allauth` para intercambiar
    el código por tokens, valida `id_token`/`extra_data` y crea/obtiene el usuario.
  - Backend devuelve los JWTs (access/refresh) generados por SimpleJWT.

2) Ejemplo de cliente (usar Google Identity Services - Authorization Code + PKCE):

  // Pseudocódigo JS (usar la librería oficial o AppAuth)
  // 1) Generar code_verifier y code_challenge (SHA256)
  // 2) Abrir el consentimiento de Google con response_type=code y code_challenge
  // 3) Recibir code en redirect_uri
  // 4) POST al backend:

  fetch('/auth/social/google/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: authCode, code_verifier: codeVerifier, redirect_uri: redirectUri })
  }).then(r => r.json()).then(data => {
    // data tendrá access/refresh tokens (y user info)
  })

3) Entorno requerido (ejemplo .env):
  GOOGLE_OAUTH_CLIENT_ID=...
  GOOGLE_OAUTH_CLIENT_SECRET=...
  GOOGLE_REDIRECT_URI=https://tu-dominio.com/auth/google/callback/
  GOOGLE_HOSTED_DOMAIN=example.com  # opcional, si quieres limitar por dominio

4) Comando para crear SocialApp (después de setear envs):
  python manage.py bootstrap_google_socialapp
 
5) Examples (curl)

Obtener tokens desde el backend después de que el frontend reciba el `code`:

```bash
curl -X POST http://localhost:8000/auth/social/google/ \
  -H "Content-Type: application/json" \
  -d '{"code":"<AUTH_CODE>","code_verifier":"<CODE_VERIFIER>","redirect_uri":"<REDIRECT_URI>"}'
```

Respuesta esperada (ejemplo):

```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {"id": 1, "email": "user@example.com"}
}
```

Notas de seguridad:
- El backend valida `email_verified` y, si configuras `GOOGLE_HOSTED_DOMAIN`, el claim `hd`.
- Recomendación: para producción usar HTTPS y validar correctamente `redirect_uri` tanto en el cliente como en la consola de Google.


