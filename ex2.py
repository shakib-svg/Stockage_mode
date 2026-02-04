#!/usr/bin/env python3
from __future__ import annotations

import io
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image
from pymemcache.client.base import Client


class Mem:
    """Wrapper simple autour de memcached via pymemcache."""
    def __init__(self, host: str = "127.0.0.1", port: int = 11211):
        self.host = host
        self.port = port
        self.client: Client | None = None

    def create(self) -> None:
        """Crée/ouvre une connexion client memcached."""
        self.client = Client((self.host, self.port), connect_timeout=1, timeout=1)
        ok = self.client.set("__ping__", b"1", expire=5)
        if not ok:
            raise RuntimeError("Connexion memcached: set() a échoué (serveur down ?)")
        _ = self.client.get("__ping__")  # doit renvoyer b"1" si ok

    def read(self, key: str) -> bytes | None:
        """Lit la valeur associée à key (bytes), ou None si absent."""
        if self.client is None:
            raise RuntimeError("Mem client non initialisé: appelle create() avant.")
        val = self.client.get(key)  # renvoie bytes ou None :contentReference[oaicite:4]{index=4}
        return val

    def write(self, key: str, value: bytes, expire: int = 0) -> None:
        """Ecrit key -> bytes dans memcached."""
        if self.client is None:
            raise RuntimeError("Mem client non initialisé: appelle create() avant.")
        ok = self.client.set(key, value, expire=expire)  # set accepte bytes :contentReference[oaicite:5]{index=5}
        if not ok:
            raise RuntimeError(f"memcached set() a échoué pour key={key}")

    def delete(self, key: str) -> None:
        """Supprime la clé."""
        if self.client is None:
            raise RuntimeError("Mem client non initialisé: appelle create() avant.")
        self.client.delete(key)  # delete existe :contentReference[oaicite:6]{index=6}

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None


def show_image_from_bytes(data: bytes, title: str) -> None:
    img = Image.open(io.BytesIO(data))
    img.load()
    plt.figure()
    plt.imshow(img)
    plt.title(title)
    plt.axis("off")
    plt.show()


def main() -> None:
    I = "./I.png"         
    K = "img:I"           
    HOST, PORT = "127.0.0.1", 11211

    # 1) Lire I -> T (bytes) et afficher
    I_path = Path(I)
    if not I_path.exists():
        raise FileNotFoundError(f"Fichier source introuvable: {I_path.resolve()}")

    T = I_path.read_bytes()
    print(f"[OK] Lecture I -> T : {len(T)} bytes depuis {I_path.resolve()}")
    show_image_from_bytes(T, "Image I (T)")

    # 2) Stocker dans memcached: K -> T
    mem = Mem(HOST, PORT)
    mem.create()
    print(f"[OK] Connexion memcached sur {HOST}:{PORT}")

    mem.write(K, T, expire=60)  # expire=60s (tu peux mettre 0 pour "pas d'expiration")
    print(f"[OK] Stockage memcached: key={K} size={len(T)} bytes")

    # 3) Lire K -> T2 et afficher
    T2 = mem.read(K)
    if T2 is None:
        raise RuntimeError(f"[ERREUR] Clé absente: {K}")

    print(f"[OK] Lecture memcached: key={K} size={len(T2)} bytes")
    show_image_from_bytes(T2, "Image depuis memcached (T2)")

    # 4) Vérif intégrité
    print("[CHECK] Données identiques ?", "OUI" if T2 == T else "NON")
    mem.close()
if __name__ == "__main__":
    main()

"""
● memcached.service - memcached daemon
     Loaded: loaded (/usr/lib/systemd/system/memcached.service; enabled; preset: enabled)
     Active: active (running) since Wed 2026-02-04 13:19:58 CET; 1h 46min ago
       Docs: man:memcached(1)
   Main PID: 1960 (memcached)
      Tasks: 10 (limit: 28425)
     Memory: 2.5M (peak: 3.2M)
        CPU: 1.079s
     CGroup: /system.slice/memcached.service
             └─1960 /usr/bin/memcached -m 64 -p 11211 -u memcache -l 127.0.0.1 -l ::1 -P /var/run/me>

Feb 04 13:19:58 shakibhp systemd[1]: Started memcached.service - memcached daemon.
"""
""" python3 ex2.py
[OK] Lecture I -> T : 83235 bytes depuis /home/shakib/Documents/GitHub/Stockage_mode/I.png
[OK] Connexion memcached sur 127.0.0.1:11211
[OK] Stockage memcached: key=img:I size=83235 bytes
[OK] Lecture memcached: key=img:I size=83235 bytes
[CHECK] Données identiques ? OUI
"""