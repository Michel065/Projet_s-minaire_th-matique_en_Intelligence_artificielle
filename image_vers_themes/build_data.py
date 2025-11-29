import sys,os, csv, random
import json
import tensorflow as tf
import numpy as np
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit

#ca c'est pour l'augmentation de data
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

AUTOTUNE = tf.data.AUTOTUNE

def construction_tuple_image_themes(csv_dos, imgages_dos):
    """
    Fonction qui doit ouvrir le csv et faire les tuples de donnée (liens_image,themes)
    
    et doit filtrer selon si l'image existe bien ou si des themes sont associer

    liste_des_genres permet d'avoir la liste de tout les elements

    Retourne: (liste_nom_image, liste_themes_par_image,liste_des_genres)
    """
    
    liste_liens_image, liste_themes_par_image,liste_des_genres = [], [],[]
    with open(csv_dos, newline='', encoding='latin1') as f:
        reader = csv.DictReader(f)
        for ligne in reader:
            imdb_id = ligne["imdbId"]
            liens_image = os.path.join(imgages_dos, f"{imdb_id}.jpg")
            if os.path.exists(liens_image):
                genres = [genre.strip() for genre in ligne["Genre"].split("|") if genre!='']
                if(len(genres) > 0):
                    liste_liens_image.append(liens_image)
                    liste_themes_par_image.append(genres)

                    for genre in genres:
                        if(genre not in liste_des_genres):
                            liste_des_genres.append(genre)

    return liste_liens_image, liste_themes_par_image,liste_des_genres

def convertisseur_themes_en_vecteur(liste_themes_par_image,liste_des_genres):
    """
    Fonction pour transformer les liste_themes_par_image en liste_vecteur_themes_par_image
    exemple : [1,0,0] pour [drama,autre, autre] poster=drama

    ce qui corespondra à la sortie attendu de notre modèle

    """
    info = {genre:index for index,genre in enumerate(liste_des_genres)}
    Y=[]
    ligne=[0 for i in liste_des_genres]
    for genres in (liste_themes_par_image):
        ligne_tmp=ligne.copy()
        for genre in genres:
            ligne_tmp[info[genre]]=1
        Y.append(ligne_tmp)
    return Y

def split_homogene(X, y, repartition=0.2, ):
    """
    fonction qui prend des np array et split mais de facon homogene. 
    ca viens de: https://www.kaggle.com/code/ljh0128/multi-label-data-split-method pour la structure
    """
    msss = MultilabelStratifiedShuffleSplit(n_splits=1, test_size=repartition, random_state=42)
    for train_idx, test_idx in msss.split(X, y):
        return X[train_idx], y[train_idx], X[test_idx], y[test_idx]
    
def partage_les_datas(X_full=[], Y_full=[], ratio_val=0.15, ratio_test=0.15):
    """
    Fonction qui répartit les posters en ensembles d'entraînement, de validation et de test
    mais en gardant une répartition !!homogène!! des thèmes
    
    Args:
        liste_liens_image 
        Y: calculé avec convertisseur_themes_en_vecteur()
        ratio_val: proportion de validation
        ratio_test: proportion de test 

    Returns:
        (train_X_liens, train_Y), (val_X_liens, val_Y), (test_X_liens, test_Y)
    """
    X = np.array(X_full, dtype=object) #on convertie en array sinon MultilabelStratifiedShuffleSplit marche pas
    Y = np.asarray(Y_full) #pareil

    X_train, train_Y, X_temp, Y_temp = split_homogene(X.reshape(-1, 1), Y, repartition=(ratio_val + ratio_test))#ca .reshape(-1, 1) pour préciser qu'il y a une seul colone sinon ca marche pas aussi
    X_val, val_Y, X_test, test_Y = split_homogene(X_temp, Y_temp, repartition=(1 - ratio_val / (ratio_val + ratio_test)))

    train_X = list(np.asarray(X_train).reshape(-1))
    val_X   = list(np.asarray(X_val).reshape(-1))
    test_X  = list(np.asarray(X_test).reshape(-1))    

    return (train_X, train_Y), (val_X, val_Y), (test_X, test_Y)

def load_poster_pour_map(liens_poster,sortie_y):
    """
    Fonction qui permet de charger un poster, et la sortie_y est la pour l'utiliation 
    dans un map de cration_datatase.
    """
    img = tf.io.read_file(liens_poster)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    return img, sortie_y

