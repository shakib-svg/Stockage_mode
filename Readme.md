# TP – Stockage et modes d’accès aux données

## 1. Introduction

L’objectif de ce TP est d’étudier et de comparer différents **modes d’accès au stockage des données**, en particulier :
- le **système de fichiers**,
- le **stockage en mémoire (RAM)** via un cache,
- et l’optimisation des accès grâce à une **politique de cache LRU (Least Recently Used)**.

Chaque type de stockage présente des compromis différents en termes de **latence**, **bande passante**, **persistance**, **coût** et **complexité**.  
Le TP vise également à comprendre comment améliorer les performances via des mécanismes de cache.

---

## 2. Partie 1 – Système de fichiers

### 2.1 Objectif

Mettre en œuvre un accès bas niveau au système de fichiers afin de :
- lire des données depuis un fichier,
- les manipuler en mémoire sous forme de tableau de bytes,
- les réécrire dans un autre fichier,
- vérifier l’intégrité des données.

---

### 2.2 Implémentation

Une classe `FS` a été développée avec les méthodes suivantes :

- `create()` : crée un répertoire de travail `R`
- `list()` : liste le contenu du répertoire
- `read()` : lit un fichier et retourne ses données sous forme de `bytes`
- `write()` : écrit un tableau de bytes dans un fichier
- `delete()` : supprime un fichier

Le programme réalise la séquence suivante :
1. Création du répertoire `R`
2. Lecture d’un fichier image source `I`
3. Stockage de ses données dans un tableau de bytes `T`
4. Écriture de `T` dans un nouveau fichier `F`
5. Lecture de `F` dans un tableau `T2`
6. Vérification de l’intégrité (`T == T2`)
7. Affichage de l’image pour valider la non-corruption

---

### 2.3 Validation

Les tests montrent que :
- la taille des données lues et écrites est identique,
- les tableaux de bytes `T` et `T2` sont strictement égaux,
- l’image affichée après relecture est correcte.

Cela valide le bon fonctionnement du stockage sur système de fichiers.

---

### 2.4 Analyse

- Le système de fichiers offre une **persistance** des données.
- Les accès sont plus lents que la RAM car ils impliquent des opérations d’E/S.
- Le **cache du système d’exploitation (Page Cache)** peut fausser les mesures de performance lors de lectures répétées, car les données peuvent être conservées en RAM par l’OS.

---

## 3. Partie 2 – Stockage en mémoire avec Memcached

### 3.1 Objectif

Utiliser un stockage en mémoire (RAM) via **memcached** afin de :
- stocker des données sous forme clé/valeur,
- accéder rapidement aux données,
- comparer avec le système de fichiers.

---

### 3.2 Outils utilisés

- `memcached` : serveur de cache en mémoire
- `python-memcached` : client Python
- `Pillow (PIL)` : manipulation et affichage d’images

---

### 3.3 Implémentation

Une classe `Mem` a été développée avec les méthodes :
- `connect()` : connexion au serveur memcached
- `create(key, value)` : stockage de bytes associés à une clé
- `read(key)` : lecture des données associées à une clé
- `delete(key)` : suppression d’une clé

Le scénario testé est :
1. Lecture d’un fichier image `I` → tableau `T`
2. Stockage de `T` dans memcached avec une clé `K`
3. Lecture de `K` depuis memcached → tableau `T2`
4. Vérification de l’intégrité (`T == T2`)
5. Affichage de l’image relue

---

### 3.4 Validation

Les résultats montrent que :
- les données sont correctement stockées en mémoire,
- la lecture est immédiate,
- l’intégrité est préservée (`T2 == T`).

---

### 3.5 Analyse

- Memcached permet des accès **beaucoup plus rapides** que le système de fichiers.
- Les données sont **volatiles** (perdues au redémarrage).
- Il n’y a pas de mécanisme de remplacement automatique basé sur l’usage → nécessité d’un cache contrôlé.

---

## 4. Partie 3 – Cache avec politique LRU (Least Recently Used)

### 4.1 Objectif

Implémenter une **politique de cache LRU** afin de :
- garder en mémoire les données les plus récemment utilisées,
- évincer automatiquement les données les moins utilisées,
- maîtriser la taille du cache.

---

### 4.2 Principe du LRU

Le cache est implémenté à l’aide :
- d’une **liste doublement chaînée** :
  - tête = élément le plus récemment utilisé (MRU),
  - queue = élément le moins récemment utilisé (LRU),
- d’un dictionnaire `clé → nœud` pour des accès en O(1).

Règles appliquées :
- `create(K)` : insère ou déplace `K` en tête
- `read(K)` : déplace `K` en tête
- `delete(K)` : supprime `K`
- si la taille dépasse `N`, alors **M clés en fin de liste sont supprimées**
- `create()` retourne la liste des clés évincées

---

### 4.3 Validation du LRU

Des tests ont montré que :
- les lectures déplacent correctement les clés en tête,
- les écritures provoquent les évictions attendues,
- exactement `M` clés sont supprimées lorsque la taille dépasse `N`.

---

## 5. Partie 4 – Intégration Memcached + LRU

### 5.1 Objectif

Combiner memcached avec une politique LRU afin de :
- garantir la cohérence entre les données stockées et l’index du cache,
- contrôler explicitement les évictions.

---

### 5.2 Implémentation

La classe `Mem` a été modifiée pour intégrer un objet `LRU`.

Fonctionnement :
- `Mem.create()` :
  1. stocke la donnée dans memcached,
  2. appelle `LRU.create(key)`,
  3. récupère les clés évincées,
  4. supprime ces clés de memcached.
- `Mem.read()` :
  - si la clé existe, appelle `LRU.read(key)`.
- `Mem.delete()` :
  - supprime la clé dans memcached et dans le LRU.

---

### 5.3 Validation

Les tests montrent que :
- les données sont correctement stockées et relues,
- la politique LRU est respectée,
- les évictions sont synchronisées entre LRU et memcached,
- l’intégrité des données est conservée.

---

## 6. Analyse globale

| Stockage        | Latence | Persistance | Coût | Complexité |
|-----------------|---------|-------------|------|------------|
| Système fichiers | Élevée  | Oui         | Faible | Faible |
| Memcached (RAM) | Très faible | Non     | Élevé | Moyen |
| Mem + LRU       | Très faible | Non     | Élevé | Plus élevé |

- Le **cache améliore fortement les performances** pour des accès répétés.
- La politique **LRU est simple et efficace** pour des workloads classiques.
- Le cache OS peut biaiser les mesures sur le système de fichiers, ce qui nécessite des précautions expérimentales.

---

## 7. Conclusion

Ce TP a permis de :
- comprendre les différences fondamentales entre stockage disque et mémoire,
- implémenter un cache mémoire efficace,
- maîtriser une politique de remplacement LRU,
- intégrer un cache contrôlé avec memcached.

L’utilisation d’un cache avec politique LRU permet d’obtenir un **excellent compromis entre performances et contrôle mémoire**, au prix d’une complexité logicielle accrue.

---

