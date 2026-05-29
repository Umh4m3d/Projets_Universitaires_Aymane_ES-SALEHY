# CampusOps

## 1. Présentation du projet

CampusOps est une plateforme de gestion académique conçue pour centraliser les opérations quotidiennes d'un établissement ou d'un centre de formation.  
Le projet permet à plusieurs acteurs de travailler dans un même système :

- `admin`
- `secretaire`
- `teacher`
- `student`

L'objectif principal est de simplifier la gestion :

- des séances de cours
- des demandes de validation de séances
- des absences
- des paiements
- des profils utilisateurs
- des notifications e-mail
- du bot Telegram
- des automatisations OpenClaw

Le projet a été réalisé comme application full stack avec une API backend, une interface web frontend, un bot Telegram et un ensemble de workflows automatisés.

---

## 2. Objectifs fonctionnels

CampusOps répond aux besoins suivants :

- authentification avec rôles
- gestion des utilisateurs
- planification des séances
- validation des demandes de séances soumises par les enseignants
- suivi des absences
- suivi des paiements et détection des retards
- demandes de modification de profil
- envoi d'e-mails automatiques
- interaction rapide via Telegram

---

## 3. Fonctionnalités principales

### Administration

- création et gestion des comptes
- consultation des demandes de séances en attente
- validation ou rejet des séances
- consultation des demandes de modification de profil
- suivi des notifications internes
- suivi des paiements en retard

### Enseignant

- consultation de ses séances du jour et de la semaine
- soumission de demandes de nouvelles séances
- suivi des notifications
- saisie du progrès pédagogique
- marquage des absences

### Étudiant

- consultation de son planning
- consultation de ses absences
- consultation de ses paiements
- réception des notifications
- configuration d'une adresse e-mail personnelle
- liaison de son compte avec Telegram

### Automatisation OpenClaw

- envoi du planning hebdomadaire aux enseignants
- détection des paiements en retard
- création de tâches de suivi
- annulation de séances et diffusion des notifications

---

## 4. Architecture du projet

Le projet est divisé en quatre blocs principaux :

### Frontend

- React
- Vite
- Material UI

Le frontend fournit l'interface utilisateur web.

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

Le backend expose toutes les routes métier, gère la sécurité, la base de données et les workflows applicatifs.

### Base de données

- PostgreSQL

La base stocke les utilisateurs, séances, absences, paiements, notifications, profils étudiants, demandes de modification, etc.

### Services annexes

- Bot Telegram
- OpenClaw
- Services e-mail SMTP / IMAP

---

## 5. Architecture logique simplifiée

```text
Frontend React
      |
      v
API FastAPI
      |
      v
PostgreSQL
      |
      +--> Bot Telegram
      +--> OpenClaw
      +--> Service e-mail
```

---

## 6. Structure du dépôt

```text
campusops/
├── app/                    # Backend FastAPI
├── bot/                    # Bot Telegram
├── frontend/               # Frontend React/Vite
├── alembic/                # Migrations
├── openclaw/               # Scripts et logique OpenClaw
├── TESTS/                  # Scripts de démonstration
├── Dockerfile.backend
├── Dockerfile.frontend
├── Dockerfile.bot
├── docker-compose.yml
├── .env.example
├── .env.docker.example
├── .dockerignore
├── .gitignore
├── nginx.conf
├── README.md
├── RAPPORT.md
├── requirements.txt
├── alembic.ini
└── migrate.py
```

---

## 7. Technologies utilisées

- Python 3
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- React
- Vite
- Material UI
- Docker
- Docker Compose
- Telegram Bot API

---

## 8. Prérequis

Pour exécuter le projet localement sans Docker :

- Python 3.10 ou plus
- Node.js 20 ou plus
- npm
- PostgreSQL

Pour exécuter le projet avec Docker :

- Docker
- Docker Compose

---

## 9. Variables d'environnement

Le dépôt ne contient pas de secrets réels.

