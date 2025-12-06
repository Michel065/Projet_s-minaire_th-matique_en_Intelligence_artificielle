# themes_vers_images/routeur.py
import os
from utils import parse_user_themes
from generated_map import GENERATED_EXAMPLES
from search_by_theme import search_similar_posters


def normalize_theme_key(theme_str: str) -> str:
    toks = [t.strip().lower() for t in theme_str.split(",") if t.strip()]
    toks = sorted(set(toks))
    return ",".join(toks)

def predict_posters_from_themes(theme_str: str, top_k_baseline: int = 5):
    key = normalize_theme_key(theme_str)
    print("[KEY]", normalize_theme_key(theme_str))

    # --- Pré-généré ---
    preg = GENERATED_EXAMPLES.get(key)
    print("[PREG]", key, "->", preg, "exists:", (os.path.exists(preg) if preg else None))
    if preg and os.path.exists(preg):
        return "pregenerated", [preg], "Image IA pré-générée."   # << LISTE !

    # --- Baseline ---
    vec = parse_user_themes(theme_str, binary=True)
    res = search_similar_posters(vec, top_k=top_k_baseline)

    # Accepte (ids, paths) ou [ (id, score, path), ... ] ou [path, ...] ou str
    if isinstance(res, tuple) and len(res) == 2:
        _, paths = res
    else:
        paths = res

    if isinstance(paths, str):              # << string -> liste
        paths = [paths]
    elif paths and isinstance(paths[0], tuple):
        paths = [t[-1] for t in paths]

    return "baseline", paths, "Affiches existantes les plus proches (baseline)."
