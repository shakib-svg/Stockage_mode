#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
from PIL import Image
import io


class FS:
    """Backend simple 'système de fichiers' pour le TP."""
    def __init__(self, root_dir: str | Path):
        self.root = Path(root_dir)

    def create(self) -> None:
        """Crée le répertoire root (R) s'il n'existe pas."""
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self) -> List[str]:
        """Liste le contenu du répertoire root."""
        if not self.root.exists():
            return []
        return sorted([p.name for p in self.root.iterdir()])

    def read(self, filepath: str | Path) -> bytes:
        """Lit un fichier (chemin absolu ou relatif à root) et retourne ses bytes."""
        p = Path(filepath)
        if not p.is_absolute():
            p = self.root / p
        with open(p, "rb") as f:
            return f.read()

    def write(self, filepath: str | Path, data: bytes) -> None:
        """Écrit des bytes dans un fichier (chemin absolu ou relatif à root)."""
        p = Path(filepath)
        if not p.is_absolute():
            p = self.root / p
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)

    def delete(self, filepath: str | Path) -> None:
        """Supprime un fichier (chemin absolu ou relatif à root) si présent."""
        p = Path(filepath)
        if not p.is_absolute():
            p = self.root / p
        if p.exists():
            p.unlink()


def show_image_from_bytes(data: bytes, title: str) -> None:
    img = Image.open(io.BytesIO(data))
    img.load()
    plt.figure()
    plt.imshow(img)
    plt.title(title)
    plt.axis("off")
    plt.show()

def main() -> None:
    R = "./R"               
    I = "./I.png"          
    F = "F_copy.png"          
    fs = FS(R)
    # 1) Crée un répertoire R
    fs.create()
    print(f"[OK] Répertoire créé/existant: {Path(R).resolve()}")

    # 2) Liste le contenu du répertoire
    print("[LIST] Contenu de R:", fs.list())

    # 3) Lit les données d’un fichier I -> T et l’affiche comme image
    with open(I, "rb") as f:
        T = f.read()
    print(f"[OK] Lecture de I -> T : {len(T)} bytes depuis {Path(I).resolve()}")
    show_image_from_bytes(T, title="Image I (T)")

    # 4) Écrit des données depuis T source dans un fichier F (dans R)
    fs.write(F, T)
    print(f"[OK] Écriture de T -> F : {len(T)} bytes vers {(Path(R)/F).resolve()}")

    # 5) Lit les données du fichier F -> T2 et l’affiche comme image
    T2 = fs.read(F)
    print(f"[OK] Lecture de F -> T2 : {len(T2)} bytes")
    show_image_from_bytes(T2, title="Image F (T2)")

    # (optionnel) Vérification stricte bytes == bytes
    print("[CHECK] Données identiques ?" , "OUI" if T2 == T else "NON")

    # 6) Reliste le contenu de R pour voir F
    print("[LIST] Contenu de R:", fs.list())

if __name__ == "__main__":
    main()



"""
[OK] Répertoire créé/existant: /home/shakib/Documents/GitHub/Stockage_mode/R
[LIST] Contenu de R: []
[OK] Lecture de I -> T : 83235 bytes depuis /home/shakib/Documents/GitHub/Stockage_mode/I.png
[OK] Écriture de T -> F : 83235 bytes vers /home/shakib/Documents/GitHub/Stockage_mode/R/F_copy.png
[OK] Lecture de F -> T2 : 83235 bytes
[CHECK] Données identiques ? OUI
[LIST] Contenu de R: ['F_copy.png']
"""