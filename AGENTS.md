# Mutualité de Santé — Guide de référence pour IA

## Vue d'ensemble

Plateforme SaaS multi-tenant de gestion de mutuelles de santé au Burundi.
Chaque **Mutualité** est un tenant isolé. Langue: français, dévise: BIF.
Framework: Django 5.1 / Python 3.12 / SQLite3 (PostgreSQL prêt en prod).

## Structure des Apps

| App | Rôle |
|-----|------|
| **core** | Socle: utilisateur, mutualité, audit, licences, notifications, middleware multi-tenant |
| **superadmin** | Panneau Super Admin: gestion de toutes les mutualités, clés, configuration globale |
| **affilies** | Gestion des membres (affiliés) avec plafonds de garantie |
| **ayants_droit** | Ayants droit (conjoint, enfants, etc.) liés à un affilié |
| **services_sante** | Catalogue des services de santé (consultation, hospit., labo, etc.) |
| **partenaires** | Établissements de santé (hôpitaux, cliniques, pharmacies), conventions |
| **origines** | Groupes d'origine (entreprises, coopératives) avec plafonds par défaut |
| **factures** | Facturation des soins, workflow brouillon→soumis→valide→payé→rejeté |
| **cotisations** | Gestion des cotisations des membres (mensuel/trimestriel/annuel) |
| **pharmacie** | Catalogue des médicaments avec taux de remboursement |
| **comptabilite** | Comptabilité SYSCOHADA: plan comptable, écritures, budgets, trésorerie, rapprochement |
| **ventilations** | Répartition analytique des charges par centre et branche |
| **groupe** | Groupes d'utilisateurs avec contrôle d'accès par menu |
| **aide** | Articles d'aide, messagerie mutualité→SuperAdmin, docs publiques |
| **portail_partenaire** | Portail en libre-service pour les partenaires (facturation, membres, médicaments) |
| **gestion_chambres** | Gestion des chambres d'hospitalisation |
| **dashboard** | Tableau de bord principal de la mutualité |
| **utilisateurs** | Gestion des utilisateurs internes |
| **corbeille** | Corbeille unifiée (soft-delete, purge auto 30 jours) |

## Modèle d'authentification (3 systèmes)

### 1. Utilisateurs mutualité (`core.Utilisateur`)
- `AUTH_USER_MODEL = 'core.Utilisateur'` (extends `AbstractUser`)
- Champs: `mutualite`, `role`, `telephone`, `nom`, `postnom`, `prenom`, `photo`, `actif`
- Rôles: `SUPER_ADMIN`, `ADMIN_MUTUALITE`, `COMPTABLE`, `AGENT`, `CONSULTATION`
- Login: `/connexion/`, session Django standard
- `request.user.est_super_admin` → redirigé vers `/superadmin/`

### 2. Portail partenaire (`partenaires.UtilisateurPartenaire`)
- Modèle séparé (pas lié à `AbstractUser`), mot de passe hashé via `make_password`/`check_password`
- Session stockée: `request.session['partenaire_user_id']`
- Login: `/portail/connexion/`
- Auth backend: `partenaires/auth_backends.py:PartenaireAuthBackend`

### 3. SuperAdmin
- Deux accès: rôle `SUPER_ADMIN` sur `Utilisateur` OU `is_superuser`/`is_staff`
- Panel: `/superadmin/` (vues custom) + `/admin/` (Django admin)
- Le SuperAdmin n'appartient à AUCUNE mutualité (`mutualite = None`)

## Isolation multi-tenant

- `core.models.TenantManager` = `Manager` filtrant par `mutualite` courante
- `core.middleware.MutualiteMiddleware` → `request.current_mutualite`
- Tous les modèles métier ont un FK `mutualite` et utilisent `TenantManager()`
- Modèles **non filtrés** (globaux): `ConfigurationApp`, `MessageSuperAdmin`, `DocumentSuperAdmin`

## Middleware (ordre d'exécution)

1. **MutualiteMiddleware** → définit `request.current_mutualite` + thread-local
2. **LicenseMiddleware** → vérifie licence, redirige si expirée (sauf `/connexion/`, `/licence/`, `/admin/`, SuperAdmin)
3. **RateLimitMiddleware** → anti brute-force: max 10 POST/5min par IP sur login
4. **AuditLogMiddleware** → log les 404 en base

## Permissions

