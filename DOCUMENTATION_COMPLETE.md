# Documentation Complète — Mutualité de Santé (SaaS Burundi)

**Version :** 1.0  
**Date :** Août 2026  
**Framework :** Django 5.1 / Python 3.12 / SQLite3 (PostgreSQL en prod)  
**Langue :** Français | **Devise :** BIF

---

## Table des matières

1. [Architecture générale](#1-architecture-générale)
2. [SuperAdmin — Administration plateforme](#2-superadmin--administration-plateforme)
3. [Admin Mutualité — Gestion d'une mutuelle](#3-admin-mutualité--gestion-dune-mutuelle)
4. [Agent / Comptable — Opérations quotidiennes](#4-agent--comptable--opérations-quotidiennes)
5. [Partenaire (Hôpital/Pharmacie) — Portail libre-service](#5-partenaire-hôpitalpharmacie--portail-libre-service)
6. [Affilié / Membre — Espace adhérent](#6-affilié--membre--espace-adhérent)
7. [Référence technique](#7-référence-technique)

---

## 1. Architecture générale

### 1.1 Multi-tenant (Une mutualité = un tenant isolé)
- **Isolation** : Tous les modèles métier ont `FK mutualite` + `TenantManager()` (filtre auto par `request.current_mutualite`)
- **Middleware** : `MutualiteMiddleware` → `request.current_mutualite` + thread-local
- **Modèles globaux (non filtrés)** : `ConfigurationApp`, `MessageSuperAdmin`, `DocumentSuperAdmin`

### 1.2 Trois systèmes d'authentification
| Système | Modèle | Login | Usage |
|---------|--------|-------|-------|
| **Mutualité** | `core.Utilisateur` (extends `AbstractUser`) | `/connexion/` | Admins, agents, comptables d'une mutualité |
| **Partenaire** | `partenaires.UtilisateurPartenaire` (custom, hash pwd) | `/portail/connexion/` | Hôpitaux, cliniques, pharmacies |
| **SuperAdmin** | `core.Utilisateur` rôle `SUPER_ADMIN` ou `is_superuser` | `/superadmin/` + `/admin/` | Admin plateforme (aucune mutualité) |

### 1.3 Rôles utilisateur mutualité
- `SUPER_ADMIN` : Accès `/superadmin/` (plateforme)
- `ADMIN_MUTUALITE` : Admin complet de sa mutualité
- `COMPTABLE` : Factures, cotisations, comptabilité, exports
- `AGENT` : Affiliés, ayants droit, factures (saisie)
- `CONSULTATION` : Lecture seule (dashboard, recherche membres)

---

## 2. SuperAdmin — Administration plateforme

**URL d'accès** : `/superadmin/` (vues custom) + `/admin/` (Django admin)

### 2.1 Dashboard global (`/superadmin/`)
- Stats : mutualités par statut, utilisateurs, membres, factures
- Graphiques : membres/factures par mutualité
- Alertes : essais expirant, licences prochaines expiration

### 2.2 Gestion des mutualités (`/superadmin/mutualites/`)
**Liste** : Recherche (nom, NIF, téléphone, responsable), filtre statut, pagination

**Créer** (`/superadmin/mutualites/creer/`) :
1. Formulaire : NIF, nom, sigle, type, responsable, contacts, adresse, max utilisateurs
2. Création auto admin mutualité : `admin_{code_mutualite}` + mot de passe aléatoire
3. Activation essai 14 jours auto
4. Journal audit

**Détail** (`/superadmin/mutualites/<pk>/`) :
- Infos mutualité, partenaires liés (FK + relations), journal audit 20 derniers

**Actions** :
- **Suspendre** : `ACTIF/ESSAI` → `SUSPENDU`
- **Réactiver** : `SUSPENDU` → `ESSAI` (si essai) ou `ACTIF`
- **Renouveler licence** : Type abonnement (ESSAI/1MOIS/6MOIS/12MOIS/24MOIS/PERSONNALISE) + durée
- **Prolonger essai** : +N jours
- **Réinitialiser** : Suppression atomique toutes données opérationnelles (16 onglets Excel exportables avant)
- **Export Excel** : 16 feuilles (Mutualité, Utilisateurs, Groupes, Affiliés, Ayants droit, Cotisations, Factures, Lignes facture, Services, Partenaires, Conventions, Utilisateurs partenaires, Origines, Médicaments, Notifications, Journal audit)

### 2.3 Gestion utilisateurs plateforme (`/superadmin/utilisateurs/`)
CRUD complet, filtres rôle/mutualité/recherche. Suppression interdite pour soi-même et autres SUPER_ADMIN.

### 2.4 Clés d'activation (`/superadmin/cles/`)
- Génération : mutualité + type plan + dates → clé visible (`CLE-XXXX-XXXX`)
- Activation : lie clé à mutualité, met à jour `cle_activation`, `date_expiration`, `statut=ACTIF`
- Révocation : motif, désactive clé

### 2.5 Configuration application (`/superadmin/configuration/`)
Singleton `ConfigurationApp` : thème global (couleurs, images, nom app, email contact, etc.)

### 2.6 Partenaires globaux (`/superadmin/partenaires/`)
CRUD partenaires toutes mutualités, filtres type/statut/mutualité. Suspendre/Réactiver/Bloquer/Débloquer.

### 2.7 Audit connexions (`/superadmin/audit/connexions/`)
Historique connexions toutes mutualités, filtres recherche/mutualité.

---

## 3. Admin Mutualité — Gestion d'une mutuelle

**URL d'accès** : `/dashboard/` après login `/connexion/` (rôle `ADMIN_MUTUALITE`)

### 3.1 Dashboard mutualité (`/dashboard/`)
Vue synthèse : stats membres, factures, cotisations, alertes plafonds, graphiques.

### 3.2 Utilisateurs mutualité (`/utilisateurs/`)
- **CRUD** : Création agents/comptables, assignation groupes/menus
- **Groupes** (`/groupe/`) : Groupes d'utilisateurs + menus autorisés (M2M `Menu`)
- **Permissions** : Par rôle (`est_admin`, `peut_modifier`, `peut_valider`, `peut_exporter`) + par groupe (`menus_autorises`)

### 3.3 Affiliés — Membres (`/affilies/`)
**Liste** : Recherche (nom, n° affiliation, n° carte, téléphone), filtres statut/origine, pagination

**Créer** :
1. Infos personnelles : nom, postnom, prénom, sexe, naissance, téléphone, email, profession, groupe sanguin
2. Adhésion : origine, date adhésion, statut (ACTIF/EN_ATTENTE/SUSPENDU/RADIE), photo
3. Plafonds (hérités de `Mutualite.def_*` ou personnalisés) :
   - Soins ambulatoires, Hospitalisation générale, Chirurgie, Maternité
   - Pharmacie, Laboratoire, Imagerie, Dentaire, Ophtalmologie
   - Plafonnement mensuel/annuel
4. Ayants droit (liés après création)

**Détail membre** :
- Infos, ayants droit, factures, consommation mensuelle, plafonds effectifs, exclusions (global/origine/individuel)
- Actions : Bloquer/Débloquer, Modifier, Voir factures

**Import/Export** : Excel (modèle fourni)

### 3.4 Ayants droit (`/ayants_droit/`)
Liés à un affilié : nom, prénom, sexe, naissance, lien parenté (CONJOINT/ENFANT/PARENT/AUTRE), actif, photo. Plafonds hérités de l'affilié.

### 3.5 Services de santé (`/services_sante/`)
**Catalogue** : Code auto (CAT-XXX), nom, catégorie (CONSULTATION/HOSPITALISATION/CHIRURGIE/MATERNITE/LABORATOIRE/IMAGERIE/DENTAIRE/OPHTALMOLOGIE/PHARMACIE/AUTRE), description, taux prise en charge (%), plafond, conditions, actif.

### 3.6 Origines — Groupes d'origine (`/origines/`)
Entreprises, coopératives, associations. Plafonds par défaut applicables aux nouveaux affiliés de cette origine.

### 3.7 Facturation (`/factures/`)
**Workflow** : `BROUILLON` → `SOUMIS` → `VALIDE` → `PAYE` / `REJETE`

**Créer facture** :
1. Sélection membre (+ ayant droit optionnel)
2. Lignes : Service **OU** Médicament + Qté + Prix unitaire + Taux appliqué (%)
3. Calcul auto : `montant_total` = Σ(qté × PU), `montant_mutualite` = Σ(qté × PU × taux/100), `montant_ticket_moderateur` = reste
4. Enregistrement brouillon → Soumettre pour validation

**Validation** (rôle `peut_valider`) : `SOUMIS` → `VALIDE` ou `REJETE` (motif)

**Paiement** : `VALIDE` → `PAYE` (mode : CASH/MOBILE/BANQUE/COOPERATIVE/CHEQUE)

**Exclusions** : 3 niveaux (Mutualité globale, Origine, Affilié individuel) sur services/médicaments

### 3.8 Cotisations (`/cotisations/`)
**Workflow** : Création → Validation

**Modes paiement** : CASH, MOBILE, BANQUE, COOPERATIVE, CHEQUE
**Périodicité** : Mensuel / Trimestriel / Annuel
**Liaison** : Affilié (+ ayant droit optionnel), montant, mois/année, référence

### 3.9 Pharmacie — Médicaments (`/pharmacie/`)
**Catégories** : Nom, description
**Médicaments** : Code AMM/interne (unique), nom commercial, DCI, catégorie, forme (COMPRIME/SIROP/INJECTION/GELULE/POMMADE/GOUTTES/SUPPOSITOIRE/AUTRE), dosage, prix référence, taux remboursement (%), pris en charge (oui/non), actif

### 3.10 Comptabilité SYSCOHADA (`/comptabilite/`)
- **Plan comptable** : Comptes (numéro, nom, type, classe), soldes
- **Écritures** : Journal, date, libellé, lignes (compte, débit, crédit), lettrage
- **Budgets** : Par compte/exercice, suivi réalisation
- **Trésorerie** : Caisses/banques, rapprochement bancaire
- **Rapprochement** : Pointage relevés vs écritures

### 3.11 Ventilations analytiques (`/ventilations/`)
Répartition charges par centre de coût et branche d'activité.

### 3.12 Gestion chambres (`/chambres/`)
Chambres d'hospitalisation : numéro, type, tarif, statut (LIBRE/OCCUPEE/MAINTENANCE), affectation patient.

### 3.13 Notifications & Alertes
- Plafonds : `APPROCHE` (80%), `ATTEINT` (100%), `DEBLOCAGE`
- Marques `vue` par utilisateur

### 3.14 Corbeille unifiée (`/corbeille/`)
Soft-delete 30 jours auto-purge : tous modèles `SoftDeleteMixin`. Restauration possible.

### 3.15 Aide locale (`/aide/`)
- Catégories + Articles (HTML/Markdown), publication, ordre, recherche
- Accessible aux utilisateurs de la mutualité

### 3.16 Messagerie vers SuperAdmin (`/aide/messages/`)
Envoi messages (sujet + contenu) → SuperAdmin reçoit dans `/superadmin/aide/messages/`

---

## 4. Agent / Comptable — Opérations quotidiennes

### 4.1 Agent (`role=AGENT`)
**Accès** : Affiliés (CRUD), Ayants droit, Factures (création/soumission), Cotisations (saisie), Recherche membres, Documents médicaux

**Facturation** :
1. `/factures/ajouter/` → Choisir membre → Ajouter lignes (services/medicaments)
2. Vérifier plafonds dispo (alertes auto)
3. Enregistrer `BROUILLON` → `SOUMETTRE` pour validation

**Cotisations** :
1. `/cotisations/ajouter/` → Membre + montant + période + mode paiement
2. Valider (si droit) ou laisser en attente

### 4.2 Comptable (`role=COMPTABLE`)
**Accès** : Tout Agent + Comptabilité, Factures (validation/paiement), Cotisations (validation), Exports, Rapports

**Validation factures** : Liste `SOUMIS` → `VALIDE` ou `REJETE` (motif obligatoire)

**Paiement factures** : `VALIDE` → `PAYE` (sélection mode, référence, date)

**Exports** : Factures, cotisations, membres (Excel/PDF)

---

## 5. Partenaire (Hôpital/Pharmacie) — Portail libre-service

**URL** : `/portail/` → Login `/portail/connexion/` (session `partenaire_user_id`)

### 5.1 Inscription (`/portail/inscription/`)
Formulaire établissement : type, nom, NIF, contacts, adresse, responsable, dates convention, taux/plafond. Statut `EN_ATTENTE` → validation mutualité → `ACTIF`

### 5.2 Dashboard partenaire (`/portail/`)
- Stats factures (total, en attente, validées, payées, montants)
- Graphiques : statuts, 6 derniers mois
- Factures récentes, membres récents
- Convention active/inactive
- Sélecteur mutualité (si multiples relations)

### 5.3 Recherche membre (`/portail/recherche/`)
Par n° affiliation, n° carte, nom, prénom, téléphone. Résultats : 30 max avec mutualité d'origine.

### 5.4 Détail membre (`/portail/membre/<pk>/`)
- Infos membre + ayants droit
- Factures chez ce partenaire (10 dernières)
- Consommation mois, plafond mensuel, reste
- Documents médicaux (10 derniers)
- **Exclusions** : services/médicaments exclus (global/origine/individuel) — affichés ⛔

### 5.5 Créer facture (`/portail/facture/ajouter/<membre_pk>/`)
1. Formulaire général : n° dossier, date, bénéficiaire (titulaire/ayant droit), diagnostic, notes
2. Lignes dynamiques (JS) :
   - **Service** : dropdown services de LA mutualité du membre (actifs)
   - **Médicament** : dropdown médicaments de LA mutualité (actifs + `pris_en_charge=True`)
   - Auto-remplissage : sélection → prix référence + taux remboursement
   - Catalogue latéral cliquable (recherche temps réel)
   - Exclusions grisées/désactivées (⛔)
3. Calculs temps réel : Total ligne, Part mutuelle, Ticket modérateur
4. Enregistrer `BROUILLON` → Soumettre

**Facture simple** (`/portail/facture/simple/`) : Sans membre préalable (client libre), choix mutualité.

### 5.6 Gestion factures (`/portail/factures/`)
Liste avec filtres statut/mois/année, pagination. Actions : Détail, Imprimer reçu, Export PDF (WeasyPrint).

### 5.7 Documents médicaux (`/portail/document/ajouter/<membre_pk>/`)
Upload : type (ORDONNANCE/RESULTAT_ANALYSE/COMPTE_RENDU/IMAGERIE/CARTE_MEMBRE/AUTRE), fichier, description. Lié à facture optionnel.

### 5.8 Catalogue médicaments (`/portail/medicaments/`)
**Liste** : Recherche nom/code/DCI, filtre forme, pagination. **CRUD** : Ajouter/Modifier/Supprimer (scope = mutualités liées au partenaire)

### 5.9 Catalogue services (`/portail/services/`)
**Liste** : Recherche nom/code, filtre catégorie, pagination. **CRUD** : Ajouter/Modifier/Supprimer (scope = mutualités liées)

### 5.10 Profil & Configuration
- **Profil** (`/portail/profil/`) : Infos établissement, relations mutualités (actives/bloquées), actions bloquer/débloquer relation
- **Modifier profil** : Infos, logo, thème (couleurs, image fond, opacité, luminosité)
- **Compte** : Changement mot de passe, infos utilisateur (nom, email, téléphone, photo, rôle)
- **Créer utilisateur partenaire** : Gestionnaire/Pharmacien/Médecin/Réceptionniste/Comptable

---

## 6. Affilié / Membre — Espace adhérent

> **Note** : L'espace adhérent n'est pas encore implémenté dans le code actuel. Prévu pour :
- Consultation plafonds/restes
- Historique factures/remboursements
- Demande prise en charge
- Messagerie
- Documents (cartes, ordonnances)

---

## 7. Référence technique

### 7.1 URLs principales
| URL | App | Description |
|-----|-----|-------------|
| `/` | core | Landing → redirection selon auth |
| `/connexion/` | core | Login mutualité |
| `/dashboard/` | dashboard | Dashboard mutualité |
| `/superadmin/` | superadmin | Panel SuperAdmin |
| `/portail/` | portail_partenaire | Portail partenaires |
| `/affilies/` | affilies | Gestion membres |
| `/factures/` | factures | Facturation |
| `/cotisations/` | cotisations | Cotisations |
| `/comptabilite/` | comptabilite | Comptabilité SYSCOHADA |
| `/pharmacie/` | pharmacie | Médicaments |
| `/aide/` | aide | Aide + messages SuperAdmin |
| `/chambres/` | gestion_chambres | Chambres hospit. |

### 7.2 Modèles clés (FK mutualite + TenantManager)
- `core.Mutualite` : thème, licence (15 champs `def_*` plafonds défaut)
- `affilies.Affilie` : membre + plafonds effectifs (hérités ou surchargés)
- `ayants_droit.AyantDroit` : lié à Affilie
- `services_sante.ServiceSante` : catalogue soins
- `pharmacie.Medicament` : catalogue médicaments + remboursement
- `partenaires.Partenaire` : établissement + conventions
- `factures.Facture` : workflow brouillon→soumis→valide→payé/rejeté
- `cotisations.Cotisation` : paiements membres
- `comptabilite.*` : PlanComptable, Ecriture, Budget, Tresorerie, Rapprochement

### 7.3 Commandes utiles
```bash
python manage.py runserver          # Lancer serveur
python manage.py check              # Vérifier projet
python manage.py makemigrations     # Créer migrations
python manage.py migrate            # Appliquer migrations
python manage.py shell              # Console Django
```

### 7.4 Templates de base
- `base.html` : Layout connecté (AdminLTE), blocs `title`, `sidebar_nav`, `content`, `extra_js`
- `base_auth.html` : Pages auth (fond `APP_BACKGROUND_IMAGE_URL`)
- `superadmin/base_superadmin.html` : Sidebar SuperAdmin
- `portail_partenaire/base_portail.html` : Layout portail partenaires

### 7.5 Context processors (variables globales templates)
- `app_config` : `APP_NOM`, `APP_PRIMARY_COLOR`, `APP_BACKGROUND_IMAGE_URL`...
- `mutualite_context` : `MUTUALITE_PRIMARY_COLOR`, `MUTUALITE_BACKGROUND_IMAGE_URL`, `licence_15j`
- `superadmin_notifications` : `superadmin_nb_messages_nouveaux`

---

## Annexe : Workflow facture médicale (détail)

```
BROUILLON (création partenaire/agent)
    │
    ├─→ SOUMIS (soumission pour validation)
    │       │
    │       ├─→ VALIDE (validation comptable/admin)
    │       │       │
    │       │       └─→ PAYE (paiement effectif)
    │       │
    │       └─→ REJETE (rejet + motif obligatoire)
    │
    └─→ (Suppression corbeille si brouillon)
```

**Calculs** :
- `montant_total` = Σ(lignes: qté × prix_unitaire)
- `montant_mutualite` = Σ(lignes: qté × prix_unitaire × taux_applique / 100)
- `montant_ticket_moderateur` = montant_total - montant_mutualite

---

*Documentation générée pour la plateforme Mutualité de Santé — Burundi*