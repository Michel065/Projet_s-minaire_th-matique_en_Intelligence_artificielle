import build_data as bd
import build_model as bm
import train as t
import tool_stats as ts
import numpy as np
import os

csv_path = "../MovieGenre.csv"
img_dir  = "../MoviePosters/"

json_filter_path = "../data_filtrer.json"
img_dir_boost  = "../MoviePosters_boost"

def boucle_entrainement_complet(nbr_epoch=50):
    print("Extraction des couple: (liens_image,liste_themes) + recuperation de la liste des differents themes.")
    liste_liens_image, liste_themes_par_image,liste_des_genres = bd.construction_tuple_image_themes(csv_path, img_dir)

    print("Conversion des liste_themes en vecteurs de 0 et 1.")
    Y = bd.convertisseur_themes_en_vecteur(liste_themes_par_image,liste_des_genres)

    print("Répartition des données en 3 enssembles pour le train, la val (pendant le train) et le test.")
    (train_X_liens, train_Y), (val_X_liens, val_Y), (test_X_liens, test_Y)=bd.partage_les_datas(liste_liens_image,Y)

    print("Creation des dataset et def des batch size.")
    batch_size=64
    dataset_train = bd.creation_dataset(train_X_liens,train_Y,batch_size)
    dataset_val = bd.creation_dataset(val_X_liens,val_Y,batch_size)
    dataset_test = bd.creation_dataset(test_X_liens,test_Y,batch_size)

    print("Definition de la strategie et du modèle.")
    model = t.define_startegie(bm.build_model)

    print("Entrainement du modèle.")
    history = t.train_model(model,dataset_train,dataset_val,nbr_epoch)

    print("Evalution du modèle.")
    t.evalution_du_model(model,dataset_test)

    print("Génére les courbe d'apprentissage.")
    ts.creation_courbe_accuracy_loss_from_hitory(history.history)

def construction_filter_json():
    print("_____ Construction du CSV filtré _____")
    print("Extraction des couples (liens_image, liste_themes) + récupération des thèmes.")
    liste_liens_image, liste_themes_par_image, liste_des_genres = bd.construction_tuple_image_themes(csv_path, img_dir)

    print("Conversion des liste_themes en vecteurs multi-hot.")
    vecteur_themes_par_image = bd.convertisseur_themes_en_vecteur(liste_themes_par_image, liste_des_genres)

    filter_data = {
        "liste_des_genres": liste_des_genres,
        "liste_liens_image": liste_liens_image,
        "vecteur_themes_par_image": vecteur_themes_par_image
    }

    print("Sauvegarde du json filtré…")
    bd.save_json(json_filter_path, filter_data )

    print("____________________________________")

def extraction_theme_rare(source=json_filter_path, seuil=2,aff=False):  # 2% = rare
    print("_____ extraction_theme_rare _____")
    data = bd.load_json(source)
    liste_key = list(data.keys())
    liste_theme_rare = []
    if not ("liste_theme_rare" in liste_key):
        repartition = ts.calculs_repartition_themes_vecteur(data["vecteur_themes_par_image"],data["liste_des_genres"],print_data=True)
        for theme, stats in repartition.items():
            pourcentage = stats[0]
            if pourcentage < seuil:
                liste_theme_rare.append((theme, pourcentage, stats[1]))
    else:
        liste_theme_rare = data["liste_theme_rare"]
    if(aff):
        for (theme, st, co) in liste_theme_rare:
            print(theme,":",st,"(",co,")")
    print("Mise à jour du json filtré")
    data["liste_theme_rare"]=liste_theme_rare
    bd.save_json(json_filter_path, data)
    print("____________________________________")
    return liste_theme_rare

