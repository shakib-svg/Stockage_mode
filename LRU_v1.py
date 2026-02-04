from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class _Node:
    key: str
    prev: Optional["_Node"] = None
    next: Optional["_Node"] = None


class LRU:
    """
    LRU basé sur:
      - une liste doublement chaînée (head = MRU, tail = LRU)
      - un dictionnaire key -> node pour O(1)

    Paramètres:
      - N: capacité max en nombre de clés
      - M: nombre de clés évincées quand on dépasse N (on supprime M dernières)

    Méthodes:
      - create(key) -> List[str] : insère/move-to-head et retourne les clés supprimées
      - read(key) -> bool : True si hit (et move-to-head), False sinon
      - delete(key) -> bool : True si supprimée, False sinon
    """

    def __init__(self, N: int, M: int):
        if N <= 0:
            raise ValueError("N doit être > 0")
        if M <= 0:
            raise ValueError("M doit être > 0")
        self.N = N
        self.M = M

        self.head: Optional[_Node] = None
        self.tail: Optional[_Node] = None
        self.map: Dict[str, _Node] = {}

    def _remove_node(self, node: _Node) -> None:
        """Retire node de la liste chaînée (sans toucher au dict)."""
        if node.prev:
            node.prev.next = node.next
        else:
            # node est head
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            # node est tail
            self.tail = node.prev

        node.prev = None
        node.next = None

    def _add_to_head(self, node: _Node) -> None:
        """Ajoute node en tête."""
        node.prev = None
        node.next = self.head

        if self.head:
            self.head.prev = node
        self.head = node

        if self.tail is None:
            # première insertion
            self.tail = node

    def _move_to_head(self, node: _Node) -> None:
        """Déplace un node existant en tête."""
        if node is self.head:
            return
        self._remove_node(node)
        self._add_to_head(node)
    """
    Conformité TP:
    - Si taille > N, alors on supprime EXACTEMENT M clés depuis la tail,
      (sauf si la liste devient vide).
    """
    def _evict_if_needed(self) -> List[str]:

        evicted: List[str] = []
        if len(self.map) <= self.N:
            return evicted

        for _ in range(self.M):
            if self.tail is None:
                break
            victim = self.tail
            self._remove_node(victim)
            del self.map[victim.key]
            evicted.append(victim.key)

        return evicted


    def create(self, key: str) -> List[str]:
        """
        Ecriture:
          - si key existe: move-to-head
          - sinon: insert head
          - si dépasse N: évince M dernières
        Retourne les clés évincées.
        """
        if key in self.map:
            self._move_to_head(self.map[key])
            return []  # pas d'éviction due à "réécriture"
        node = _Node(key=key)
        self.map[key] = node
        self._add_to_head(node)
        return self._evict_if_needed()

    def read(self, key: str) -> bool:
        """
        Lecture:
          - si key existe: move-to-head et retourne True
          - sinon: False
        """
        node = self.map.get(key)
        if node is None:
            return False
        self._move_to_head(node)
        return True

    def delete(self, key: str) -> bool:
        """
        Suppression:
          - si key existe: supprime de la liste + dict, retourne True
          - sinon: False
        """
        node = self.map.get(key)
        if node is None:
            return False
        self._remove_node(node)
        del self.map[key]
        return True

    # Optionnel
    def keys_mru_to_lru(self) -> List[str]:
        out: List[str] = []
        cur = self.head
        while cur:
            out.append(cur.key)
            cur = cur.next
        return out
if __name__ == "__main__":
    lru = LRU(N=3, M=2)

    print("create A evicted:", lru.create("A"), lru.keys_mru_to_lru())  # A
    print("create B evicted:", lru.create("B"), lru.keys_mru_to_lru())  # B A
    print("create C evicted:", lru.create("C"), lru.keys_mru_to_lru())  # C B A

    # read A => A devient head
    print("read A:", lru.read("A"), lru.keys_mru_to_lru())             # A C B

    # create D => dépasse N (4>3) => évince M=2 dernières => supprime B puis C
    print("create D evicted:", lru.create("D"), lru.keys_mru_to_lru()) # D A

    # delete A
    print("delete A:", lru.delete("A"), lru.keys_mru_to_lru())         # D



"""
(TF) shakib@shakibhp:~/Documents/GitHub/Stockage_mode$ python3 LRU.py 
create A evicted: [] ['A']
create B evicted: [] ['B', 'A']
create C evicted: [] ['C', 'B', 'A']
read A: True ['A', 'C', 'B']
create D evicted: ['B', 'C'] ['D', 'A']
delete A: True ['D']
"""