def creation_dataset(X,Y,batch_size=64, shuffle=False, shuffle_buffer=10000):
    """
    regroupe X et Y dans un dataset et definie le batch
    """
    ds = tf.data.Dataset.from_tensor_slices((X, Y))

    if shuffle:
        # on limite le buffer au nombre d'éléments pour éviter de tuer la RAM si on a beaucoup de data
        buffer_size = min(shuffle_buffer, len(X))
        ds = ds.shuffle(buffer_size=buffer_size)

    ds = ds.map(load_poster_pour_map, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(AUTOTUNE)
    return ds

def save_json(path, dico):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dico,f,ensure_ascii=False,separators=(",", ":"),indent=None)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_poster_with_transformation(lien_origine_poster, y_original, num_variante=1, img_dir_boost="../MoviePosters_boost"):
    """
    Génère une variante du poster selon num_variante, l'enregistre dans img_dir_boost
    et retourne (new_path, new_y).

    Pour l'instant new_y = y_original, mais on pourra plus tard "tricher" en modifiant
    les thèmes trop fréquents ici.
    """
    if not os.path.exists(lien_origine_poster):
        raise FileNotFoundError(f"Poster introuvable : {lien_origine_poster}")

    os.makedirs(img_dir_boost, exist_ok=True)

    img = Image.open(lien_origine_poster).convert("RGB")

    def t_flip_h(im):  return ImageOps.mirror(im)
    def t_color(im):   return ImageEnhance.Color(im).enhance(1.3)
    def t_contrast(im):return ImageEnhance.Contrast(im).enhance(1.2)
    def t_sharpen(im): return im.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    transforms = [t_flip_h, t_color, t_contrast,t_sharpen]

    # On utilise num_variante comme masque binaire
    mask = num_variante
    if mask == 0:
        raise ValueError("Mask à 0, c'est louche !!")

    for i, transfo in enumerate(transforms):
        if mask & (1 << i):
            img = transfo(img)

    base = os.path.splitext(os.path.basename(lien_origine_poster))[0]
    new_name = f"{base}_boost_{num_variante}.jpg"
    new_path = os.path.join(img_dir_boost, new_name)

    img.save(new_path, format="JPEG", quality=95)
    new_y = y_original.copy()

    return new_path, new_y

def reformate_vecteur_themes_par_image(Y_full, mask_genres_other):
    """
    Fusionne les genres masqués dans une seule colonne 'Other'.
    - Y_full
    - mask_genres_other

    Retour :
        New_Y :
    """
    Y_full = np.asarray(Y_full)
    mask = np.asarray(mask_genres_other)

    if Y_full.ndim != 2 or mask.ndim != 1:
        raise ValueError("Dimensions invalides : Y_full doit être (N,K) et mask (K,)")

    if Y_full.shape[1] != mask.shape[0]:
        raise ValueError("Taille de mask incohérente avec Y_full.")

    # Séparation des colonnes normales et masquées
    cols_normales = np.where(~mask)[0]   # indices à conserver
    cols_other    = np.where(mask)[0]    # indices à fusionner

    # Extraction
    Y_normales = Y_full[:, cols_normales]
    Y_others   = Y_full[:, cols_other]

    # Fusion des colonnes masquées
    col_other = (Y_others.max(axis=1) if Y_others.shape[1] > 0 else np.zeros(Y_full.shape[0]))

    # Construction de la nouvelle matrice
    New_Y = np.concatenate([Y_normales, col_other.reshape(-1, 1)],axis=1)
    return New_Y

def verif_image_existe(image_path=""):
    if(image_path is not None):
        return os.path.exists(image_path)
    
def recup_aleatoirement_x_image_from_dir(folder_path="",nb_random=1):
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Dossier introuvable : {folder_path}")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Le chemin n'est pas un dossier : {folder_path}")
    
    EXT = {".jpg", ".jpeg", ".png"}
    liste_images = [os.path.join(folder_path, f) for f in os.listdir(folder_path)if os.path.splitext(f.lower())[1] in EXT]
    
    nbr_total = len(liste_images)

    if nbr_total == 0:
        raise ValueError(f"Aucune image valide trouvée dans : {folder_path}")

    if nb_random > nbr_total:
        raise ValueError(
            f"Nombre demandé ({nb_random}) > nombre d'images disponibles ({nbr_total})"
        )
    return random.sample(liste_images, nb_random)