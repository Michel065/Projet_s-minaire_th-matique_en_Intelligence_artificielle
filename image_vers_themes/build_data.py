import sys,os, csv
import tensorflow as tf
import numpy as np
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit
import tool_stats as sd

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
    
def partage_les_datas(liste_liens_image=[], Y=[], ratio_val=0.15, ratio_test=0.15):
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

    X = np.array(liste_liens_image, dtype=object) #on convertie en array sinon MultilabelStratifiedShuffleSplit marche pas
    Y = np.asarray(Y) #pareil

    X_train, train_Y, X_temp, Y_temp = split_homogene(X.reshape(-1, 1), Y, repartition=(ratio_val + ratio_test))#ca .reshape(-1, 1) pour préciser qu'il y a une seul colone sinon ca marche pas aussi
    X_val, val_Y, X_test, test_Y = split_homogene(X_temp, Y_temp, repartition=(1 - ratio_val / (ratio_val + ratio_test)))

    train_X_liens = list(np.asarray(X_train).reshape(-1))
    val_X_liens   = list(np.asarray(X_val).reshape(-1))
    test_X_liens  = list(np.asarray(X_test).reshape(-1))    

    return (train_X_liens, train_Y), (val_X_liens, val_Y), (test_X_liens, test_Y)

def load_poster_pour_map(liens_poster,sortie_y):
    """
    Fonction qui permet de charger un poster, et la sortie_y est la pour l'utiliation 
    dans un map de cration_datatase.
    """
    img = tf.io.read_file(liens_poster)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    return img, sortie_y

def creation_dataset(X,Y,batch_size=64):
    """
    regroupe X et Y dans un dataset et definie le batch
    """
    ds = tf.data.Dataset.from_tensor_slices((X, Y))
    ds = ds.map(load_poster_pour_map, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size).prefetch(AUTOTUNE)
    return ds

def test():
    csv_path = "../MovieGenre.csv"
    img_dir  = "../MoviePosters/"

    liste_liens_image, liste_themes_par_image,liste_des_genres = construction_tuple_image_themes(csv_path, img_dir)
    #print(liste_des_genres, len(liste_des_genres))
    #sd.calculs_repartition_themes(liste_themes_par_image)
    Y = convertisseur_themes_en_vecteur(liste_themes_par_image,liste_des_genres)
    #print("sortie Y ",Y[10000])
    #print("liste des genres:",liste_des_genres)
    #print("conparatifs:",liste_themes_par_image[10000])

    (train_X_liens, train_Y), (val_X_liens, val_Y), (test_X_liens, test_Y)=partage_les_datas(liste_liens_image,Y)
    #test des résultat
    #sd.calculs_repartition_themes_Y(train_Y,liste_des_genres,"répartition pour le train")
    #sd.calculs_repartition_themes_Y(val_Y,liste_des_genres,"répartition pour le val")
    #sd.calculs_repartition_themes_Y(test_Y,liste_des_genres)
