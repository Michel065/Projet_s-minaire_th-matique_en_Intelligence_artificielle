from typing import List, Dict, Literal
import os

import numpy as np

from utils import GENRES, parse_user_themes
from generate_baseline import predict_posters_from_themes
from clip_classifier import predict_themes_from_image


ModeType = Literal["baseline"]  # plus tard tu pourras ajouter: "diffusion"


def generate_from_themes(
    theme_str: str,
    mode: ModeType = "baseline",
    top_k: int = 5,
) -> Dict:
    """
    Point d'entrée 'propre' pour la partie thèmes -> images.

    - theme_str : chaîne saisie par l'utilisateur ("action, horreur, drame")
    - mode      : "baseline" pour l'instant (recherche d'affiches existantes)
                  plus tard, tu pourras ajouter "diffusion"
    - top_k     : nombre de résultats à retourner

    Retourne un dictionnaire prêt pour une API / interface.
    """
    theme_str = theme_str.strip()
    if not theme_str:
        raise ValueError("La chaîne de thèmes est vide.")

    # On garde aussi le vecteur au cas où tu en aies besoin
    theme_vector = parse_user_themes(theme_str, binary=True)

    if mode == "baseline":
        poster_paths: List[str] = predict_posters_from_themes(theme_str, top_k=top_k)
    else:
        raise ValueError(f"Mode inconnu: {mode}")

    # Normaliser les chemins (utile pour une interface web plus tard)
    poster_paths = [p.replace("\\", "/") for p in poster_paths]

    return {
        "mode": mode,
        "input_themes": theme_str,
        "theme_vector": theme_vector.tolist(),
        "posters": poster_paths,
    }


def analyze_poster(
    image_path: str,
    top_k: int = 5,
) -> Dict:
    """
    Point d'entrée 'propre' pour la partie image -> thèmes (via CLIP).

    - image_path : chemin vers une affiche
    - top_k      : combien de thèmes les plus probables retourner

    Retourne un dict avec:
    - 'image_path'
    - 'raw_scores' : dict {genre: score}
    - 'top_k'      : liste triée des meilleurs thèmes
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    scores = predict_themes_from_image(image_path)  # shape (28,)
    scores = np.asarray(scores, dtype=np.float32)

    # Construire un dict {genre: score}
    raw_scores = {genre: float(score) for genre, score in zip(GENRES, scores)}

    # Top-k genres les plus probables
    idx_sorted = np.argsort(scores)[::-1][:top_k]
    top_k_list = [
        {
            "genre": GENRES[i],
            "score": float(scores[i]),
        }
        for i in idx_sorted
    ]

    return {
        "image_path": image_path.replace("\\", "/"),
        "raw_scores": raw_scores,
        "top_k": top_k_list,
    }
