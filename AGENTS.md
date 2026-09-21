# Mutualité de Santé — Mode Single-Tenant

## Vue d'ensemble

Cette instance gère **une seule mutualité** avec plusieurs partenaires.
Le mode single-tenant simplifie l'isolation : une seule mutualité est active,
et tous les partenaires y sont rattachés.

## Architecture

### App `single_tenant`
- **Modèle** : `SingleTenantConfig` — stocke la mutualité unique active
- **Middleware** : `SingleTenantMiddleware` — injecte automatiquement la mutualité unique dans chaque requête
- **Vues** : Configuration et activation de la mutualité unique
- **URLs** : `/single-tenant/config/`

### Fonctionnement
1. Un `SingleTenantConfig` est créé via l'admin Django
2. La mutualité est définie comme `ACTIVE`
3. Le middleware `SingleTenantMiddleware` remplace automatiquement le tenant courant
4. Toutes les vues voient `request.current_mutualite` = la mutualité unique
5. Les `TenantManager` filtrent automatiquement par cette mutualité

### Différence avec le mode multi-tenant
- **Multi-tenant** (`MutualiteMiddleware`) : le tenant est déduit de `request.user.mutualite`
- **Single-tenant** (`SingleTenantMiddleware`) : le tenant est fixe, défini dans `SingleTenantConfig`

## Commandes utiles

```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Notes
- Le projet original `www.facturation.bi - Copy` reste intact et inchangé
- Ce projet `www.facturation.bi - single_tenant` fonctionne de la même manière que l'original
- Le mode single-tenant est activé via la configuration dans l'admin Django
