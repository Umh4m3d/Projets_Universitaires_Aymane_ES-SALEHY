# Rapport du projet CampusOps

## 1. Introduction

CampusOps est un projet de fin de semestre visant à concevoir une plateforme de gestion académique centralisée.  
L'application a été pensée pour répondre à plusieurs besoins concrets dans un contexte scolaire ou universitaire :

- gestion des utilisateurs selon leur rôle
- planification des séances
- gestion des absences
- suivi des paiements
- envoi de notifications
- automatisation de certaines tâches répétitives

L'objectif du projet est à la fois pédagogique et technique : produire une application complète, cohérente, démontrable et suffisamment structurée pour être comprise et exécutée rapidement.

---

## 2. Problématique

Dans beaucoup de contextes académiques, les opérations de gestion sont dispersées :

- planning géré séparément
- absences suivies manuellement
- paiements consultés dans un autre outil
- communication faite par messages ou e-mails non structurés

Cette dispersion provoque :

- perte de temps
- erreurs de suivi
- manque de visibilité
- absence d'automatisation

CampusOps propose une solution unifiée.

---

## 3. Objectifs du projet

Les objectifs principaux étaient :

- centraliser les opérations académiques
- fournir une interface web claire
- mettre en place une API structurée
- gérer plusieurs rôles avec permissions
- automatiser certains flux métier
- offrir un accès rapide par Telegram
- rendre le projet exécutable sur d'autres machines via Docker

---

## 4. Acteurs du système

### Admin

- gère les comptes
- valide ou rejette les demandes de séances
- suit les paiements en retard
- consulte les demandes de modification de profil

### Secrétaire

- gère certaines opérations administratives
- suit les étudiants
- travaille avec les paiements et les absences

### Enseignant

- consulte ses séances
- propose des demandes de nouvelles séances
- marque les absences
- renseigne le progrès pédagogique

### Étudiant

- consulte son planning
- consulte ses absences
- consulte ses paiements
- reçoit des notifications

---

## 5. Choix technologiques

### Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

### Frontend

- React
- Vite
- Material UI

### Base de données

- PostgreSQL

### Services annexes

- Telegram Bot API
- SMTP / IMAP
- Docker / Docker Compose

---

## 6. Architecture générale

L'architecture repose sur un modèle classique full stack :

```text
Frontend React
      |
      v
Backend FastAPI
      |
      v
PostgreSQL
      |
      +--> Bot Telegram
      +--> OpenClaw
      +--> Service e-mail
```

Le frontend dialogue avec l'API FastAPI.  
Le backend applique les règles métier, gère l'authentification, interagit avec la base PostgreSQL et déclenche les notifications ou les workflows automatisés.

---

## 7. Modules principaux

### 7.1 Authentification

Le système utilise des tokens JWT avec gestion du refresh token.  
Les rôles sont contrôlés dans les dépendances backend pour protéger les routes.

### 7.2 Gestion des séances

Le module permet :

- création de séances
- validation/rejet des demandes
- consultation par rôle
- annulation d'une séance

### 7.3 Gestion des absences

Les enseignants ou secrétaires peuvent enregistrer une absence.  
Le système notifie l'étudiant et peut aussi prévenir le parent à partir d'un certain seuil.

### 7.4 Gestion des paiements

Le système suit les paiements mensuels ou d'inscription, leur état, et déclenche des alertes en cas de retard.

### 7.5 Profil utilisateur

Un utilisateur peut demander certains changements de profil.  
Ces changements sont soumis à validation par l'administrateur.

### 7.6 Notifications et e-mails

Le système produit :

- notifications internes
- e-mails de retard de paiement
- e-mails d'absence
- e-mails d'annulation
- e-mails de planning hebdomadaire
- e-mails de réinitialisation de mot de passe

### 7.7 Bot Telegram

Le bot permet une interaction rapide selon le rôle :

- consultation des séances
- consultation des paiements
- consultation des absences
- résumé admin
- accès aux demandes en attente

### 7.8 OpenClaw

OpenClaw orchestre certains traitements automatiques :

- envoi de planning hebdomadaire
- détection des paiements en retard
- traitement des annulations

---

## 8. Travail réalisé

Le projet a évolué vers une application complète comprenant :

- une interface frontend exploitable
- un backend structuré
- des routes métier cohérentes
- des migrations de base de données
- des automatisations e-mail
- un bot Telegram à logique sensible au rôle
- des scripts de démonstration

Un effort particulier a été fait pour améliorer :

- la cohérence des permissions
- la sécurité des endpoints sensibles
- le comportement réel des flux de refresh token
- la fiabilité des flux e-mail

---

## 9. Difficultés rencontrées

Plusieurs difficultés ont été rencontrées pendant le développement :

### 9.1 Gestion des dépendances locales

Le projet mélangeait initialement des dépendances système et applicatives, ce qui compliquait la reproductibilité.

### 9.2 Cohérence des rôles

Certaines routes ou certains usages, notamment via Telegram, n'étaient pas toujours alignés avec les besoins réels de chaque rôle.

### 9.3 Refresh token

Le flux frontend/backend devait être corrigé pour fonctionner réellement avec cookie HTTP-only.

### 9.4 Tests des e-mails

Tester des e-mails réels impose :

- de bonnes variables SMTP/IMAP
- des comptes valides
- des scénarios réalistes

### 9.5 Préparation du rendu

Le projet devait être non seulement fonctionnel, mais aussi présentable et vérifiable rapidement par un enseignant.

---

## 10. Validation et démonstration

Le projet a été validé par :

- tests manuels sur l'interface web
- tests de l'API
- démonstration de flux e-mail réels
- démonstration de demandes de séances en attente
- démonstration de demandes de modification de profil
- démonstration des commandes Telegram selon le rôle

Le dépôt inclut aussi des scripts de test pour reproduire les scénarios.

---

## 11. Dockerisation

Dans la perspective d'un lancement plus simple sur n'importe quelle machine, le projet a été préparé pour Docker avec :

- un conteneur backend
- un conteneur frontend
- un conteneur bot
- un conteneur PostgreSQL
- un `docker-compose.yml`

Cela permet de réduire les problèmes d'installation locale et d'améliorer la portabilité du projet.

---

## 12. Limites actuelles

Certaines limites restent présentes :

- dépendance à des services externes pour l'e-mail et Telegram
- absence d'un pipeline CI/CD complet
- possibilité d'enrichir les statistiques et le dashboard admin
- certains scripts restent orientés démonstration

---

## 13. Perspectives d'amélioration

Améliorations possibles :

- déploiement cloud complet
- tableau de bord admin plus avancé
- gestion de tâches de suivi plus visible
- interface mobile ou responsive encore plus poussée
- statistiques avancées sur absences et paiements
- intégration continue

---

## 14. Conclusion

CampusOps répond à l'objectif principal du projet : proposer une plateforme cohérente, full stack, exécutable et démontrable pour la gestion académique.

Le travail réalisé couvre :

- l'analyse fonctionnelle
- la conception technique
- le développement backend
- le développement frontend
- l'automatisation des flux
- l'intégration d'un bot Telegram
- la préparation du projet pour un rendu GitHub clair et exécutable

Le projet constitue ainsi une base solide, à la fois pédagogique et techniquement exploitable.

