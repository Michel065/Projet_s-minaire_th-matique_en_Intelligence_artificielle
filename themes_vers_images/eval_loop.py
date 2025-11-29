import os
import argparse
from typing import List, Tuple

import numpy as np

from utils import GENRES, load_theme_vectors, normalize_vectors
from generate_baseline import predict_posters_from_themes


# ==========================
# 1. À COMPLÉTER AVEC LE MODÈLE DU BINÔME
# ==========================

from clip_classifier import predict_themes_from_image



# ==========================
# 2. MÉTRIQUES
# ==========================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def topk_overlap(a: np.ndarray, b: np.ndarray, k: int = 3) -> float:
    """
    Calcule la proportion de thèmes communs dans le top-k de chaque vecteur.
    Retourne un score entre 0 et 1.
    """
    k = min(k, len(a), len(b))

    # indices triés par score décroissant
    top_a = np.argsort(a)[::-1][:k]
    top_b = np.argsort(b)[::-1][:k]

    set_a = set(top_a.tolist())
    set_b = set(top_b.tolist())
    inter = set_a & set_b

    return len(inter) / float(k)


# ==========================
# 3. BOUCLE D'ÉVALUATION
# ==========================

def vector_to_theme_string(vec: np.ndarray, max_themes: int = 4, threshold: float = 0.5) -> str:
    """
    Convertit un vecteur de thèmes en chaîne lisible, ex :
    "Action, Horror, Drama"

    - On prend d'abord tous les thèmes dont la valeur >= threshold.
    - Si ça fait trop de thèmes, on garde les max_themes plus forts.
    - Si rien ne passe le seuil, on prend simplement les max_themes meilleurs.
    """
    vec = np.asarray(vec)
    # indices triés par score décroissant
    sorted_idx = np.argsort(vec)[::-1]

    # thèmes au-dessus du seuil
    above = [i for i in sorted_idx if vec[i] >= threshold]

    if len(above) == 0:
        # si aucun thème ne dépasse le seuil, on prend les max_themes premiers
        top_idx = sorted_idx[:max_themes]
    else:
        # on limite à max_themes parmi ceux au-dessus du seuil
        top_idx = above[:max_themes]

    labels = [GENRES[i] for i in top_idx]
    return ", ".join(labels)


def eval_loop(
    csv_path: str = "data/movie_theme_vectors.csv",
    num_samples: int = 50,
    seed: int = 0,
    use_normalized: bool = False,
    output_path: str | None = "data/eval_results_baseline.csv",
):
    """
    Boucle d'évaluation :
    - sélectionne num_samples films aléatoires depuis le CSV
    - part de leur vecteur de thèmes (y_true)
    - génère une affiche existante via ta baseline (thèmes -> posters)
    - envoie cette affiche au modèle de ton binôme (image -> thèmes)
    - compare y_true et y_pred avec cosinus + overlap top-k
    """
    print(f"[eval_loop] Chargement des vecteurs depuis {csv_path} ...")
    ids, X, image_paths = load_theme_vectors(csv_path)
    X = X.astype(np.float32)

    if use_normalized:
        print("[eval_loop] Normalisation L2 des vecteurs ...")
        X_eval = normalize_vectors(X)
    else:
        X_eval = X

    n = len(ids)
    print(f"[eval_loop] {n} films disponibles.")

    rng = np.random.default_rng(seed)
    indices = rng.choice(n, size=min(num_samples, n), replace=False)

    all_results: List[Tuple[str, float, float, float]] = []

    import csv as _csv
    if output_path is not None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        f_out = open(output_path, "w", newline="", encoding="utf-8")
        writer = _csv.writer(f_out)
        writer.writerow([
            "imdbId",
            "cosine_similarity",
            "top3_overlap",
            "top5_overlap",
        ])
    else:
        writer = None
        f_out = None

    try:
        for idx in indices:
            imdb_id = ids[idx]
            y_true = X_eval[idx]

            # 1) vecteur -> chaîne de thèmes
            theme_str = vector_to_theme_string(y_true, max_themes=4, threshold=0.5)

            # 2) chaîne de thèmes -> affiche existante (baseline)
            posters = predict_posters_from_themes(theme_str, top_k=1)
            if not posters:
                print(f"[eval_loop] Aucun poster trouvé pour imdbId={imdb_id}, skip.")
                continue

            gen_poster_path = posters[0]

            # 3) affiche -> vecteur de thèmes prédit par le modèle du binôme
            try:
                y_pred = predict_themes_from_image(gen_poster_path)
            except NotImplementedError as e:
                print("\n[eval_loop] ATTENTION :")
                print("  La fonction predict_themes_from_image n'est pas encore implémentée.")
                print("  Tu dois la connecter au modèle image->thèmes de ton binôme.")
                if f_out is not None:
                    f_out.close()
                return

            y_pred = np.asarray(y_pred, dtype=np.float32)
            if use_normalized:
                # on normalise aussi y_pred si on a normalisé y_true
                y_pred = y_pred / (np.linalg.norm(y_pred) + 1e-8)

            # 4) métriques
            cos_sim = cosine_similarity(y_true, y_pred)
            top3 = topk_overlap(y_true, y_pred, k=3)
            top5 = topk_overlap(y_true, y_pred, k=5)

            all_results.append((imdb_id, cos_sim, top3, top5))

            if writer is not None:
                writer.writerow([imdb_id, cos_sim, top3, top5])

        if f_out is not None:
            f_out.close()

    finally:
        if f_out is not None and not f_out.closed:
            f_out.close()

    # Agrégation simple
    if all_results:
        cos_vals = [r[1] for r in all_results]
        top3_vals = [r[2] for r in all_results]
        top5_vals = [r[3] for r in all_results]

        print("\n[eval_loop] Résultats agrégés :")
        print(f"  Nombre d'exemples évalués : {len(all_results)}")
        print(f"  Cosine similarity moyen    : {np.mean(cos_vals):.3f}")
        print(f"  Top-3 overlap moyen        : {np.mean(top3_vals):.3f}")
        print(f"  Top-5 overlap moyen        : {np.mean(top5_vals):.3f}")
    else:
        print("[eval_loop] Aucun résultat exploitable.")


# ==========================
# 4. POINT D'ENTRÉE CLI
# ==========================

def main():
    parser = argparse.ArgumentParser(description="Boucle d'évaluation analyse <-> génération (baseline).")
    parser.add_argument(
        "--csv_path",
        type=str,
        default="data/movie_theme_vectors.csv",
        help="Chemin vers le CSV de thèmes (par défaut: data/movie_theme_vectors.csv).",
    )
    parser.add_argument(
        "--num_samples",
        type=int,
        default=50,
        help="Nombre de films à évaluer (par défaut: 50).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed pour l'échantillonnage aléatoire (par défaut: 0).",
    )
    parser.add_argument(
        "--use_normalized",
        action="store_true",
        help="Normaliser les vecteurs avant calcul des métriques.",
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="data/eval_results_baseline.csv",
        help="Fichier CSV de sortie pour les résultats détaillés (None pour désactiver).",
    )

    args = parser.parse_args()

    eval_loop(
        csv_path=args.csv_path,
        num_samples=args.num_samples,
        seed=args.seed,
        use_normalized=args.use_normalized,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