Les fichiers d'exemple fournis à la racine sont :

- `.env.example` pour une exécution locale sans Docker
- `.env.docker.example` pour une exécution avec Docker
- `frontend/.env.example` pour le frontend en mode développement

Il faut créer un fichier `.env` à partir de `.env.example`.

Exemple :

```bash
cp .env.example .env
```

Pour Docker :

```bash
cp .env.docker.example .env.docker
```

Pour le frontend local :

```bash
cp frontend/.env.example frontend/.env
```

Puis compléter uniquement vos propres valeurs :

- `SECRET_KEY`
- `DATABASE_URL`
- `OPENCLAW_KEY`
- `TELEGRAM_BOT_TOKEN`
- `MAIL_USER`
- `MAIL_PASSWORD`

Important :

- ne jamais publier `.env`
- ne jamais publier `.env.docker`
- ne jamais publier `frontend/.env`
- ne jamais mettre de mot de passe réel dans le `README.md`

---

## 10. Lancement en local sans Docker

### 10.1 Backend

Créer un environnement virtuel puis installer les dépendances :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Lancer les migrations :

```bash
alembic upgrade head
```

Démarrer le backend :

```bash
uvicorn app.main:app --reload
```

Le backend sera disponible sur :

```text
http://localhost:8000
```

### 10.2 Frontend

Dans un autre terminal :

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Le frontend sera disponible sur :

```text
http://localhost:5173
```

### 10.3 Bot Telegram

Dans un autre terminal :

```bash
python bot/main.py
```

---

## 11. Lancement avec Docker

Cette procédure a été validée sur une installation propre avec PostgreSQL, backend, frontend et bot.

### 11.1 Préparation

Créer le fichier d'environnement Docker :

```bash
cp .env.docker.example .env.docker
```

Compléter les vraies valeurs.

Si vous ne configurez pas `TELEGRAM_BOT_TOKEN`, le conteneur du bot restera en attente sans bloquer le reste du projet.

### 11.2 Réinitialisation propre de l'environnement

Pour repartir d'une base vide :

```bash
sudo docker compose --env-file .env.docker down -v
```

### 11.3 Build

Sur certaines machines, Docker nécessite `sudo`.  
Si `docker compose` renvoie `permission denied while trying to connect to the docker API`, utilisez `sudo docker compose ...`.

```bash
sudo docker compose --env-file .env.docker build
```

Si vous souhaitez forcer une reconstruction des images backend et bot :

```bash
sudo docker compose --env-file .env.docker build --no-cache backend bot
```

### 11.4 Démarrage

```bash
sudo docker compose --env-file .env.docker up -d
```

### 11.5 Vérification des conteneurs

```bash
sudo docker compose --env-file .env.docker ps
```

Les services attendus sont :

- `campusops-postgres`
- `campusops-backend`
- `campusops-frontend`
- `campusops-bot`

Le backend doit devenir `healthy`.

### 11.6 Vérification HTTP

Backend :

```text
http://localhost:8000/health
```

Frontend :

```text
http://localhost:5173
```

On peut aussi tester rapidement avec :

```bash
curl http://localhost:8000/health
```

### 11.7 Logs utiles

```bash
sudo docker compose --env-file .env.docker logs -f backend
sudo docker compose --env-file .env.docker logs -f frontend
sudo docker compose --env-file .env.docker logs -f bot
sudo docker compose --env-file .env.docker logs -f postgres
```

### 11.8 Peuplement de la base de démonstration

Après le démarrage des conteneurs, exécuter :

```bash
sudo docker compose --env-file .env.docker exec backend python migrate.py
```

Le script :

- crée le premier compte admin si la base est vide
- crée les groupes, cours, enseignants et étudiants de démonstration
- ajoute des séances et des entrées de progression pédagogique

### 11.9 Problèmes connus en démonstration

- `429 Too Many Requests` sur `/api/v1/auth/login` signifie simplement que trop de tentatives de connexion ont été envoyées en moins d'une minute
- dans ce cas, attendre environ 60 secondes avant de réessayer
- `GET /favicon.ico 404` n'est pas bloquant

