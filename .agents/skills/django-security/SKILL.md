---
name: django-security
description: Checklist securite Django obligatoire (5 niveaux) + regles prod cPanel sans coupure.
version: 1.0.0
author: Alain Kay
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [django, security, audit, owasp, cpanel, production]
    category: engineering
    related_skills: []
---

# Django Security Skill — Remarque permanente

Appliquer cette checklist a CHAQUE projet Django futur, avant toute mise en prod.
Source : `methodedesecurite.txt` + retours d'audit (IDOR mutualite/societe, Open Redirect, uploads, secrets, cPanel live).

## NIVEAU 1 — Statique (lire le code)

1. **Anti-Injection SQL** : aucun `.raw(f"`, `.extra(`, `cursor.execute(f"`. Tout en `filter()/get()/%s`. Outil : `bandit -r . -k B608`.
2. **Anti-XSS** : aucun `|safe`, `mark_safe()`, `autoescape off` sur donnee user ; aucun `HttpResponse(f"{request...")`. Tester `<script>alert(1)</script>` et `<img src=x onerror=alert(1)>` dans chaque champ. Charts JSON → `json_script`, pas `|safe`.
3. **Anti-CSRF** : `CsrfViewMiddleware` present ; `{% csrf_token %}` partout ; aucun `@csrf_exempt` sur vue sensible (si `sendBeacon`, justifier + garder `@login_required` + controle tenant).
4. **Anti-Command Injection** : aucun `os.system(request...)`, `subprocess...(request...)`, `eval/exec(request...)`. Outil : `bandit -r . -k B602`.
5. **Secrets** : `SECRET_KEY`, `DB PASSWORD`, cles API JAMAIS en dur — `.env` / variables Passenger uniquement, sans fallback `django-insecure-*`. Jamais `db.sqlite3`, `*.sql`, `venv/`, `.git/` dans le repo ni en prod web-root.

Script auto : `python scripts/test_security.py` (niveaux 1+2, lecture seule).

## NIVEAU 2 — Config (`python manage.py check --deploy` → 0 warning)

- `DEBUG=False`, `ALLOWED_HOSTS` prod, `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_HSTS_SECONDS>0`, `X_FRAME_OPTIONS='DENY'`, `SECRET_KEY` > 50 chars aleatoire.
- `SESSION_COOKIE_HTTPONLY=True`, `SAMESITE=Lax`, password `min_length>=8`, pas de `BrowsableAPIRenderer`/`BasicAuthentication` en prod, CSP + `Referrer-Policy` + `Permissions-Policy`.

## NIVEAU 3 — Auth & autorisation (le plus critique : IDOR)

- `/admin/`, `/dashboard/` sans login → redirect login. 20 mauvais passwords → blocage (rate-limit), echecs logges.
- **Chaque vue objet** : `get_object_or_404(Modele, pk=..., mutualite=request.user.mutualite)` (ou `societe=...`). Pattern superadmin sans tenant : garder comportement explicite, jamais queryset non filtre. `TenantManager.get_queryset()` : si pas de tenant → `qs.none()`, jamais tout retourner.
- Session : logout → bouton Retour ne montre plus rien ; cookie `sessionid` modifie → pas d'usurpation.

## NIVEAU 4 — Dynamique (OWASP Top 10)

- SQLi `' OR '1'='1`, XSS, upload `shell.php` → `FileExtensionValidator` + check `content_type` + limite taille + `media/` sans execution, traversal `/media/../../settings.py`, Open Redirect `?next=http://google.com` → `url_has_allowed_host_and_scheme`. Scanner ZAP en local avant prod.

## NIVEAU 5 — Dependances & infra

- `pip-audit` → upgrade libs. `securityheaders.com` → A. Rate-limit 100 req/s → `django-ratelimit`/Redis, pas `LocMem` seul.

## REGLES PROD cPanel (app en cours d'utilisation)

1. Ne jamais changer de branche live (`ancienne-version` vs `main` = evolutive, pas secu) sans backup DB+fichiers + fenetre creuse + `migrate --plan` + rollback.
2. Correctifs SAFE copiables directs : `.htaccess` (blocage `.git/HEAD/config/hooks/objects/refs/.env/sqlite/logs/venv/`), `deploy.php` (POST-only + secret requis). Pas de restart Django requis.
3. `SECRET_KEY`/`DB PASSWORD` : d'abord variables Passenger, puis settings sans fallback, puis `touch tmp/restart.txt` (deconnecte tous — normal). Repo git : Prive, jamais de `*.sql`/`sqlite`.
4. Toujours : backup `.old`, 1 fichier a la fois, `manage.py check` → 0 erreur, test accueil+login+URL bloquee, rollback immediat si anomalie.

## Plan 30 minutes

`pip install bandit pip-audit` → `bandit -r .` (corriger HIGH) → `pip-audit` (upgrade) → `check --deploy` (0 warning) → ZAP localhost → test IDOR 2 comptes → `test_security.py` vert.
