import requests, re, os
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

def download_imdb_poster_from_imdb(imdb_url: str, out_path: str = "test.jpg",format_:str="182x268"):
    """
    fonction empruntée à internet, non créée,
    qui permet de télécharger des images depuis le site IMDb
    et pas depuis les liens fournis dans le CSV (meilleure qualité).
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    r = requests.get(imdb_url, headers=headers, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tag = soup.find("meta", property="og:image")
    img_url = tag["content"] if tag and tag.get("content") else None

    if not img_url:
        link_tag = soup.find("link", rel="image_src")
        img_url = link_tag["href"] if link_tag and link_tag.get("href") else None

    if not img_url:
        raise RuntimeError("Aucune URL d'image trouvée sur la page.")

    img_url = re.sub(r"\._V1_.*\.jpg", "._V1_.jpg", img_url)

    img = requests.get(img_url, headers=headers, timeout=30)
    img.raise_for_status()


    image = Image.open(BytesIO(img.content))
    if format_:
        try:
            largeur, hauteur = map(int, format_.lower().split("x"))
            image = image.resize((largeur, hauteur), Image.Resampling.LANCZOS)
        except Exception as e:
            raise ValueError(f"Format invalide '{format_}' : {e}")

    ext = os.path.splitext(img_url.split("?")[0])[1] or ".jpg"
    out_path = out_path if out_path.endswith(ext) else out_path + ext
    image.save(out_path)
    return out_path


def telecharger_poster_from_link(url, nom_image="test.jpg", print_=False):
    """
    télécharge l'image via le lien direct (qualité inférieure).
    """
    r = requests.get(url, stream=True, timeout=20)
    if r.status_code == 200:
        with open(nom_image, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        return True
    else:
        raise Exception(f"Erreur HTTP {r.status_code}")


def corriges_lurl(url_page="http://www.imdb.com/title/tt114709", print_=False):
    """
    les liens de la BDD ne sont plus valides,
    mais en les reformatant un peu, ça marche.
    """
    code = url_page.split("/")[-1]
    code_sans_t = code[2:]
    new_url = "http://www.imdb.com/fr/title/tt0" + code_sans_t
    return new_url    


#download_imdb_poster_from_imdb(corriges_lurl())

def main():
    source_d_info = "./MovieGenre.csv"
    sortie_image = "./MoviePosters/"
    
    if not os.path.exists(sortie_image):
        os.mkdir(sortie_image)
    
    depuis_le_site = False
    nb_lignes_traitees = 0     # tout ce qu’on a lu
    nb_download_tentes = 0     # ce qu’on a vraiment essayé de dl
    nb_erreurs = 0
    liste_des_erreur = []
    
    with open(source_d_info, newline='', encoding='latin1') as f:
        reader = list(csv.DictReader(f))
        with tqdm(total=len(reader), ncols=90, colour="cyan") as pbar:
            for ligne in reader:
                nb_lignes_traitees += 1
                code_poster = ligne["imdbId"]
                nom_poster = sortie_image + code_poster + ".jpg"

                if os.path.exists(nom_poster):
                    # on avance la barre quand même
                    pbar.set_description(f"Traités: {nb_lignes_traitees} | DL: {nb_download_tentes} | Err: {nb_erreurs}")
                    pbar.update(1)
                    continue

                nb_download_tentes += 1

                try:
                    if depuis_le_site:
                        imdb_url = corriges_lurl(ligne["Imdb Link"])
                        download_imdb_poster_from_imdb(imdb_url, nom_poster)
                    else:
                        # On considère que telecharger_poster_from_link renvoie True si OK.
                        success = telecharger_poster_from_link(ligne["Poster"], nom_poster)
                        if not success:
                            raise RuntimeError("Échec du téléchargement via le lien direct.")
                except Exception as e:
                    nb_erreurs += 1
                    liste_des_erreur.append((nom_poster, str(e)))


                pbar.set_description(
                    f"Traités: {nb_lignes_traitees} | DL: {nb_download_tentes} | Err: {nb_erreurs}"
                )
                pbar.update(1)

    print()
    print(f"{nb_lignes_traitees} lignes lues.")
    print(f"{nb_download_tentes - nb_erreurs} posters téléchargés.")
    print(f"{nb_erreurs} erreurs.")
    # print(liste_des_erreur)

main()
