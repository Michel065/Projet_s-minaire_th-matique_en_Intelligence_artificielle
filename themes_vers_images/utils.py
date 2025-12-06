import csv
from typing import List, Tuple
import numpy as np


GENRES: List[str] = [
    "Animation", "Adventure", "Comedy",
    "Action", "Family", "Romance", "Drama",
    "Crime", "Thriller", "Fantasy", "Horror",
    "Biography", "History", "Mystery", "Sci-Fi",
    "War", "Sport", "Music", "Documentary", "Musical",
    "Western", "Short", "Film-Noir", "Talk-Show",
    "News", "Adult", "Reality-TV", "Game-Show"
]

FR_TO_EN_GENRE = {
    "animation": "Animation",
    "aventure": "Adventure",
    "adventure": "Adventure",
    "comedy": "Comedy",
    "comédie": "Comedy",
    "action": "Action",
    "famille": "Family",
    "family": "Family",
    "romance": "Romance",
    "drame": "Drama",
    "drama": "Drama",
    "crime": "Crime",
    "thriller": "Thriller",
    "fantasy": "Fantasy",
    "fantastique": "Fantasy",
    "horreur": "Horror",
    "horror": "Horror",
    "biographie": "Biography",
    "biography": "Biography",
    "histoire": "History",
    "history": "History",
    "mystère": "Mystery",
    "mystery": "Mystery",
    "sci-fi": "Sci-Fi",
    "science-fiction": "Sci-Fi",
    "sf": "Sci-Fi",
    "war": "War",
    "guerre": "War",
    "sport": "Sport",
    "music": "Music",
    "musique": "Music",
    "documentaire": "Documentary",
    "documentary": "Documentary",
    "musical": "Musical",
    "western": "Western",
    "court-métrage": "Short",
    "short": "Short",
    "film-noir": "Film-Noir",
    "talk-show": "Talk-Show",
    "news": "News",
    "adult": "Adult",
    "reality-tv": "Reality-TV",
    "game-show": "Game-Show",
}

def load_theme_vectors(path_csv: str) -> Tuple[List[str], np.ndarray, List[str]]:
    """
    Lit le fichier CSV créé par build_local_dataset.py
    (data/movie_theme_vectors.csv) et retourne :

    - ids         : liste des imdbId (str)
    - X           : matrice NumPy de taille (n_films, n_genres)
    - image_paths : liste des chemins d'affiches (str)
    """
    ids: List[str] = []
    image_paths: List[str] = []
    vectors: List[List[float]] = []

    with open(path_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Vérif minimale : les colonnes de GENRES doivent exister
        missing = [g for g in GENRES if g not in reader.fieldnames]
        if missing:
            raise ValueError(f"Colonnes manquantes dans le CSV : {missing}")

        for row in reader:
            imdb_id = row["imdbId"]
            poster_path = row["poster_path"]

            vec = [float(row[g]) for g in GENRES]

            ids.append(imdb_id)
            image_paths.append(poster_path)
            vectors.append(vec)

    X = np.array(vectors, dtype=np.float32)
    return ids, X, image_paths


def normalize_vectors(X: np.ndarray) -> np.ndarray:
    """
    Normalisation L2 ligne par ligne (chaque film = vecteur de norme 1).
    Si une ligne est nulle, on la laisse telle quelle.
    """
    # norme sur l'axe des features
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    # éviter division par zéro
    norms[norms == 0] = 1.0
    X_norm = X / norms
    return X_norm


def parse_user_themes(input_str: str, binary: bool = True) -> np.ndarray:
    """
    Transforme une chaîne de thèmes utilisateur en vecteur de dimension 28.

    Exemples:
    - "action, horreur"
    - "Action | Comedy | Drama"
    - "drame; romance"

    Si binary=True -> 0/1
    Si binary=False -> on peut mettre 1.0 pour les thèmes cités et 0.0 pour les autres
                       (pareil, mais prêt pour du pondéré plus tard).
    """
    # vecteur initial à 0
    vec = np.zeros(len(GENRES), dtype=np.float32)

    if not input_str:
        return vec


    raw_parts = re_split_themes(input_str)

    for raw in raw_parts:
        key = raw.strip().lower()
        if not key:
            continue

        
        if key in FR_TO_EN_GENRE:
            canonical = FR_TO_EN_GENRE[key]
        else:
           
            canonical = None
            for g in GENRES:
                if key == g.lower():
                    canonical = g
                    break

        if canonical and canonical in GENRES:
            idx = GENRES.index(canonical)
            vec[idx] = 1.0 if binary else 1.0  

    return vec


def re_split_themes(input_str: str) -> List[str]:
    """
    Petit helper pour découper une chaîne de thèmes sur plusieurs séparateurs:
    ',', ';', '|'
    """
    import re

    tmp = re.sub(r"[;|]", ",", input_str)
    parts = [p for p in tmp.split(",")]
    return parts