---

## 12. Données de démonstration

Le script `migrate.py` permet de peupler le système avec des données de démonstration.

Exécution :

```bash
python migrate.py
```

Avec Docker :

```bash
sudo docker compose --env-file .env.docker exec backend python migrate.py
```

Comptes de démonstration créés par le seed :

- admin : `admin@campusops.com` / `Admin1234`
- secrétaires : comptes `@eidia.ma`
- enseignants : comptes `@eidia.ma`
- étudiants : comptes `@eidia.ma`

---

## 13. Scripts de test et de démonstration

Le dossier `TESTS/` contient un script de démonstration des flux e-mail :

- `campusops_mail_demo.py`

Ce script déclenche automatiquement :

- e-mail de planning hebdomadaire
- e-mail de paiement en retard
- e-mail d'annulation de séance
- e-mail de réinitialisation de mot de passe
- e-mail d'absence
- e-mail d'alerte parent

Exécution :

```bash
python3 TESTS/campusops_mail_demo.py
```

---

## 14. Vérification rapide du projet

### Scénario 1 : interface web

1. Ouvrir `http://localhost:5173`
2. Se connecter avec un compte de démonstration
3. Vérifier le dashboard
4. Créer une séance
5. Vérifier les pages absences, paiements, utilisateurs

### Scénario 2 : validation des demandes de séance

1. Se connecter comme enseignant
2. Soumettre une demande de séance
3. Se connecter comme admin
4. Vérifier la file d'attente
5. Approuver ou rejeter la demande

### Scénario 3 : Telegram

1. Générer un code de liaison depuis le profil
2. Envoyer `/link CODE` au bot
3. Tester `/today`, `/week`, `/notifications`
4. Tester les commandes admin si un compte admin est lié

### Scénario 4 : flux e-mail

1. Configurer `MAIL_USER` et `MAIL_PASSWORD`
2. Exécuter le script `TESTS/campusops_mail_demo.py`
3. Vérifier la réception des e-mails

### Scénario 5 : validation Docker

1. Construire les images avec `sudo docker compose --env-file .env.docker build`
2. Démarrer les services avec `sudo docker compose --env-file .env.docker up -d`
3. Vérifier `http://localhost:8000/health`
4. Vérifier `http://localhost:5173`
5. Peupler la base avec `sudo docker compose --env-file .env.docker exec backend python migrate.py`
6. Vérifier la connexion admin

---

## 15. Commandes Telegram principales

Le bot est maintenant sensible au rôle utilisateur.

### Admin

- `/today`
- `/week`
- `/requests`
- `/notifications`
- `/overdue`

### Teacher

- `/today`
- `/week`
- `/notifications`

### Student

- `/today`
- `/week`
- `/absence`
- `/payments`
- `/notifications`

---

## 16. Limites actuelles

- le projet dépend d'un serveur SMTP/IMAP valide pour les e-mails
- le bot Telegram dépend d'un token réel
- certaines tâches de supervision admin pourraient être encore enrichies
- il n'existe pas encore de pipeline CI/CD complet

---

## 17. Sécurité du dépôt

Avant de pousser le projet sur GitHub, vérifier que les fichiers suivants ne sont pas présents dans le commit :

- `.env`
- `.env.docker`
- `frontend/.env`
- tout fichier contenant des clés réelles SMTP, Telegram ou OpenClaw

Le dépôt doit contenir uniquement :

- `.env.example`
- `.env.docker.example`
- `frontend/.env.example`

---

## 18. Contenu demandé pour le rendu

Ce dépôt contient :

- le code source complet
- un README détaillé
- les fichiers Docker
- un rapport de projet
- des scripts de test / démonstration

Le projet est donc :

- présentable
- exécutable
- vérifiable

---

## 19. Auteur

Projet universitaire de fin de semestre : `CampusOps`
