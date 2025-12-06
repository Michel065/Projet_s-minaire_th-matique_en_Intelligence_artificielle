import os
import csv
import shutil
from tqdm import tqdm

# Liste des 28 genres dans l'ordre donné dans info_sur_le_csv.txt
GENRES = [
    "Animation", "Adventure", "Comedy",
    "Action", "Family", "Romance", "Drama",
    "Crime", "Thriller", "Fantasy", "Horror",
    "Biography", "History", "Mystery", "Sci-Fi",
    "War", "Sport", "Music", "Documentary", "Musical",
    "Western", "Short", "Film-Noir", "Talk-Show",
    "News", "Adult", "Reality-TV", "Game-Show"
]

def build_local_dataset(
    source_csv="../MovieGenre.csv",
    source_posters_dir="../MoviePosters",
    out_csv="data/movie_theme_vectors.csv",
    out_posters_dir="data/posters",
    max_movies=None  
):
    """
    Construit un dataset local pour themes_vers_images :
    - copie les affiches vers themes_vers_images/data/posters/
    - crée data/movie_theme_vectors.csv avec:
      imdbId, 28 colonnes de thèmes (0/1), poster_path
    """

    os.makedirs(out_posters_dir, exist_ok=True)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)

    with open(source_csv, newline="", encoding="latin1") as f_in:
        reader = list(csv.DictReader(f_in))

    fieldnames = ["imdbId"] + GENRES + ["poster_path"]

    with open(out_csv, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        nb_ok = 0
        nb_skip_no_poster = 0
        nb_skip_no_genre = 0

        with tqdm(total=len(reader), ncols=90, colour="cyan") as pbar:
            for row in reader:
                imdb_id = row.get("imdbId")
                if not imdb_id:
                    pbar.update(1)
                    continue

                # Poster dans MoviePosters à la racine
                src_poster = os.path.join(source_posters_dir, f"{imdb_id}.jpg")
                if not os.path.exists(src_poster):
                    nb_skip_no_poster += 1
                    pbar.update(1)
                    continue

                genres_str = row.get("Genre", "")
                if not genres_str:
                    nb_skip_no_genre += 1
                    pbar.update(1)
                    continue

                movie_genres = [g.strip() for g in genres_str.split("|") if g.strip()]

                genre_vector = {g: 0 for g in GENRES}
                any_valid = False
                for g in movie_genres:
                    if g in genre_vector:
                        genre_vector[g] = 1
                        any_valid = True

                if not any_valid:
                    nb_skip_no_genre += 1
                    pbar.update(1)
                    continue

                
                dst_poster = os.path.join(out_posters_dir, f"{imdb_id}.jpg")
                if not os.path.exists(dst_poster):
                    shutil.copy2(src_poster, dst_poster)

                poster_path_rel = os.path.join(out_posters_dir, f"{imdb_id}.jpg")
                poster_path_rel = poster_path_rel.replace("\\", "/")

                out_row = {
                    "imdbId": imdb_id,
                    "poster_path": poster_path_rel
                }
                for g in GENRES:
                    out_row[g] = genre_vector[g]

                writer.writerow(out_row)

                nb_ok += 1
                pbar.set_description(
                    f"OK: {nb_ok} | no_poster: {nb_skip_no_poster} | no_genre: {nb_skip_no_genre}"
                )
                pbar.update(1)

                if max_movies is not None and nb_ok >= max_movies:
                    break

    print()
    print(f"Films retenus   : {nb_ok}")
    print(f"Sans poster     : {nb_skip_no_poster}")
    print(f"Sans genre/util : {nb_skip_no_genre}")
    print(f"CSV écrit dans  : {out_csv}")
    print(f"Posters dans    : {out_posters_dir}")


if __name__ == "__main__":
    build_local_dataset()

