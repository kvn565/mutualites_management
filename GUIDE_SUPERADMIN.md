# Guide SuperAdmin — Administration de la plateforme

**Public cible** : Super Administrateur de la plateforme SaaS  
**Accès** : `/superadmin/` (après login `/connexion/` avec rôle `SUPER_ADMIN` ou `is_superuser`)

---

## 1. Première connexion & Dashboard

### 1.1 Connexion
1. Aller sur `https://votre-domaine.com/connexion/`
2. Identifiants SuperAdmin fournis à l'installation
3. Redirection auto vers `/superadmin/`

### 1.2 Dashboard (`/superadmin/`)
**Vue d'ensemble** :
- **Stats globales** : Mutualités (Actives/Essai/Suspendues/Expirées), Utilisateurs, Membres, Factures
- **Graphiques** : Membres & factures par mutualité
- **Alertes** :
  - Essais expirant (< 3 jours)
  - Mutualités sans licence
  - Licences expirant (< 7 jours)
- **Derniers audits** : 10 dernières actions SuperAdmin

---

## 2. Gestion des Mutualités

### 2.1 Liste (`/superadmin/mutualites/`)
**Filtres** : Recherche (nom, NIF, téléphone, responsable, code), Statut (ACTIF/ESSAI/SUSPENDU/EXPIRE/BLOQUE)  
**Actions** : Voir détail, Modifier, Suspendre, Réactiver, Renouveler, Prolonger essai, Réinitialiser, Export Excel

### 2.2 Créer une mutualité (`/superadmin/mutualites/creer/`)
**Étapes** :
1. Remplir formulaire :
   - **Identification** : NIF (vérif OBR auto), Nom, Sigle, Type (MUTUELLE/ASSOCIATION/COOPERATIVE/ENTREPRISE/AUTRE)
   - **Responsable** : Nom, Téléphone, Email
   - **Adresse** : Province, Commune, Zone, Quartier, Avenue, Numéro, Colline, Adresse complète
   - **Limites** : Max utilisateurs (défaut 10)
   - **Admin auto** : Username, Email, Mot de passe (laissés vides = auto-générés)
2. Cliquer **"Enregistrer"**
3. **Résultat** :
   - Mutualité créée + essai 14 jours activé
   - Admin mutualité créé : `admin_{code_mutualite}` / mot de passe affiché **une seule fois**
   - Journal audit tracé

> ⚠️ **Note** : Noter le mot de passe admin immédiatement (non récupérable plus tard)

### 2.3 Détail mutualité (`/superadmin/mutualites/<pk>/`)
**Onglets/Sections** :
- Infos générales + thème + licence
- **Partenaires liés** : Via FK direct + via `RelationPartenaireMutualite` + `Convention`
- **Journal audit** : 20 dernières actions

### 2.4 Actions sur mutualité

| Action | Condition | Effet |
|--------|-----------|-------|
| **Suspendre** | ACTIF ou ESSAI | Statut → SUSPENDU (accès coupé) |
| **Réactiver** | SUSPENDU | Statut → ESSAI (si essai_gratuit) ou ACTIF |
| **Renouveler licence** | Toute | Nouveau type abonnement + durée → date_expiration mise à jour |
| **Prolonger essai** | ESSAI | +N jours sur date_fin_essai & date_expiration |
| **Export Excel** | Toute | 16 onglets (voir §2.6) |
| **Réinitialiser** | Toute | **IRRÉVERSIBLE** — Supprime TOUTES données opérationnelles |

### 2.5 Renouveler licence (`/superadmin/mutualites/<pk>/renouveler/`)
1. Choisir **Type abonnement** : ESSAI (14j) / 1MOIS / 6MOIS / 12MOIS / 24MOIS / PERSONNALISE
2. Si PERSONNALISE : saisir Date début + Date fin
3. Valider → Mutualité : `statut=ACTIF`, `date_expiration` mise à jour, `cle_activation` liée

### 2.6 Export Excel mutualité (`/superadmin/mutualites/<pk>/export-excel/`)
**16 feuilles** :
1. Mutualité (infos complètes)
2. Utilisateurs
3. Groupes
4. Affiliés
5. Ayants droit
6. Cotisations
7. Factures
8. Lignes facture
9. Services santé
10. Partenaires
11. Conventions
12. Utilisateurs partenaires
13. Origines
14. Médicaments
15. Notifications
16. Journal audit

### 2.7 Réinitialiser mutualité (`/superadmin/mutualites/<pk>/reinitialiser/`)
**⚠️ DANGER — IRRÉVERSIBLE**
1. Sélectionner mutualité → stats affichées (nb affiliés, factures, etc.)
2. Cliquer **"Exporter en Excel"** (backup) — **OBLIGATOIRE avant reset**
3. Cliquer **"Réinitialiser"** → Modale confirmation
4. Saisir **exactement le nom de la mutualité** pour confirmer
5. Validation → Suppression atomique (transaction) de :
   - Origines, Services, Factures, Cotisations, Ayants droit, Affiliés, Partenaires
   - **Conservés** : Mutualité, Utilisateurs, Groupes, Licence, Thème, Journal audit

---

## 3. Gestion Utilisateurs Plateforme

### 3.1 Liste (`/superadmin/utilisateurs/`)
**Filtres** : Recherche, Rôle, Mutualité  
**Colonnes** : Username, Nom complet, Email, Rôle, Mutualité, Actif, Date création

### 3.2 Créer utilisateur (`/superadmin/utilisateurs/creer/`)
1. Username, Email, Nom, Postnom, Prénom, Téléphone
2. **Rôle** : SUPER_ADMIN / ADMIN_MUTUALITE / COMPTABLE / AGENT / CONSULTATION
3. **Mutualité** : Obligatoire sauf SUPER_ADMIN (laissé vide)
4. Mot de passe (laissé vide = auto-généré + affiché une fois)
5. Actif : Oui/Non

