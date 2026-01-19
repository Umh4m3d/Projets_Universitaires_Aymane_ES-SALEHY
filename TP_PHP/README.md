# TP PHP – Développement Web côté serveur

Ce dossier regroupe les travaux pratiques réalisés dans le cadre du module
**Développement Web côté serveur (PHP)**.  
Ces TP couvrent la création de pages dynamiques, la manipulation de tableaux,
l’accès sécurisé à une base de données avec PDO, et la découverte des
vulnérabilités LFI (Local File Inclusion) et leur protection.

---

## Objectifs pédagogiques

- Comprendre le fonctionnement de PHP côté serveur
- Créer des pages web dynamiques
- Manipuler des tableaux numériques, associatifs et multidimensionnels
- Se connecter et interagir avec une base de données MySQL via PDO
- Découvrir les failles LFI et mettre en place des protections
- Appliquer les bonnes pratiques pour l’affichage sécurisé des données

---

## Contenu du dossier

### 1️⃣ TP2 : Création de pages PHP dynamiques

**Description :**  
Création de pages web dynamiques avec PHP et inclusion de fichiers pour
structurer le site.

**Objectifs spécifiques :**
- Affichage de variables PHP
- Utilisation de la fonction `date()`
- Création de `header.php` et `footer.php`
- Inclusion de fichiers avec `include`

**Fichiers principaux :**
- `index.php` : page principale
- `header.php` : début de la page HTML
- `footer.php` : fin de la page HTML
- `calcul.php` : opérations numériques et conditions

**Instructions d’exécution :**
- Copier le dossier dans `htdocs` ou le serveur web local
- Accéder à `http://localhost/TP_PHP/index.php` dans un navigateur

---

### 2️⃣ TP3 : Manipulation de tableaux et structures de contrôle

**Description :**  
Travail sur les tableaux numériques, associatifs et multidimensionnels
en PHP, avec parcours et calcul de moyennes.

**Objectifs spécifiques :**
- Déclaration et parcours de tableaux
- Affichage des valeurs sur une page HTML
- Calcul de la moyenne des notes d’étudiants

**Fichiers principaux :**
- `tableaux.php` (exemple avec films, livres et étudiants)

---

### 3️⃣ TP4 : Affichage de données depuis une base de données (PDO)

**Description :**  
Connexion sécurisée à MySQL avec PDO et affichage des produits depuis la
base `ecommerce_securise_db`.

**Objectifs spécifiques :**
- Connexion à MySQL via PDO
- Exécution de requêtes `SELECT`
- Affichage sécurisé avec `htmlspecialchars()`
- Gestion des erreurs de connexion

**Fichiers principaux :**
- `produits.php` : affiche tous les produits

**Instructions d’exécution :**
- Créer la base `ecommerce_securise_db` et les tables
- Ajouter les utilisateurs MySQL avec privilèges limités
- Lancer Apache/MySQL, puis accéder à `produits.php`

---

### 4️⃣ TP5 : Lab LFI – exploitation et protection

**Description :**  
Étude de la vulnérabilité LFI (Local File Inclusion) et mise en place
d’une protection via liste blanche de fichiers autorisés.

**Objectifs spécifiques :**
- Comprendre et exploiter LFI
- Créer un fichier `lfi_vuln.php` volontairement vulnérable
- Mettre en place une version sécurisée avec whitelist

**Fichiers principaux :**
- `lfi_vuln.php` : fichier vulnérable et sécurisé
- `home.php` : page d’accueil
- `secret.txt` : fichier à protéger

**Instructions d’exécution :**
- Copier les fichiers dans `htdocs`
- Accéder à `http://localhost/TP_PHP/lfi_vuln.php?page=home.php`
- Tester la protection avec des fichiers non autorisés

