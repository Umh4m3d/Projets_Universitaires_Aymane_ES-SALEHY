# Projet : Université Connectée – Réseau Étendu

## Description
Ce projet consiste à concevoir et mettre en œuvre une **architecture réseau hiérarchisée et évolutive** pour un environnement universitaire multi-bâtiments.  
L’objectif est d’assurer une **communication sécurisée et fiable** entre les différents étages et bâtiments tout en optimisant la gestion des VLANs et du routage.

---

## Objectifs
- Segmenter le réseau avec des VLANs pour isoler différents groupes d’utilisateurs (Professeurs, Étudiants, Visiteurs, Administrateurs, Direction, Services Financiers).  
- Implémenter le **routage inter-VLAN** via un routeur central.  
- Utiliser **OSPF** pour le routage dynamique et la convergence rapide.  
- Faciliter l’**extensibilité** et la gestion du réseau à travers plusieurs bâtiments.

---

## Topologie Réseau
L’université comprend :  
- **Bâtiments Académiques** : A, B, C, D (4 étages chacun, 3 VLAN par étage : Professeurs, Étudiants, Visiteurs)  
- **Bâtiment Administratif** : 1 étage, 3 VLAN (Administrateurs, Direction, Services Financiers)  
- **Routeur Central** : Relie tous les bâtiments et permet la communication inter-bâtiments  

**Hiérarchie OSPF (areas)** :
Area 0 (Backbone)
├─ Area 1 : Bâtiment A
├─ Area 2 : Bâtiment B
├─ Area 3 : Bâtiment C
├─ Area 4 : Bâtiment D
└─ Area 5 : Bâtiment Administratif


---

## Plan d’Adressage IP

### Exemple Bâtiment A – VLANs par étage
| VLAN | Réseau         | Masque        | CIDR | Gateway       | Plage IP     |
|------|----------------|---------------|------|---------------|-------------|
| 10   | 192.168.1.0    | 255.255.255.240 | /28  | 192.168.1.2   | .1–.14      |
| 20   | 192.168.1.16   | 255.255.255.240 | /28  | 192.168.1.18  | .17–.30     |
| 30   | 192.168.1.32   | 255.255.255.240 | /28  | 192.168.1.34  | .33–.46     |

**Gateways successives par étage (VLAN10, VLAN20, VLAN30)**

| Étage | VLAN10       | VLAN20       | VLAN30       |
|-------|-------------|-------------|-------------|
| 1     | 192.168.1.14 | 192.168.1.30 | 192.168.1.46 |
| 2     | 192.168.1.62 | 192.168.1.78 | 192.168.1.94 |
| 3     | 192.168.1.110 | 192.168.1.126 | 192.168.1.142 |
| 4     | 192.168.1.158 | 192.168.1.174 | 192.168.1.190 |

---

## Configuration Réseau

### VLANs et Sous-Interfaces
- Chaque routeur gère des sous-interfaces pour chaque VLAN avec encapsulation 802.1Q.  
- Les trunks entre switches transportent tous les VLANs actifs.

### Routage Dynamique OSPF
- Un processus OSPF par bâtiment pour isoler les domaines de routage.  
- Redistribution des routes entre les différents processus sur le routeur central.  

## Résultats

- Les VLANs communiquent correctement à l’intérieur et entre eux.
- OSPF est opérationnel avec tous les voisins en état FULL.
- Le routage inter-bâtiments fonctionne parfaitement.
- Les trunks et les VLANs sont actifs et correctement configurés.

## Conclusion

- Le projet a permis de concevoir un réseau robuste, hiérarchisé et évolutif pour un environnement multi-bâtiments.
- La segmentation VLAN assure une isolation logique, et OSPF garantit un routage dynamique fiable.
- L’architecture est prête pour des extensions futures (nouveaux bâtiments, sécurité avancée, services réseau supplémentaires).