def boost_theme_rare(source=json_filter_path, max_variantes_par_image=15,facteur_cible=0.5,seuil_ultra_rare = 10,afff=False):
    """
    On va chercher à prendre les thèmes rares et à dupliquer les images associées
    en les transformant (augmentation de données) pour réduire l'écart de répartition.

    params:
    - source
    - max_variantes_par_image
    - facteur_cible : on essaie de rapprocher les rares à XX% du niveau moyen.
    """
    print("_____ boost_theme_rare _____")

    data = bd.load_json(source)
    liste_des_genres = data["liste_des_genres"]
    liste_liens_image = data["liste_liens_image"]
    vecteur_themes_par_image = np.asarray(data["vecteur_themes_par_image"])
    liste_theme_rare = data.get("liste_theme_rare", [])

    liste_liens_image_boost = []
    vecteur_themes_par_image_boost = []

    nb_images = vecteur_themes_par_image.shape[0]

    counts, dico_genre_vers_idx = ts.construire_index_genres_vecteur(vecteur_themes_par_image,liste_des_genres)

    set_rares = {t[0] for t in liste_theme_rare}
    counts_non_rares = [counts[i] for i, g in enumerate(liste_des_genres) if g not in set_rares]
    moyenne_non_rares = np.mean(counts_non_rares) if len(counts_non_rares) > 0 else 0
    print(f"Moyenne d'occurrences des genres non rares : {moyenne_non_rares:.1f}")
    freq_moyenne = moyenne_non_rares / counts.sum()
    print(f"Seuil automatique pour 'thème fréquent' : {freq_moyenne*100:.2f}%")

    duplications_par_image = {i: 0 for i in range(nb_images)}

    nbr_ajout_boost=0

    for theme, _, count in liste_theme_rare:
        if moyenne_non_rares == 0:
            continue
        
        if count < seuil_ultra_rare:
            # ultra rare, on va au max_variantes_par_image
            target = int(moyenne_non_rares)
            a_ajouter = max(0, target - count)
        else:
            # cas normal
            target = int(moyenne_non_rares * facteur_cible)
            a_ajouter = max(0, target - count)

        nbr_tmp_ajout_boost=0
        if a_ajouter == 0:
            continue

        # Liste des images contenant ce thème
        idx_candidats = dico_genre_vers_idx.get(theme, [])
        if not idx_candidats:
            continue

        # On trie les candidats, on préfère ceux qui ont peu de gros genres
        scores_candidats = []
        for idx in idx_candidats:
            y = vecteur_themes_par_image[idx]
            # pénalise les gros thèmes (ex: Drama, Comedy, etc.) 
            penalite = 0
            for j, val in enumerate(y):
                if val == 1:
                    freq = counts[j] / counts.sum()  # fréquence globale
                    if freq > freq_moyenne:
                        penalite += 1
            scores_candidats.append((penalite, idx))

        scores_candidats.sort()  # les moins pénalisés d'abord
        idx_candidats_tries = [idx for (pen, idx) in scores_candidats]

        # génération des augmentations
        i_cand = 0
        nb_cand = len(idx_candidats_tries)

        for _ in range(a_ajouter):
            idx_img = idx_candidats_tries[i_cand]
            
            nbr_actuel_variantes=duplications_par_image[idx_img]
            # on surveille le seuil
            if nbr_actuel_variantes >= max_variantes_par_image:
                # on avance dans les candidats, si on boucle partout on arrête
                i_cand = (i_cand + 1) % nb_cand
                if all(duplications_par_image[i] >= max_variantes_par_image for i in idx_candidats_tries):
                    break
                continue

            ancien_chemin = liste_liens_image[idx_img]
            y_original = vecteur_themes_par_image[idx_img].tolist()

            new_path, new_y = bd.generate_poster_with_transformation(ancien_chemin,y_original,nbr_actuel_variantes+1,img_dir_boost)
            nbr_tmp_ajout_boost+=1
            if(afff):
                print(new_path)
            liste_liens_image_boost.append(new_path)
            vecteur_themes_par_image_boost.append(new_y)

            duplications_par_image[idx_img] += 1
            i_cand = (i_cand + 1) % nb_cand

        nbr_ajout_boost+=nbr_tmp_ajout_boost
        print(f"[{theme}] actuel={count}, cible={target}, à ajouter={a_ajouter}, ajouté réellement {nbr_tmp_ajout_boost}.")


    print("Mise à jour du json filtré avec les données boostées")

    data["liste_liens_image_boost"] = liste_liens_image_boost
    data["vecteur_themes_par_image_boost"] = vecteur_themes_par_image_boost
    print(f"Au final {nbr_ajout_boost} posters ajouté.")

    bd.save_json(source, data)
    print("____________________________")

def calculs_repartition_with_boost(source=json_filter_path,print_data=True,titre="Répartition des thèmes (avec boost)"):
    """
    Charge le json filtré, fusionne les vecteurs originaux + boost,
    puis calcule la répartition globale des thèmes.

    Retourne un dict : { theme: [pourcentage, count], ... }
    """
    data = bd.load_json(source)
    Y_base = np.asarray(data["vecteur_themes_par_image"])
    Y_boost = data.get("vecteur_themes_par_image_boost", [])#on recup si on peut

    if len(Y_boost) > 0:
        Y_boost = np.asarray(Y_boost)
        Y_total = np.concatenate([Y_base, Y_boost], axis=0)
    else:
        Y_total = Y_base

    # on réutilise la fonction de stats déjà existante
    repartition = ts.calculs_repartition_themes_vecteur(Y_total,data["liste_des_genres"],titre=titre,print_data=print_data)

    return repartition

def construire_data_boost(source=json_filter_path,img_dir_boost=img_dir_boost):
    """
    1. Vérifie si data_filter existe
    2. Charge les données
    3. Extrait les themes rares
    4. Boost les images
    5. Affiche la comparaison avant/après
    """
    print("_________CONSTRUCTION DATA BOOST __________")

    if os.path.exists(img_dir_boost):
       print("Fichier de boost deja existant,on annule")
       return 
    
    if not os.path.exists(source):
        print(f"ERREUR : Le fichier '{source}' n'existe pas. creation ...")
        construction_filter_json()
    data = bd.load_json(source)
    vect_base = np.asarray(data["vecteur_themes_par_image"])
    liste_des_genres = data["liste_des_genres"]
    repart_avant = ts.calculs_repartition_themes_vecteur(vect_base,liste_des_genres,print_data=False,titre="Répartition AVANT boost :")
    print("\nExtraction des thèmes rares…")
    extraction_theme_rare(source)
    print("\nGénération des images boostées…")
    boost_theme_rare(source)
    repart_apres = calculs_repartition_with_boost(source)
    ts.comparaison_repartition(repart_avant, repart_apres, liste_des_genres)
    print("_____________________________________")

construire_data_boost()