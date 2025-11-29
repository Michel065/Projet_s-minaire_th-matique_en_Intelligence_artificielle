import os
import numpy as np
from utils import load_theme_vectors, normalize_vectors

INDEX_PATH = "data/theme_vectors_index.npz"
CSV_PATH = "data/movie_theme_vectors.csv"


def build_index(
    csv_path: str = CSV_PATH,
    index_path: str = INDEX_PATH,
):
    """
    Construit un index simple pour la recherche par similarité :
    - charge les vecteurs de thèmes depuis le CSV
    - normalise les vecteurs (L2)
    - sauvegarde ids, X_norm, image_paths dans un fichier .npz
    """
    print(f"[build_index] Chargement des vecteurs depuis {csv_path} ...")
    ids, X, image_paths = load_theme_vectors(csv_path)
    print(f"[build_index] {len(ids)} films chargés, matrice {X.shape}")

    print("[build_index] Normalisation des vecteurs ...")
    X_norm = normalize_vectors(X)

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    print(f"[build_index] Sauvegarde de l'index vers {index_path} ...")
    np.savez_compressed(
        index_path,
        ids=np.array(ids),
        X_norm=X_norm,
        image_paths=np.array(image_paths),
    )

    print("[build_index] Terminé.")


if __name__ == "__main__":
    build_index()
