from typing import List
from utils import parse_user_themes, GENRES
from search_by_theme import search_similar_posters


def predict_posters_from_themes(theme_str: str, top_k: int = 5) -> List[str]:
    """
    Pipeline simple pour prédire les affiches les plus proches
    d'une liste de thèmes (baseline : recherche par similarité).
    """
    # 1. Convertir les thèmes en vecteur
    query_vec = parse_user_themes(theme_str, binary=True)

    # 2. Recherche par similarité
    results = search_similar_posters(query_vec, top_k=top_k)

    # 3. Extraire uniquement les chemins des affiches
    poster_paths = [img_path for (_, _, img_path) in results]
    return poster_paths


def main():
    print("=== Baseline Thèmes -> Posters ===")
    theme_str = input("Entrez vos thèmes (ex: 'action, horreur, drame'): ")

    posters = predict_posters_from_themes(theme_str, top_k=5)

    print("\nRésultats :")
    for p in posters:
        print(" -", p)


if __name__ == "__main__":
    main()