### 3.3 Règles de suppression
- ❌ Impossible de supprimer **son propre compte**
- ❌ Impossible de supprimer un **autre SUPER_ADMIN**

---

## 4. Clés d'Activation (Licences)

### 4.1 Liste (`/superadmin/cles/`)
**Filtres** : Recherche, Statut (DISPONIBLE/UTILISEE/REVOQUEE/EXPIREE), Type plan  
**Colonnes** : Clé visible, Mutualité, Type plan, Dates, Statut, Utilisée, Créée par

### 4.2 Générer clé (`/superadmin/cles/generer/`)
1. Mutualité (dropdown)
2. Type plan : ESSAI / 1MOIS / 6MOIS / 12MOIS / 24MOIS / PERSONNALISE
3. Si PERSONNALISE : Date début + Date fin
4. Valider → Clé générée : `CLE-XXXX-XXXX` (format visible)
5. **Copier la clé** — elle n'est plus affichée en clair après

### 4.3 Activer clé (`/superadmin/cles/<pk>/activer/`)
- Disponible seulement si statut `DISPONIBLE`
- Lie clé à mutualité : met à jour `cle_activation`, `date_activation`, `date_expiration`, `type_abonnement`, `statut=ACTIF`
- Journal `AuditCle` tracé

### 4.4 Révoquer clé (`/superadmin/cles/<pk>/revoquer/`)
- Motif obligatoire
- Clé → `active=False`, `statut=REVOQUEE`
- Mutualité non affectée (garde sa licence en cours)

---

## 5. Configuration Application (Globale)

### 5.1 Accès : `/superadmin/configuration/`
**Singleton** `ConfigurationApp` — s'applique à TOUTES les mutualités (fallback si mutualité n'a pas son thème)

**Champs** :
- **Identité** : Nom application, Email contact, Téléphone support
- **Thème** : Couleur primaire, secondaire, fond, texte, image fond, opacité, luminosité
- **Fonctionnalités** : Modules activés, pagination, formats export

---

## 6. Partenaires Globaux (Toutes mutualités)

### 6.1 Liste (`/superadmin/partenaires/`)
**Filtres** : Recherche, Type (HOPITAL/CLINIQUE/PHARMACIE/...), Statut, Mutualité

### 6.2 Actions
- **Suspendre** : ACTIF/EN_ATTENTE → SUSPENDU
- **Réactiver** : SUSPENDU → ACTIF
- **Bloquer** : → BLOQUE (accès portail coupé)
- **Débloquer** : BLOQUE → ACTIF

---

## 7. Audit Connexions

### 7.1 Accès : `/superadmin/audit/connexions/`
**Filtres** : Recherche (user, IP, user-agent), Mutualité  
**Colonnes** : Utilisateur, Mutualité, IP, User Agent, Date, Succès/Échec

---

## 8. Messages des Mutualités

### 7.1 Accès : `/superadmin/aide/messages/`
**Filtres** : Statut (NOUVEAU/EN_COURS/REPONDU/FERME), Mutualité, Recherche  
**Actions** :
- Voir détail → Passe auto `NOUVEAU` → `EN_COURS`
- **Répondre** : Saisie réponse → Statut `REPONDU` + date + auteur
- **Changer statut** : Dropdown direct

---

## 9. Documents Publics (Documentation SuperAdmin)

### 9.1 Accès : `/superadmin/aide/documents/`
**Modèle** : `DocumentSuperAdmin` (type : DOCUMENTATION/GUIDE/FAQ)

### 9.2 Créer document (`/superadmin/aide/documents/creer/`)
1. **Type** : DOCUMENTATION / GUIDE / FAQ
2. **Titre** + **Slug** (auto si vide)
3. **Résumé** (affiché en liste)
4. **Contenu** : HTML/Markdown (éditeur riche)
5. **Fichier joint** : PDF, DOC, etc. (optionnel)
6. **Vidéo** : URL YouTube/Vimeo (optionnel)
7. **Version** : ex "1.0"
8. **Publié** : Oui/Non (si oui → date_publication = maintenant)
9. **Ordre** : Tri affichage

### 9.3 Publication pour mutualités
- Document `publie=True` → visible dans :
  - `/aide/` (index mutualité) — 10 derniers
  - `/aide/documents-superadmin/` (liste complète, filtres type/recherche)
  - `/aide/documents-superadmin/<slug>/` (détail)

---

## 10. Raccourcis & Astuces

| Action | Raccourci / Astuce |
|--------|-------------------|
| Tuer processus Django avant restart | `taskkill /f /im python.exe` (Windows) |
| Vérifier config | `python manage.py check` |
| Shell Django | `python manage.py shell` |
| Voir SQL migrations | `python manage.py sqlmigrate app 0001` |
| Créer superuser | `python manage.py createsuperuser` |

---

## 11. Dépannage courant

| Problème | Solution |
|----------|----------|
| Mutualité ne voit pas thème | Vérifier `Mutualite.primary_color` etc. non vides, sinon fallback `ConfigurationApp` |
| Licence expirée mais accès OK | Vérifier `LicenseMiddleware` exemptions (`/connexion/`, `/licence/`, `/admin/`, SuperAdmin) |
| Partenaire ne voit pas mutualité | Vérifier `RelationPartenaireMutualite.statut=ACTIVE` ou `Convention.statut=ACTIVE` |
| Export Excel corrompu | Vérifier `openpyxl` installé, relancer `pip install openpyxl` |

---

*Guide SuperAdmin — Mutualité de Santé v1.0*