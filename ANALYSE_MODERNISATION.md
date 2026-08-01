# ANALYSE & MODERNISATION — Application de Gestion des Mutualités de Santé

> Date : Juillet 2026
> Projet : facturation.bi (Django 5.1 + AdminLTE 4)

---

## TABLE DES MATIÈRES

1. [État des lieux](#1-État-des-lieux)
2. [Architecture & Performance](#2-architecture--performance)
3. [Interface Utilisateur (UX/UI)](#3-interface-utilisateur-uxui)
4. [Expérience Métier (Fonctionnel)](#4-expérience-métier-fonctionnel)
5. [Technologies à Ajouter](#5-technologies-à-ajouter)
6. [Qualité & Sécurité](#6-qualité--sécurité)
7. [Fonctionnalités Bonus](#7-fonctionnalités-bonus)
8. [Priorisation](#8-priorisation)

---

## 1. ÉTAT DES LIEUX

### 1.1 Stack technique actuelle

| Composant | Technologie |
|-----------|-------------|
| Backend | Django 5.1.4 |
| API | Django REST Framework (limité au superadmin uniquement) |
| Frontend | Django Templates + AdminLTE 4 (Bootstrap 5.3) |
| Base de données | SQLite3 (développement), PostgreSQL configuré en commentaire |
| Cache | LocMemCache (non scalable) |
| Tâches asynchrones | AUCUNE |
| Assets | npm (AdminLTE, Bootstrap Icons) |
| Auth | Sessions Django, rate limiting maison |
| Stockage fichiers | Local filesystem (`media/`) |

### 1.2 Ce qui existe déjà (mais inexploité côté hôpital)

| Fonctionnalité | État |
|----------------|------|
| `Partenaire` (hôpital/clinique) | Modèle complet avec localisation, contact, convention, statut |
| `UtilisateurPartenaire` | Modèle défini mais **aucune vue, aucun dashboard, aucune session** |
| `Facture` liée Partenaire + Affilie | Workflow complet (BROUILLON → SOUMIS → VALIDE → PAYE) |
| `Convention` | Contrat entre mutualité et partenaire |
| `Affilie` | Infos complètes : plafonds, garanties, groupe sanguin, contact urgence |
| API REST | Existe uniquement pour superadmin (`/api/superadmin/`) |
| Portail hôpital | **AUCUN** — les factures sont saisies côté mutualité uniquement |
| Transfert de fichiers | Upload basique sur chaque facture, pas de GED structurée |

### 1.3 Faiblesses identifiées

- ❌ **Aucun portail pour les hôpitaux** — ils ne peuvent pas consulter les membres ni soumettre de factures
- ❌ **API REST inexistante pour le métier** — impossible d'intégrer avec les SIH existants
- ❌ **SQLite en production** — ne passera pas à l'échelle
- ❌ **Pas de cache performant** — LocMemCache ne tient pas en multi-processus
- ❌ **Pas de tâches asynchrones** — exports PDF, emails, notifications bloquants
- ❌ **Stockage local des fichiers** — risque de perte, pas de backup automatique
- ❌ **Tests automatisés absents** — `test/` vide, `tests.py` squelettes vides
- ❌ **Recherche limitée** — pas de recherche globale instantanée
- ❌ **Pas de notifications temps réel**

---

## 2. ARCHITECTURE & PERFORMANCE

### 2.1 DRF API complète (`/api/v1/`)

Créer une API REST complète pour toutes les entités métier :

```
/api/v1/
├── /mutualites/          → informations de la mutualité
├── /affilies/            → CRUD membres
│   ├── /{id}/ayants-droit/ → ayants droit du membre
│   ├── /{id}/factures/     → historique des soins
│   ├── /{id}/cotisations/  → historique des cotisations
│   └── /{id}/plafonds/     → garanties disponibles en temps réel
├── /partenaires/         → CRUD partenaires (hôpitaux)
│   ├── /{id}/conventions/  → conventions associées
│   └── /{id}/factures/     → factures du partenaire
├── /factures/            → CRUD + workflow (soumettre, valider, rejeter, payer)
├── /cotisations/         → CRUD cotisations
├── /services-sante/      → catalogue des prestations
├── /pharmacie/           → médicaments pris en charge
├── /documents/           → upload/download documents médicaux
└── /utilisateurs/        → gestion utilisateurs
```

**Avantages :**
- Alimente un frontend SPA moderne (React/Vue.js)
- Permet l'intégration avec les Systèmes d'Information Hospitaliers (SIH)
- Facilite les échanges machine-à-machine (transfert automatisé de dossiers)
- Mobile-ready (applications natives peuvent consommer l'API)

### 2.2 Migration PostgreSQL

**Pourquoi :**
- SQLite ne supporte pas la concurrence (un seul writer à la fois)
- PostgreSQL supporte les transactions avancées, les indexes partiels, full-text search
- Prêt pour la scalabilité horizontale

**Action :** Décommenter la configuration PostgreSQL dans `settings.py` et ajouter `psycopg2` dans `requirements.txt`.

### 2.3 Cache Redis

**Pourquoi :**
- `LocMemCache` est réinitialisé à chaque redémarrage du serveur
- En multi-processus (Gunicorn/uWSGI), chaque processus a son propre cache → incohérent
- Redis sert aussi pour : sessions, WebSockets, file d'attente Celery

**Action :**
```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
```

### 2.4 Tâches asynchrones (Celery / Huey)

**Cas d'usage :**
- Génération de rapports PDF (reportlab)
- Envoi d'emails (notifications, relances)
- Export Excel volumineux (openpyxl)
- Sauvegarde automatique de la base de données
- Nettoyage des fichiers temporaires

### 2.5 Stockage Cloud (S3 / MinIO)

**Pourquoi :**
- Les fichiers (photos, scans factures, conventions, documents) sont stockés en local (`media/`)
- Risque de perte si le serveur tombe
- Pas de backup automatique
- Pas scalable (espace disque limité)

**Actions :**
- Migrer vers `django-storages` avec S3 compatible (AWS S3, DigitalOcean Spaces, MinIO auto-hébergé)
- Les anciens fichiers doivent être migrés vers le nouveau stockage
- Backup automatique configuré

---

## 3. INTERFACE UTILISATEUR (UX/UI)

### 3.1 Mode sombre (Dark Mode)

AdminLTE 4 supporte nativement le dark mode via `data-bs-theme="dark"`.

**Actions :**
- Ajouter un toggle dans la navbar (icône soleil/lune)
- Persister le choix dans le localStorage et/ou dans le profil utilisateur
- Adapter les couleurs personnalisées (variables CSS) pour le thème sombre
- Actuellement le `base.html` a `data-bs-theme="light"` en dur → le rendre dynamique

**Exemple de toggle :**
```html
<button class="nav-link" onclick="document.documentElement.dataset.bsTheme =
    document.documentElement.dataset.bsTheme === 'dark' ? 'light' : 'dark'">
    <i class="bi bi-moon-stars"></i>
</button>
```

### 3.2 Recherche globale instantanée (HTMX + Alpine.js)

**Fonctionnalité :**
- Barre de recherche unique dans le header de la navbar
- Tapez le nom, numéro d'affiliation, téléphone d'un membre
- Résultats en dropdown avec : photo miniature, nom, n° affiliation, statut, lien direct

**Technologie recommandée : HTMX** (léger, pas de build JS, fonctionne avec Django templates)

**Comportement :**
```html
<input type="search" name="q" hx-get="/api/v1/recherche-globale/"
       hx-trigger="keyup changed delay:300ms" hx-target="#search-results"
       placeholder="Rechercher un membre, facture, partenaire...">
<div id="search-results"></div>
```

### 3.3 Tableaux améliorés

**Améliorations :**
- Colonnes configurables (afficher/masquer des colonnes)
- Filtres inline (par date, statut, type)
- Tri multi-colonnes
- Export CSV/Excel direct depuis le tableau
- Pagination infinie ou "Show more" (HTMX)

### 3.4 Notifications en temps réel (WebSocket)

**Django Channels + Redis :**

Cas d'utilisation :
- "Nouvelle facture soumise par hôpital XXX"
- "Facture n°XXX validée ✅"
- "Facture n°XXX rejetée ❌ — motif : ..."
- "Cotisation en retard pour membre XXX"
- "Licence expirera dans 5 jours"

**Architecture :**
```
Hôpital soumet facture → Event "facture.soumise" → Redis Pub/Sub
    → Notification push vers la mutualité (WebSocket)
    → Toast dans l'interface
```

### 3.5 Dashboard avec graphiques interactifs

Chart.js est déjà disponible via AdminLTE. Ajouter :

| Graphique | Type | Données |
|-----------|------|---------|
| Évolution des cotisations | Courbe | Par mois sur l'année |
| Répartition factures par partenaire | Camembert | Top 10 hôpitaux |
| Taux de validation/rejet | Barres | Ratio mensuel |
| Membres actifs vs suspendus | Jauge | En temps réel |
| Top 10 diagnostics | Barres horizontales | Fréquence |
| Évolution du chiffre (mutualité) | Aire | Cumul mensuel |

### 3.6 Animations et micro-interactions

- Transitions entre pages → TurboLinks ou Hotwire (Turbo Drive)
- Skeleton loaders pendant le chargement des données
- Ripple effect sur les boutons
- Validation inline des formulaires (Alpine.js)
- Progress bar lors des soumissions de formulaire

### 3.7 Responsive mobile

- Vérifier tous les formulaires longs (affilié, facture) sur écran < 768px
- Sidebar repliable avec mémorisation du statut (localStorage)
- Tableaux horizontaux scrollables sur mobile (déjà partiellement fait)
- Boutons d'action accessibles au pouce (taille minimum 44x44px)

---

## 4. EXPÉRIENCE MÉTIER (FONCTIONNEL)

### 4.1 PORTAL PARTENAIRE (HÔPITAL) — NOUVELLE APP `portail_partenaire/`

C'est la priorité absolue. Actuellement, le modèle `UtilisateurPartenaire` existe mais est totalement inutilisé.

#### 4.1.1 Authentification

- Login dédié pour `UtilisateurPartenaire` (actuellement stocké avec mot de passe en clair dans le modèle → **à corriger** utiliser `hashers`)
- Session séparée de celle des utilisateurs mutualité
- Décorateur `@partenaire_login_required`
- Rate limiting, audit de connexion

#### 4.1.2 Dashboard Hôpital

```
╔═══════════════════════════════════════════════════════════╗
║  BIENVENUE, HÔPITAL PRINCE LOUIS RWAGASORE               ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ║
║  │ Factures  │  │ Membres  │  │ Dossiers │  │ Convent. │  ║
║  │ en att. 5 │  │ traités  │  │ en cours │  │ Active   │  ║
║  └──────────┘  └──────────┘  └──────────┘  └──────────┘  ║
║                                                           ║
║  ┌────────────────────────────────────────────────────┐   ║
║  │ Dernières factures soumises                       │   ║
║  │ N° FAC-202607-0012 — MUTEMBERE Annonciate  ⏳ En attente│
║  │ N° FAC-202607-0011 — NKURUNZIZA Eric        ✅ Validée│
║  └────────────────────────────────────────────────────┘   ║
╚═══════════════════════════════════════════════════════════╝
```

**Widgets :**
- Factures en attente de validation (avec délai)
- Membres consultés aujourd'hui
- Alertes : convention expirant bientôt
- Chiffres du mois : total facturé, montant part mutualité, ticket modérateur

#### 4.1.3 Recherche et fiche membre

**Barre de recherche :**
- Par numéro d'affiliation (scan ou saisie)
- Par nom, téléphone
- Résultat instantané : photo, nom complet, n° affiliation, statut cotisation

**Fiche membre complète (consultation seule) :**

```
┌─────────────────────────────────────────────────────────┐
│  👤 NKURUNZIZA Eric (AFF-2026-0042)    🟢 Cotisation OK │
├─────────────────────────────────────────────────────────┤
│  📋 Informations personnelles                           │
│  ├── Sexe : M | Âge : 34 ans | Groupe : O+             │
│  ├── Tél : +257 79 123 456 | Email : eric@email.com    │
│  ├── Contact urgence : Jeanne (79 987 654)             │
│  └── Hôpital référence : CHU Kamenge                    │
│                                                         │
│  👨‍👩‍👧‍👦 Ayants droit (3)                              │
│  ├── NKURUNZIZA Marie (Conjoint)    🟢 Actif           │
│  ├── NKURUNZIZA Jean (Enfant)       🟢 Actif           │
│  └── NKURUNZIZA Alice (Enfant)      ⚠️ Suspension      │
│                                                         │
│  💰 Garanties / Plafonds                                │
│  ├── Soins ambulatoires : 500 000 BIF ████████░░ 80%   │
│  ├── Hospitalisation : 2 000 000 BIF  ████░░░░░░ 40%   │
│  ├── Pharmacie : 300 000 BIF          ██████░░░░ 60%   │
│  └── Maternité : 500 000 BIF          ░░░░░░░░░░  0%   │
│                                                         │
│  📜 Historique des soins (5 dernières)                  │
│  ├── 15/06/2026 — Consultation générale — 45 000 BIF   │
│  ├── 02/05/2026 — Analyse sang — 25 000 BIF            │
│  └── 18/04/2026 — Hospitalisation 3j — 850 000 BIF     │
└─────────────────────────────────────────────────────────┘
```

#### 4.1.4 Saisie de facture par l'hôpital

**Formulaire :**
1. Rechercher et sélectionner le membre (ou ayant droit)
2. Voir les plafonds disponibles en temps réel
3. Ajouter des lignes de prestation (service, quantité, prix unitaire)
4. Le système calcule automatiquement :
   - Part mutualité (selon taux de prise en charge)
   - Ticket modérateur (part patient)
5. Upload de documents médicaux (ordonnance, résultats d'analyse, imagerie)
6. Diagnostic / raison de la consultation
7. Soumettre → statut "SOUMIS"

**Vérifications automatiques :**
- Cotisation du membre à jour
- Plafond non dépassé
- Convention active
- Ayant droit valide (si concerné)

#### 4.1.5 Workflow complet

```
HÔPITAL                          MUTUALITÉ
───────                          ─────────

Saisie facture
  │
  ├── Brouillon (brouillon)
  │       │
  │       └── Enregistrer
  │
  ├── Soumettre ──────────────> Notification reçue
  │       │                         │
  │       │                    Visualisation + documents
  │       │                         │
  │       │              ┌──────────┴──────────┐
  │       │              │                     │
  │       │           Valider               Rejeter
  │       │              │                     │
  │       │              ▼                     ▼
  │       │         Notification           Notification
  │       │         "Validée ✅"           "Rejetée ❌ + motif"
  │       │              │                     │
  │       │         Paiement              Modifier +
  │       │              │                resoumettre
  │       │              ▼                     │
  │       │           PAYÉ                    │
  │       │              │                     │
  │       │              └─────────────────────┘
  │       ▼
  │   Suivi en temps réel du statut
  │
  └── Historique complet
```

### 4.2 Messagerie intégrée mutualité ↔ hôpital

**Modèle :**
```python
class Message(models.Model):
    mutualite = ForeignKey(Mutualite)
    partenaire = ForeignKey(Partenaire)
    expediteur_type = CharField(choices=('MUTUALITE', 'HOPITAL'))
    expediteur_nom = CharField()  # nom de la personne
    facture = ForeignKey(Facture, null=True, blank=True)
    contenu = TextField()
    fichier_joint = FileField(null=True, blank=True)
    lu = BooleanField(default=False)
    date_creation = DateTimeField(auto_now_add=True)
```

**Interface :**
- Fil de discussion par facture (comme une conversation)
- Badge de messages non lus dans le header
- Notifications en temps réel (WebSocket)

### 4.3 Workflow d'hospitalisation complet

| Étape | Description |
|-------|-------------|
| **Admission** | Enregistrement entrée, lit/chambre, service |
| **Prescriptions** | Examens, médicaments, soins prescrits |
| **Suivi** | Notes médicales quotidiennes |
| **Soins prodigués** | Actes réalisés avec quantification |
| **Sortie** | Résumé clinique, ordonnance de sortie |
| **Facturation** | Génération automatique de la facture d'hospitalisation |

### 4.4 Gestion des plafonds en temps réel

- Chaque ligne de facture vérifie le plafond restant disponible pour le membre
- Calcul : plafond_initial - total_des_factures_validees_sur_la_periode
- Alerte visuelle si le seuil approche (80%, 90%, 100%)
- Impossible de soumettre si le plafond est dépassé (sauf dérogation)

### 4.5 QR Code pour les cartes membres

- Génération d'un QR code unique par membre (contenant n° affiliation + clé de vérification)
- Intégré dans la carte membre PDF exportable
- L'hôpital scanne → fiche membre complète affichée instantanément
- Utiliser `qrcode` (Python) ou une API de génération

### 4.6 Signature électronique

- Validation des factures avec signature numérique
- Conventions signées électroniquement (upload + certificat)
- Piste d'audit horodatée

---

## 5. TECHNOLOGIES À AJOUTER

| Technologie | Version | Usage | Priorité |
|-------------|---------|-------|----------|
| **HTMX** | 2.x | Rendre les pages dynamiques sans JS. Recherche, filtres, pagination ajax, modals | P1 |
| **Alpine.js** | 3.x | Interactivité légère dans les templates (calculs en direct, toggles, validations) | P1 |
| **Django Channels** | 4.x | WebSockets pour notifications temps réel, messagerie | P1 |
| **Redis** | 7.x | Cache, sessions, file d'attente, WebSocket layer | P1 |
| **Celery** | 5.x | Tâches asynchrones (PDF, emails, exports lourds) | P1 |
| **django-filter** | 25.x | Filtres avancés dans les listes et l'API (déjà configuré DRF) | P1 |
| **django-import-export** | 4.x | Import/Export Excel des données (affiliés, cotisations) | P2 |
| **django-debug-toolbar** | 5.x | Debug des performances SQL/templates (développement) | P1 |
| **Sentry** | SDK | Monitoring des erreurs en production | P2 |
| **Whitenoise** | 6.x | Servir les fichiers statiques en production (déjà compatible) | P2 |
| **django-cors-headers** | 4.x | Si API consommée par frontend externe (SPA, mobile) | P2 |
| **django-storages** | 1.x | Stockage cloud S3/MinIO pour les fichiers uploadés | P1 |
| **django-oauth-toolkit** | 3.x | OAuth2 pour l'API (sécurisation des accès partenaires) | P2 |
| **ruff** | - | Linter Python ultra-rapide (remplace flake8 + isort + black) | P1 |
| **pre-commit** | - | Hooks git pour linting, formatage automatique | P2 |
| **pytest** | 8.x | Tests unitaires + coverage | P1 |

### Installation recommandée (requirements.txt complet)

```
Django==5.1.4
djangorestframework>=3.15
django-filter>=25.1
django-cors-headers>=4.6
django-storages>=1.14
django-channels>=4.2
django-import-export>=5.1
channels-redis>=4.2
redis>=5.2
celery>=5.4
Pillow>=10.0.0
openpyxl>=3.1.0
reportlab>=4.0.0
psycopg2-binary>=2.9.0
requests>=2.32.0
sentry-sdk>=2.20
whitenoise>=6.9
gunicorn>=23.0
```

---

## 6. QUALITÉ & SÉCURITÉ

### 6.1 Tests automatisés

**État actuel :**
- `test/` → dossier vide
- `affilies/tests.py` → vide/squelette
- `factures/tests.py` → vide/squelette
- Aucun test dans les autres apps

**Plan d'action :**
```
tests/
├── conftest.py              # Fixtures globales (mutualite, user, partenaire, affilie)
├── test_affilies.py         # CRUD membres, recherche, export
├── test_ayants_droit.py     # CRUD ayants droit
├── test_factures.py         # Workflow complet facture (brouillon → soumis → valide → paye)
├── test_partenaires.py      # CRUD partenaires, conventions
├── test_cotisations.py      # CRUD cotisations, calculs
├── test_api.py              # Endpoints API REST
└── test_auth.py             # Authentification, permissions, audit
```

**Framework :** pytest + pytest-django + coverage (> 80%)

### 6.2 CI/CD (GitHub Actions)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: POSTGRES_DB: test_db
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: pytest --cov --cov-report=term-missing
      - run: python manage.py check --deploy
```

### 6.3 Audit trail avancé

`JournalAudit` existe déjà. Améliorations :
- Interface de relecture des modifications (qui a changé quoi, avant/après)
- Export PDF du journal d'audit
- Filtres avancés : par utilisateur, module, date, action
- Rétention configurable (90 jours, 1 an, etc.)

### 6.4 2FA (Authentification à deux facteurs)

- Optionnel pour les rôles sensibles (ADMIN_MUTUALITE, SUPER_ADMIN)
- Via Google Authenticator, SMS, ou email
- Utiliser `django-otp` ou solution maison

### 6.5 Sécurité renforcée

- Rate limiting sur toutes les endpoints API
- Validation des fichiers uploadés (taille, type, scan antivirus)
- Headers de sécurité (déjà partiellement configurés dans settings.py)
- Audit des accès API (`JournalAudit`)
- Rotation des clés API

---

## 7. FONCTIONNALITÉS BONUS

### 7.1 Envoi SMS/Email automatique

| Type | Déclencheur | Canal |
|------|-------------|-------|
| Relance cotisation impayée | J+1, J+7, J+30 après échéance | SMS + Email |
| Confirmation adhésion | Après création membre | Email |
| Notification validation facture | Changement statut facture | Email (hôpital) |
| Notification rejet facture | Rejet avec motif | Email (hôpital) |
| Alerte licence expirant | J-30, J-15, J-7, J-3 | Email (admin mutualité) |
| Carte membre numérique | À la demande | Email (PDF) |

### 7.2 Module de réclamation

- Membre dépose une réclamation sur un remboursement refusé
- Suivi par la mutualité avec escalade
- Historique complet des interactions
- Délai de traitement garanti (SLA)

### 7.3 GED (Gestion Électronique de Documents)

Un modèle centralisé pour tous les documents :

```python
class Document(models.Model):
    CATEGORIES = [
        ('CONVENTION', 'Convention'),
        ('ORDONNANCE', 'Ordonnance'),
        ('RESULTAT_ANALYSE', "Résultat d'analyse"),
        ('COMPTE_RENDU', 'Compte rendu médical'),
        ('IMAGERIE', "Imagerie médicale"),
        ('FACTURE_SCAN', 'Scan de facture'),
        ('CARTE_MEMBRE', 'Carte membre'),
        ('RECU_COTISATION', "Reçu de cotisation"),
        ('PIECE_COMPTABLE', 'Pièce comptable'),
        ('AUTRE', 'Autre'),
    ]
    mutualite = ForeignKey(Mutualite)
    partenaire = ForeignKey(Partenaire, null=True)
    affilie = ForeignKey(Affilie, null=True)
    facture = ForeignKey(Facture, null=True)
    categorie = CharField(choices=CATEGORIES)
    fichier = FileField(upload_to='documents/')
    description = TextField(blank=True)
    cree_par_partenaire = ForeignKey(UtilisateurPartenaire, null=True)
    cree_par = ForeignKey(Utilisateur, null=True)
    date_creation = DateTimeField(auto_now_add=True)
    version = IntegerField(default=1)  # versioning
    tags = CharField(max_length=500, blank=True)  # recherche plein texte
```

**Fonctionnalités :**
- Recherche plein texte (PostgreSQL full-text search)
- Prévisualisation directe dans le navigateur (PDF, images)
- Versioning des documents
- Partage sécurisé entre mutualité et hôpital

### 7.4 Export PDF professionnel

Avec reportlab (déjà installé) :

| Document | Contenu |
|----------|---------|
| Fiche membre | Photo, informations, garanties, QR code |
| Attestation d'affiliation | Pour l'hôpital, preuve de couverture |
| Facture | En-tête mutualité, lignes, totaux, statut |
| Reçu de cotisation | Montant, période, mode de paiement |
| Convention | Contrat complet entre mutualité et partenaire |
| Rapport d'audit | Journal des actions filtré |

### 7.5 PWA (Progressive Web App)

Permet d'installer l'application sur le mobile comme une app native :
- Service Worker pour le cache offline
- Manifest.json avec icônes
- Notifications push
- Mode hors-ligne pour les données essentielles (consulter les fiches membres)

### 7.6 Export Excel avancé

- Export de toutes les listes avec mise en forme (couleurs, en-têtes, largeurs colonnes)
- Modèles d'export configurables
- Export programmé (rapports mensuels automatiques)

---

## 8. PRIORISATION

### Par priorité

| Priorité | Action | Impact métier | Effort estimé | Dépendances |
|----------|--------|:-------------:|:-------------:|:-----------:|
| **P0** | Portail partenaire (hôpital) | 🔥 Très élevé | 3-4 semaines | API REST |
| **P0** | API REST complète `/api/v1/` | 🔥 Très élevé | 2 semaines | DRF existant |
| **P1** | Migration PostgreSQL + Redis | Élevé | 1 semaine | - |
| **P1** | Recherche globale + HTMX/Alpine | Élevé | 1 semaine | - |
| **P1** | Notifications temps réel (WebSockets) | Élevé | 1-2 semaines | Redis, Channels |
| **P1** | Cache Redis + sessions | Moyen | 2-3 jours | Redis |
| **P1** | Celery (tâches async) | Moyen | 1 semaine | Redis |
| **P1** | Stockage cloud S3 | Moyen | 3-5 jours | django-storages |
| **P1** | Tests automatisés + CI/CD | Moyen | 2 semaines | pytest |
| **P1** | Linting (ruff) + pre-commit | Faible | 1 jour | - |
| **P2** | Dark mode | Faible | 3-5 jours | - |
| **P2** | Graphiques dashboard améliorés | Moyen | 1 semaine | Chart.js |
| **P2** | Responsive mobile | Moyen | 1 semaine | - |
| **P2** | Export PDF professionnel | Moyen | 1 semaine | reportlab |
| **P2** | GED centralisée | Élevé | 2 semaines | API REST |
| **P3** | Messagerie hôpital ↔ mutualité | Utile | 2 semaines | Channels |
| **P3** | QR Code carte membre | Utile | 1 semaine | qrcode lib |
| **P3** | 2FA | Faible | 1 semaine | django-otp |
| **P3** | Signature électronique | Faible | 2 semaines | - |
| **P3** | PWA | Utile | 1 semaine | - |
| **P3** | SMS/Email automatique | Utile | 1-2 semaines | Celery |

### Roadmap recommandée

```
Semaine 1-2   → API REST complète (/api/v1/)
Semaine 3-6   → Portail partenaire (hôpital) — authentification, dashboard, recherche membre
Semaine 7-8   → Portail partenaire — saisie facture, soumission, workflow complet
Semaine 9-10  → PostgreSQL + Redis + Celery en production
Semaine 11    → Notifications temps réel + Messagerie
Semaine 12-13 → Tests automatisés + CI/CD
Semaine 14    → Dark mode + Recherche globale HTMX
Semaine 15    → Graphiques dashboard + Export PDF
Semaine 16    → GED + Transfert documents médicaux
Semaine 17+   → 2FA, QR Code, PWA, SMS automatique
```

### Estimation d'effort total

| Phase | Durée | Développeurs |
|-------|-------|:------------:|
| Phase 1 (P0) — Fondation API + Portail | 8 semaines | 1-2 devs |
| Phase 2 (P1) — Infrastructure & Qualité | 4 semaines | 1 dev |
| Phase 3 (P2) — Améliorations UI/UX | 3 semaines | 1 dev |
| Phase 4 (P3) — Fonctionnalités avancées | 4 semaines | 1 dev |
| **Total** | **~19 semaines** | **1-2 devs** |

---

## RÉSUMÉ DES RECOMMANDATIONS CLÉS

### Ce qu'il faut faire MAINTENANT (P0)
1. ✅ **Créer l'API REST** — fondation de toute la modernisation
2. ✅ **Activer `UtilisateurPartenaire`** — authentification réelle pour les hôpitaux
3. ✅ **Créer le portail hôpital** — dashboard, recherche membre, saisie facture
4. ✅ **Ajouter `DocumentMedical`** — transfert structuré de documents

### Ce qu'il faut faire ENSUITE (P1)
5. ✅ **Migrer PostgreSQL** — production ready
6. ✅ **Ajouter Redis** — cache + sessions + WebSockets
7. ✅ **Notifications temps réel** — WebSockets + toasts
8. ✅ **Tests + CI/CD** — qualité et confiance
9. ✅ **Recherche globale HTMX** — productivité utilisateur

### Ce qu'il faut faire PLUS TARD (P2/P3)
10. ⏳ **Dark mode, graphiques, responsive**
11. ⏳ **GED, messagerie, QR Code**
12. ⏳ **2FA, PWA, SMS automatique**

---

*Document généré le 10 juillet 2026 — pour toute question, contactez le développeur.*
