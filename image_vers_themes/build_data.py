import sys,os, csv, numpy as np, tensorflow as tf

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

def calculs_repartition_themes(liste_themes_par_image):
    """
    Calcule et affiche la répartition % de chaque theme dans la liste.
    """
    dico = {}
    for themes_image in liste_themes_par_image:
        for theme in themes_image:
            if theme in dico:
                dico[theme] += 1
            else:
                dico[theme] = 1

    total = sum(dico.values())
    if total == 0:
        print("Aucune donnée trouvée.")
        return
    
    print()
    print("Répartition des thèmes:")
    for theme, count in sorted(dico.items(), key=lambda x: x[1], reverse=True):
        pourcentage = (count / total) * 100
        print(f" - {theme:<20}: {pourcentage:.3f}% ({count})")

    return dico

    


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

def test():
    csv_path = "../MovieGenre.csv"
    img_dir  = "../MoviePosters/"

    liste_liens_image, liste_themes_par_image,liste_des_genres = construction_tuple_image_themes(csv_path, img_dir)
    #print(liste_des_genres, len(liste_des_genres))
    #calculs_repartition_themes(liste_themes_par_image)
    Y = convertisseur_themes_en_vecteur(liste_themes_par_image,liste_des_genres)
    print("sortie Y ",Y[10000])
    print("liste des genres:",liste_des_genres)
    print("conparatifs:",liste_themes_par_image[10000])

test()