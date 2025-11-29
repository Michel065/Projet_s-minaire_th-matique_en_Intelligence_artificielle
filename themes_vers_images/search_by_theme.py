import os
import argparse
import numpy as np
from typing import List, Tuple

from utils import GENRES, parse_user_themes

INDEX_PATH = "data/theme_vectors_index.npz"


def load_index(index_path: str = INDEX_PATH) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Charge l'index pré-calculé :
    - ids         : array de str (imdbId)
    - X_norm      : matrice (n_films, n_genres) normalisée
    - image_paths : array de str (chemins d'affiches)
    """
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index non trouvé : {index_path}. Lance d'abord build_index.py.")

    data = np.load(index_path, allow_pickle=True)
    ids = data["ids"]
    X_norm = data["X_norm"]
    image_paths = data["image_paths"]
    return ids, X_norm, image_paths


def search_similar_posters(query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, str]]:
    """
    Cherche les affiches les plus similaires à un vecteur de thèmes donné.

    Retourne une liste de tuples (imdbId, score_similarité, image_path)
    triée par score décroissant.
    """
    ids, X_norm, image_paths = load_index()

    # Normaliser le vecteur de requête
    q = query_vector.astype(np.float32)
    norm = np.linalg.norm(q)
    if norm == 0:
        # vecteur nul -> on renvoie rien
        return []
    q = q / norm

    # Similarité cosinus : X_norm · q
    scores = X_norm @ q  # produit matriciel, shape (n_films,)

    # top_k indices
    top_k = min(top_k, len(scores))
    top_indices = np.argsort(scores)[::-1][:top_k]

    results: List[Tuple[str, float, str]] = []
    for idx in top_indices:
        imdb_id = str(ids[idx])
        score = float(scores[idx])
        img_path = str(image_paths[idx])
        results.append((imdb_id, score, img_path))

    return results


def main_cli():
    parser = argparse.ArgumentParser(description="Recherche d'affiches par thèmes.")
    parser.add_argument(
        "--themes",
        type=str,
        required=True,
        help='Liste de thèmes, ex: "action, horreur, drame"',
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=5,
        help="Nombre de résultats à retourner (par défaut: 5)",
    )
    args = parser.parse_args()

    # Construire le vecteur de requête à partir de la chaîne utilisateur
    query_vec = parse_user_themes(args.themes, binary=True)

    print(f"Thèmes demandés : {args.themes}")
    print(f"Vecteur non nul sur : {[g for g, v in zip(GENRES, query_vec) if v > 0]}")

    results = search_similar_posters(query_vec, top_k=args.top_k)

    if not results:
        print("Aucun résultat (vecteur de requête nul ?)")
        return

    print("\nTop résultats :")
    for imdb_id, score, img_path in results:
        print(f"- imdbId={imdb_id:>8} | score={score:.3f} | poster={img_path}")


if __name__ == "__main__":
    main_cli()
