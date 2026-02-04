#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, List
import memcache  


# LRU (liste doublement chaînée)
@dataclass
class _Node:
    key: str
    prev: Optional["_Node"] = None
    next: Optional["_Node"] = None


class LRU:
    """
    Conformité TP :
    - head = plus récemment utilisé (MRU)
    - tail = moins récemment utilisé (LRU)
    - create(k): met k en head ; si taille > N => supprime EXACTEMENT M derniers
      et retourne la liste des clés évincées
    - read(k): si présent => move-to-head
    - delete(k): supprime de la liste
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
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        node.prev = None
        node.next = None

    def _add_to_head(self, node: _Node) -> None:
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node

    def _move_to_head(self, node: _Node) -> None:
        if node is self.head:
            return
        self._remove_node(node)
        self._add_to_head(node)

    def create(self, key: str) -> List[str]:
        evicted: List[str] = []

        if key in self.map:
            self._move_to_head(self.map[key])
            return evicted

        node = _Node(key=key)
        self.map[key] = node
        self._add_to_head(node)

        # Conformité TP : si dépasse N => supprime EXACTEMENT M dernières clés
        if len(self.map) > self.N:
            for _ in range(self.M):
                if self.tail is None:
                    break
                victim = self.tail
                self._remove_node(victim)
                del self.map[victim.key]
                evicted.append(victim.key)

        return evicted

    def read(self, key: str) -> bool:
        node = self.map.get(key)
        if node is None:
            return False
        self._move_to_head(node)
        return True

    def delete(self, key: str) -> bool:
        node = self.map.get(key)
        if node is None:
            return False
        self._remove_node(node)
        del self.map[key]
        return True

    def keys_mru_to_lru(self) -> List[str]:
        out: List[str] = []
        cur = self.head
        while cur:
            out.append(cur.key)
            cur = cur.next
        return out



# Mem + LRU

class Mem:
    """
    Memcache + LRU.
    - create(key, value): set memcached + LRU.create(key) + delete(evicted_keys)
      retourne la liste des clés évincées
    - read(key): get memcached + si hit => LRU.read(key)
    - delete(key): delete memcached + LRU.delete(key)
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 11211, N: int = 100, M: int = 10):
        self.server = f"{host}:{port}"
        self.client: Optional[memcache.Client] = None
        self.lru = LRU(N=N, M=M)

    def connect(self) -> None:
        self.client = memcache.Client([self.server], debug=0)
        # ping simple
        self.client.set("__ping__", b"1", time=5)
        if self.client.get("__ping__") != b"1":
            raise RuntimeError("Impossible de communiquer avec memcached")

    def create(self, key: str, value: bytes, expire: int = 0) -> List[str]:
        if self.client is None:
            raise RuntimeError("Mem non connecté: appelle connect()")

        # 1) écrire dans memcached
        ok = self.client.set(key, value, time=expire)
        if not ok:
            raise RuntimeError(f"memcached set() a échoué pour key={key}")

        # 2) mise à jour LRU + récupération évictions
        evicted_keys = self.lru.create(key)

        # 3) supprimer les clés évincées côté memcached (cohérence cache)
        for k in evicted_keys:
            self.client.delete(k)

        return evicted_keys

    def read(self, key: str) -> Optional[bytes]:
        if self.client is None:
            raise RuntimeError("Mem non connecté: appelle connect()")

        val = self.client.get(key)  # bytes ou None
        if val is not None:
            self.lru.read(key)  # refresh LRU seulement si hit
        return val

    def delete(self, key: str) -> bool:
        if self.client is None:
            raise RuntimeError("Mem non connecté: appelle connect()")

        self.client.delete(key)
        return self.lru.delete(key)

def show_image_from_bytes(image_data: bytes) -> None:
    from PIL import Image
    import io
    import matplotlib.pyplot as plt

    img = Image.open(io.BytesIO(image_data))
    img.load()
    plt.figure()
    plt.imshow(img)
    plt.axis("off")
    plt.show()



def main() -> None:
    I = "./I.png"
    K = "img:I"

    mem = Mem(N=3, M=2)  # petit N/M pour voir l’éviction
    mem.connect()
    print("[OK] Connecté à memcached")

    # lire fichier I -> T
    with open(I, "rb") as f:
        T = f.read()
    print("[OK] Lecture fichier I:", len(T), "bytes")
    show_image_from_bytes(T)

    # create K -> T
    evicted = mem.create(K, T, expire=60)
    print("[OK] create key=", K, "evicted=", evicted, "LRU=", mem.lru.keys_mru_to_lru())

    # read K -> T2
    T2 = mem.read(K)
    print("[OK] read key=", K, "hit=", T2 is not None, "LRU=", mem.lru.keys_mru_to_lru())
    if T2 is not None:
        show_image_from_bytes(T2)
        print("[CHECK] Identique ?", "OUI" if T2 == T else "NON")

if __name__ == "__main__":
    main()
"""
(TF) shakib@shakibhp:~/Documents/GitHub/Stockage_mode$ python3 mem_LRU.py
[OK] Connecté à memcached
[OK] Lecture fichier I: 83235 bytes
[OK] create key= img:I evicted= [] LRU= ['img:I']
[OK] read key= img:I hit= True LRU= ['img:I']
[CHECK] Identique ? OUI
"""