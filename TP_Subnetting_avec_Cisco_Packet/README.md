# TP Subnetting & VLSM – Architecture Cisco Packet Tracer

Ce dossier contient le travail pratique réalisé dans le cadre du module **Réseaux Informatiques**, portant sur l’**adressage IP**, le **subnetting (y compris VLSM)** et la **simulation d’une architecture réseau dans Cisco Packet Tracer**.  
Le TP inclut également la **configuration d’un serveur DHCP sous Ubuntu** et la vérification de la connectivité réseau avec des commandes ping.

---

## Objectifs pédagogiques

- Comprendre et appliquer l’adressage IPv4 et le subnetting  
- Calculer les sous-réseaux, le nombre d’hôtes, les adresses de broadcast et passerelles  
- Utiliser VLSM pour optimiser l’utilisation des adresses IP  
- Configurer une architecture réseau dans Cisco Packet Tracer   
- Tester la connectivité entre sous-réseaux avec des pings  
- Documenter la configuration et les résultats

---

## Contenu du TP

### 1️⃣ Calcul des sous-réseaux et VLSM

**Description :**  
- Division d’un réseau principal en plusieurs sous-réseaux adaptés au nombre d’hôtes requis  
- Calcul des éléments essentiels pour chaque sous-réseau :  
  - Adresse réseau  
  - Masque de sous-réseau (Subnet Mask)  
  - Plage d’adresses utilisables  
  - Adresse de broadcast  
  - Adresse de la passerelle (Gateway)  

**Objectifs spécifiques :**  
- Maîtriser le calcul des sous-réseaux et l’utilisation du VLSM  
- Optimiser l’utilisation des adresses IP  
- Préparer une base logique pour la configuration physique dans Cisco Packet Tracer

**Fichiers associés :**  
- `TP3_subnetting.pdf` : rapport avec les calculs et explications  

---

### 2️⃣ Architecture réseau dans Cisco Packet Tracer

**Description :**  
- Implémentation de l’architecture réseau conçue dans le TP précédent  
- Utilisation de routeurs, switches et PCs  
- Configuration des adresses IP et VLAN si nécessaire  
- Test de connectivité entre sous-réseaux

**Objectifs spécifiques :**  
- Configurer correctement les interfaces des équipements Cisco  
- Vérifier la communication réseau entre tous les sous-réseaux avec `ping`  
- Identifier et corriger d’éventuelles erreurs de configuration

**Fichiers associés :**  
- `AymaneTP3.pkt` : fichier Cisco Packet Tracer  
