import build_data as bd
import tool_stats as ts
import numpy as np
import os

def boost_theme_rare_de_train(source="../data_filtrer.json",img_dir_boost  = "../MoviePosters_boost", max_variantes_par_image=15,facteur_cible=0.5,afff=False):
    """
    On va chercher à prendre les thèmes rares et à dupliquer les images associées
    en les transformant (augmentation de données) pour réduire l'écart de répartition.

    params:
    - source
    - max_variantes_par_image
    - facteur_cible : on essaie de rapprocher les rares à XX% du niveau moyen.
    """
    print("_____ boost_train_theme_rare _____")

    data = bd.load_json(source)

    # Vérification
    required_keys = ["liste_des_genres", "liste_theme_rare", "train_X", "train_Y"]
    for k in required_keys:
        if k not in data:
            print(f"ERREUR : clé '{k}' absente du fichier {source}.")
            print("____________________________________")
            return

    liste_des_genres = data["liste_des_genres"]
    liste_theme_rare = data["liste_theme_rare"]
    train_X = data["train_X"]
    train_Y = np.asarray(data["train_Y"])

    train_X_boost = []
    train_Y_boost = []

    if len(liste_des_genres) == 0:
        print("ERREUR : 'liste_des_genres' est vide. Impossible de booster.")
        print("____________________________________")
        return

    if len(train_X) == 0 or train_Y.size == 0:
        print("ERREUR : train_X / train_Y vides. Le split n'a probablement pas été fait.")
        print("____________________________________")
        return

    if train_Y.ndim != 2 or train_Y.shape[1] != len(liste_des_genres):
        print("ERREUR : Dimensions de train_Y incompatibles avec liste_des_genres.")
        print(f" - train_Y.shape = {train_Y.shape}")
        print(f" - len(liste_des_genres) = {len(liste_des_genres)}")
        print("____________________________________")
        return

    if len(train_X) != train_Y.shape[0]:
        print("ERREUR : train_X et train_Y n'ont pas le même nombre d'échantillons.")
        print(f" - len(train_X) = {len(train_X)}")
        print(f" - train_Y.shape[0] = {train_Y.shape[0]}")
        print("____________________________________")
        return

    nb_images = train_Y.shape[0]
    counts, dico_genre_vers_idx = ts.construire_index_genres_vecteur(train_Y,liste_des_genres)
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
            y = train_Y[idx]
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

            ancien_train_X = train_X[idx_img]
            y_original = train_Y[idx_img].tolist()

            new_path, new_y = bd.generate_poster_with_transformation(ancien_train_X,y_original,nbr_actuel_variantes+1,img_dir_boost)
            nbr_tmp_ajout_boost+=1
            if(afff):
                print(new_path)
            train_X_boost.append(new_path)
            train_Y_boost.append(new_y)

            duplications_par_image[idx_img] += 1
            i_cand = (i_cand + 1) % nb_cand

        nbr_ajout_boost+=nbr_tmp_ajout_boost
        print(f"[{theme}] actuel={count}, cible={target}, à ajouter={a_ajouter}, ajouté réellement {nbr_tmp_ajout_boost}.")

    print("Mise à jour du json filtré avec les données boostées")

    data["train_X_boost"] = train_X_boost
    data["train_Y_boost"] = train_Y_boost
    print(f"Au final {nbr_ajout_boost} posters ajouté.")

    bd.save_json(source, data)
    print("____________________________")

def calculs_repartition_with_boost(source="../data_filtrer.json",print_data=True,titre="Répartition des thèmes (avec boost)"):  
    """
    Charge le json filtré, fusionne les vecteurs originaux + boost,
    puis calcule la répartition globale des thèmes.

    Retourne un dict : { theme: [pourcentage, count], ... }
    """
    data = bd.load_json(source)

    # Vérification
    required_keys = ["train_Y", "train_Y_boost"]
    for k in required_keys:
        if k not in data:
            print(f"ERREUR : clé '{k}' absente du fichier {source}.")
            print("____________________________________")
            return
        
    if len(data["train_Y"]) == 0 or len(data["train_Y_boost"]) == 0:
        print("ERREUR : train_Y ou train_Y_boost est vide.")
        print("Il faut d’abord exécuter la phase de boost et la répartition initiale.")
        print("____________________________________")
        return
    
    train_Y = np.asarray(data["train_Y"])
    train_Y_boost = np.asarray(data["train_Y_boost"])
    Y_total = np.concatenate([train_Y, train_Y_boost], axis=0)
    # on réutilise la fonction de stats déjà existante
    repartition = ts.calculs_repartition_themes_vecteur(Y_total,data["liste_des_genres"],titre=titre,print_data=print_data)

    return repartition

