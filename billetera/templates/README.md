This is the Django templates root used by settings.py (DIRS = [BASE_DIR/"templates"]).

Active overrides live here:
- base.html: global layout
- account/login.html: allauth account login (kept for compatibility; /accounts/login/ redirects to /usuarios/login/)
- socialaccount/login.html: provider handshake interstitial (auto-submit)

App-specific templates should remain inside each app's templates/ folder (e.g., usuarios/templates/usuarios/login.html) unless intentionally overridden here.