- Par **rôle**: propriétés `est_admin`, `peut_modifier`, `peut_valider`, `peut_exporter`, etc. sur `Utilisateur`
- Par **groupe**: `Groupe` → M2M `Menu` → `Utilisateur.menus_autorises` (liste d'URL names)
- Template tags: `{% menu_autorise 'url_name' %}`, `{% section_autorise 'url1' 'url2' %}`
- Mixins vues: `RoleRequiredMixin`, `AdminRequiredMixin`, `MutualiteRequiredMixin`, `SuperAdminRequiredMixin`

## Templates

| Template | Usage |
|----------|-------|
| `base.html` | Layout principal connecté (AdminLTE), blocs: `title`, `sidebar_nav`, `content`, `extra_js` |
| `base_auth.html` | Pages de connexion/inscription, fond via `APP_BACKGROUND_IMAGE_URL` |
| `superadmin/base_superadmin.html` | Sidebar SuperAdmin, extends `base.html` |

**Context processors** (variables globales dans tous les templates):
- `app_config` → `APP_NOM`, `APP_PRIMARY_COLOR`, `APP_BACKGROUND_IMAGE_URL`, etc.
- `mutualite_context` → `MUTUALITE_PRIMARY_COLOR`, `MUTUALITE_BACKGROUND_IMAGE_URL`, `licence_15j`
- `superadmin_notifications` → `superadmin_nb_messages_nouveaux`

## Modèles clés

### `core.Mutualite`
Champs de thème: `primary_color`, `accent_color`, `background_color`, `background_image`, `background_opacity`, `background_brightness`, `text_color`
Champs licence: `cle_activation`, `date_expiration`, `type_abonnement`, `statut` (ACTIF/ESSAI/SUSPENDU/EXPIRE)
15 champs `def_*` = plafonds par défaut pour les nouveaux affiliés.

### `core.ConfigurationApp` (UNIQUE, singleton)
Même champs de thème que Mutualite mais au niveau application.

### `core.Notification`
Alertes plafond: `type_notification` (APPROCHE/ATTEINT/DEBLOCAGE/etc.), `affilie`, `consommation`, `pourcentage`, `vue`

### `aide.DocumentSuperAdmin`
Doc public vidéo: champ `video_url`, slug, contenu, fichier.

## URLs principales

| URL | App |
|-----|-----|
| `/` | Landing, redirige selon auth |
| `/connexion/` | core |
| `/dashboard/` | dashboard |
| `/superadmin/` | superadmin |
| `/portail/` | portail_partenaire |
| `/affilies/` | affilies |
| `/factures/` | factures |
| `/cotisations/` | cotisations |
| `/comptabilite/` | comptabilite |
| `/pharmacie/` | pharmacie |
| `/aide/` | aide |
| `/chambres/` | gestion_chambres |

Voir `mutualite/urls.py` pour la liste complète des inclusions.

## Workflows métier

### Facture médicale
`brouillon → soumis → valide → payé`

Calcul: `montant_total` = somme des lignes, `montant_ticket_moderateur` = part patient, `montant_mutualite` = prise en charge.

### Cotisation
Paiement mensuel/trimestriel/annuel par affilié. Workflow: création → validation. Modes: CASH, MOBILE, BANQUE, COOPERATIVE, CHEQUE.

### Réinitialisation mutualité (SuperAdmin)
1. Page `/superadmin/reinitialiser-selection/` → dropdown + boutons Export Excel / Réinitialiser
2. Export Excel: 16 onglets (Mutualité, Utilisateurs, Groupes, Affiliés, Ayants droit, Cotisations, Factures, Lignes facture, Services santé, Partenaires, Conventions, Utilisateurs partenaires, Origines, Médicaments, Notifications, Journal audit)
3. Réinitialisation: modale de confirmation + saisie du nom + suppression atomique de toutes les données opérationnelles

### Portail partenaire
Les partenaires (hôpitaux) peuvent: soumettre des factures, vérifier les membres, gérer les médicaments, consulter l'historique. Session séparée du Django auth.

## Architecture technique

- **Base de données**: SQLite3 (`db.sqlite3`) ou PostgreSQL via `settings.DATABASE_URL`
- **Fichiers média**: `media/`, servis par `static()` en dev
- **CSS/JS**: Bootstrap 5, AdminLTE 4, Bootstrap Icons, Google Fonts (Inter, Outfit)
- **Templating**: Django templates avec héritage multi-niveaux
- **API DRF**: `/api/superadmin/` (MutualiteViewSet, DashboardAPIView) — limité pour l'instant

## Commandes utiles

```bash
python manage.py runserver          # Lancer le serveur
python manage.py check              # Vérifier le projet
python manage.py makemigrations     # Créer migrations
python manage.py migrate            # Appliquer migrations
python manage.py shell              # Console Django
```

## Notes pour une IA

- Toujours tuer les processus Python avant de redémarrer le serveur pour éviter le cache d'URLs
- Le fichier `images.jpg` dans `/media/` peut manquer → 404 non-bloquant
- `ConfigrationApp` = 1 seul `u` (pas `ConfigurationApp`), ne pas corriger l'orthographe
- La `Mutualite` n'a PAS de champs `matricule` pour `Affilie` → utiliser `numero_affiliation`
- Le SuperAdmin n'a pas de `mutualite` → ne pas utiliser `RequireMutualiteMixin` pour ses vues
- Les context processors `notifications_portail` ne fournissent les variables de thème QUE si l'utilisateur est connecté au portail
