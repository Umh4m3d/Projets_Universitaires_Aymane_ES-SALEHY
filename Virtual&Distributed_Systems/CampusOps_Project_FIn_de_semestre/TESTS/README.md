# Tests et démonstrations

Ce dossier regroupe des scripts utiles pour démontrer rapidement le projet.

## Script disponible

### `campusops_mail_demo.py`

Ce script exécute plusieurs scénarios de démonstration sur l'API en cours d'exécution :

- envoi du planning hebdomadaire enseignant
- paiement en retard
- annulation de séance
- réinitialisation de mot de passe
- e-mails d'absence
- alerte parent

## Exécution

```bash
python3 TESTS/campusops_mail_demo.py
```

## Préconditions

- backend démarré
- base de données disponible
- variables `MAIL_*` correctement configurées
- `OPENCLAW_KEY` présent
- comptes de démonstration créés

## Vérifications conseillées

- réception des e-mails sur les adresses Gmail de démonstration
- présence des notifications dans l'application
- cohérence des paiements et absences créés

