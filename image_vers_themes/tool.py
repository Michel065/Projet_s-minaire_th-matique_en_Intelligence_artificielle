#fichier qui va servir a rassembler les fonction principale du code soit celle qui le param ou le contruise
import build_data as bd
import build_model as bm
import tool_stats as ts
import extend_data as ed
import train as t
import numpy as np
import os,shutil

def construction_filter_json(csv_path="../MovieGenre.csv", img_dir= "../MoviePosters/",output_source="../data_filtrer.json"):
    print("_____ Construction du CSV filtré _____")
    print("Extraction des couples (liens_image, liste_themes) + récupération des thèmes.")
    train_X, liste_themes_par_image, liste_des_genres = bd.construction_tuple_image_themes(csv_path, img_dir)

    print("Conversion des liste_themes en vecteurs multi-hot.")
    train_Y = bd.convertisseur_themes_en_vecteur(liste_themes_par_image, liste_des_genres)
    filter_data = {
        "liste_des_genres": liste_des_genres,
        "X_full": train_X,
        "Y_full": train_Y,
        "train_X": [],
        "train_Y": [],
        "val_X":   [],
        "val_Y":   [],
        "test_X":   [],
        "test_Y":   [],
        "train_X_boost":   [],
        "train_Y_boost":   [],
        "liste_theme_rare":   [],
        "seuils_optimaux":   [],
    }
    print("Sauvegarde du json filtré…")
    bd.save_json(output_source, filter_data )
    print("____________________________________\n")

def extraction_theme_rare(source="../data_filtrer.json", seuil=2,aff=False):  # 2% = rare
    print("_____ extraction_theme_rare _____")
    data = bd.load_json(source)
    liste_theme_rare = []
    repartition = ts.calculs_repartition_themes_vecteur(data["Y_full"],data["liste_des_genres"],print_data=False)
    for theme, stats in repartition.items():
        pourcentage = stats[0]
        if pourcentage < seuil:
            liste_theme_rare.append((theme, pourcentage, stats[1]))
    if(aff):
        for (theme, st, co) in liste_theme_rare:
            print(theme,":",st,"(",co,")")
    print("Mise à jour du json filtré")
    data["liste_theme_rare"]=liste_theme_rare
    bd.save_json(source, data)
    print("____________________________________\n")
    return liste_theme_rare

def construire_data_boost_train(source="../data_filtrer.json",img_dir_boost="../MoviePosters_boost",max_variantes_par_image=15,facteur_cible=0.5):
    """
    1. Vérifie si data_filter existe
    2. Charge les données
    3. Extrait les themes rares
    4. Boost les images
    5. Affiche la comparaison avant/après
    """
    print("_________CONSTRUCTION DATA BOOST __________")
    
    if not os.path.exists(source):
        print(f"ERREUR : Le fichier '{source}' n'existe pas. on doit le créer avant!!")
        return

    img_ajoute=0

    data = bd.load_json(source)
    vect_base = np.asarray(data["train_Y"])
    liste_des_genres = data["liste_des_genres"]
    repart_avant = ts.calculs_repartition_themes_vecteur(vect_base,liste_des_genres,print_data=False,titre="Répartition train_X AVANT boost :")
    
    if os.path.exists(img_dir_boost):
       print("Fichier de boost deja existant,on annule la création")
    else: 
        print("\nGénération des images boostées…")
        img_ajoute = ed.boost_theme_rare_de_train(source,img_dir_boost,max_variantes_par_image,facteur_cible)

    repart_apres = ed.calculs_repartition_with_boost(source,False)
    ts.comparaison_repartition(repart_avant, repart_apres, liste_des_genres)
    print("_____________________________________\n")
    return img_ajoute

def fusionner_genres_trop_rares_en_other(source="../data_filtrer.json",seuil_min_count=100,nom_other="Other"):
    """
    Charge le data_filtrer.json, repère les genres trop rares (count < seuil_min_count),
    et prépare la fusion de ces genres dans une classe 'Other'.

    - Met à jour:
        - data["liste_des_genres"]
        - data["Y_full"]
        - data["liste_theme_rare"]
    """
    print("_____ fusionner_genres_rares_en_other _____")

    data = bd.load_json(source)

    if "liste_des_genres" not in data or "Y_full" not in data or "liste_theme_rare" not in data :
        print("ERREUR : 'liste_des_genres' ou 'Y_full' ou 'liste_theme_rare' manquants dans le json.")
        print("Impossible de fusionner les genres trop rares.")
        print("___________________________________________\n")
        return

    ancienne_liste = data["liste_des_genres"]
    Y_full = np.asarray(data["Y_full"])
    liste_theme_rare = data["liste_theme_rare"]

    # Vérification
    if Y_full.ndim != 2 or Y_full.shape[1] != len(ancienne_liste):
        print("ERREUR : Dimensions de vecteur_themes_par_image incompatibles avec liste_des_genres.")
        print(f" - Y_full.shape = {Y_full.shape}")
        print(f" - len(liste_des_genres) = {len(ancienne_liste)}")
        print("___________________________________________\n")
        return

    # Genres trop rares à fusionner dans Other
    themes_trop_rares = [theme for (theme, _,count) in liste_theme_rare if count < seuil_min_count]
    themes_trop_rares_data = [(p,c) for (t, p,c) in liste_theme_rare if t in themes_trop_rares]

    if len(themes_trop_rares) == 0:
        print(f"Aucun genre avec count < {seuil_min_count}. Rien à fusionner.")
        print("___________________________________________\n")
        return

    print(f"Genres fusionnés en '{nom_other}' (count < {seuil_min_count}) : {themes_trop_rares}")

    # Construction du mask 
    # True, theme sera mappé vers 'Other'
    mask_genres_other = []
    for genre in ancienne_liste:
        mask_genres_other.append(genre in themes_trop_rares)

    nouvelle_liste = [g for g in ancienne_liste if g not in themes_trop_rares]
    if nom_other not in nouvelle_liste:
        nouvelle_liste.append(nom_other)

    New_Y_full = bd.reformate_vecteur_themes_par_image(Y_full,mask_genres_other)

    
    new_liste_theme_rare = [elt for elt in liste_theme_rare if elt[0] not in themes_trop_rares]

    count_other = sum(c for (_,c) in themes_trop_rares_data)
    if (nom_other not in [t for (t,_,_) in new_liste_theme_rare]) and count_other > 0:
        pct_other = sum(p for (p,_) in themes_trop_rares_data)
        new_liste_theme_rare.append((nom_other,pct_other,count_other))
    
    data["Y_full"] = New_Y_full.tolist()
    data["liste_des_genres"] = nouvelle_liste
    data["liste_theme_rare"] = new_liste_theme_rare

    bd.save_json(source, data)

    print(f"Nouvelle liste des genres ({len(nouvelle_liste)} genres) sauvegardée.")
    print("_______________________\n")
    return new_liste_theme_rare

def split_train_eval_test(source="../data_filtrer.json", ratio_val=0.15, ratio_test=0.15):
    """
    Split X_full / Y_full en ensembles :
    - train
    - val
    - test

    Les résultats sont sauvegardés dans le JSON :
    - train_X, train_Y
    - val_X, val_Y
    - test_X, test_Y
    """

    print("_________split_train_eval_test__________")
    data = bd.load_json(source)

    if "X_full" not in data or "Y_full" not in data:
        print("ERREUR : X_full ou Y_full non trouvés dans le JSON.")
        print("_________________________________________\n")
        return

    (train_X, train_Y), (val_X, val_Y), (test_X, test_Y)=bd.partage_les_datas(data["X_full"],data["Y_full"],ratio_val,ratio_test)
    
    data["train_X"] = train_X
    data["train_Y"] = train_Y.tolist()

    data["val_X"] = val_X
    data["val_Y"] = val_Y.tolist()

    data["test_X"] = test_X
    data["test_Y"] = test_Y.tolist()

    print(f"Répartition : train={len(train_X)}, val={len(val_X)}, test={len(test_X)}")
    print("Mise à jour du json filtré")
    bd.save_json(source, data)
    print("_________________________________________\n")
    return len(train_X),len(val_X),len(test_X)

def generer_datasets(source="../data_filtrer.json", batch_size=64,boost=True):
    print("_____ génération des datasets TF _____")

    data = bd.load_json(source)

    train_X = data["train_X"]
    train_Y = np.asarray(data["train_Y"])

    if ("train_X_boost" in data and "train_Y_boost" in data) and boost:
        train_X = train_X + data["train_X_boost"]
        train_Y = np.concatenate([train_Y, np.asarray(data["train_Y_boost"])], axis=0)

    val_X   = data["val_X"]
    val_Y   = np.asarray(data["val_Y"])
    test_X  = data["test_X"]
    test_Y  = np.asarray(data["test_Y"])

    dataset_train = bd.creation_dataset(train_X, train_Y, batch_size=batch_size, shuffle=True)
    dataset_val   = bd.creation_dataset(val_X,   val_Y,   batch_size=batch_size, shuffle=False)
    dataset_test  = bd.creation_dataset(test_X,  test_Y,  batch_size=batch_size, shuffle=False)
    print("_______________________________\n")
    return dataset_train, dataset_val, dataset_test

def entrainement(dataset_train, dataset_val,source="../data_filtrer.json",EPOCHS=50,output_dir="../model",name_model="cnn",forme=(268,182,3)):
    """
    Pipeline d'entraînement complet :
    - Vérifie la présence du fichier data_filter
    - Construit et compile le modèle
    - Entraîne le modèle
    Retourne :model entraîné
    """
    print(f"___________ ENTRAINEMENT lancer ({EPOCHS})___________")
    if not os.path.exists(source):
        raise FileNotFoundError(f"ERREUR : Le fichier '{source}' est introuvable. ")

    data = bd.load_json(source)

    # Verification
    required_keys = ["liste_des_genres"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"ERREUR : La clé '{k}' manque dans {source}. ")

    liste_des_genres = data["liste_des_genres"]

    param_model = (forme, len(liste_des_genres))
    model = t.define_startegie(bm.build_model, param_model)

    print("Modèle compilé")

    history,model = t.train_model(model, dataset_train, dataset_val,EPOCHS,output_dir)
    print("Entraînement terminé")
    
    t.save_model_entier(model,output_dir,name_model)
    print("Sauvegarde model!")

    t.save_history(history,output_dir)
    print("Sauvegarde history!")

    print("____________________________________________")
    
    return model,history

def calculs_seuils(model, dataset_val, source="../data_filtrer.json"):
    """
    Calcule les seuils optimaux par genre à partir du dataset de validation,
    et les enregistre dans le fichier JSON.

    Sauvegarde dans le JSON : "seuils_optimaux" 

    Retourne :
        seuils, stats_seuils
    """
    print("___________ CALCULS_SEUILS ___________")

    data = bd.load_json(source)
    # Verification
    required_keys = ["liste_des_genres"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"ERREUR : La clé '{k}' manque dans {source}. ")
        
    if dataset_val is None:
        raise ValueError("ERREUR : dataset_val est None.")

    liste_des_genres = data["liste_des_genres"]

    seuils = t.finds_seuil_pour_chaque_theme(model,dataset_val,liste_des_genres)
    seuils_dict = { genre: float(seuils[i]) for i, genre in enumerate(liste_des_genres)}
    print("Seuils optimaux déterminés.")

    data["seuils_optimaux"] = seuils_dict
    bd.save_json(source, data)
    print("Mise à jour du json filtré.")
    print("____________________________________")

    return seuils

def evaluation(model, dataset_test, source="../data_filtrer.json"):
    """
    Évalue le modèle sur le dataset de test en utilisant les seuils optimaux enregistrés dans le JSON.

    Utilise :
        - "liste_des_genres"
        - "seuils_optimaux"

    Sauvegarde dans le JSON :
        - "resume_global"     
        - "stats_par_genre" 

    Retourne :
        resume_global, stats_par_genre
    """
    print("___________ EVALUATION ___________")

    data = bd.load_json(source)

    # Verification
    required_keys = ["liste_des_genres"]
    for k in required_keys:
        if k not in data:
            raise ValueError(f"ERREUR : La clé '{k}' manque dans {source}. ")
    if dataset_test is None:
        raise ValueError("ERREUR : dataset_test est None.")

    liste_des_genres = data["liste_des_genres"]

    seuils = data.get("seuils_optimaux", None)
    if seuils is None:
        raise ValueError("ERREUR : aucun seuil trouvé dans le json ")
    resume_global, stats_par_genre = t.evalution_du_model_avec_seuils(model,dataset_test,liste_des_genres,seuils)
    print("Évaluation finale terminée.")

    data["resume_global"]   = resume_global
    data["stats_par_genre"] = stats_par_genre
    bd.save_json(source, data)
    print("Mise à jour du json filtré.")
    print("____________________________________")
    return resume_global, stats_par_genre

def creation_courbe_from_history(output_dir="../model"):
    """
    Génère les courbes loss + AUC à partir de l’historique sauvegardé dans le dossier.
    """
    print("_________ COURBES D'ENTRAÎNEMENT _________")

    history = t.load_history(output_dir)
    if history is None:
        print("Erreur:Aucun historique trouvé.")
        print("__________________________________________")
        return
    paths = ts.creation_courbe_from_history(history, output_dir)
    print(f"Courbes générées dans : {output_dir}")
    print("__________________________________________")
    return paths




def clean_all(json_filter_path="../data_filtrer.json", img_dir_boost="../MoviePosters_boost",model_dir="../model"):
    """
    Supprime le fichier JSON, le dossier MoviePosters_boost et le dossier du model 
    """
    print("_____ CLEAN ALL_____")
    clean_data_filter(json_filter_path)
    clean_boost_dir(img_dir_boost)
    clean_model_dir(model_dir)
    print("__________________\n")

def clean_model_dir(model_dir="../model"):
    """
    Supprime le dossier du model 
    """
    print("_____ CLEAN MODEL DIR_____")
    
    if os.path.exists(model_dir):
        try:
            shutil.rmtree(model_dir)
            print(f"Dossier supprimé : {model_dir}")
        except Exception as e:
            print(f"Erreur suppression dossier du model : {e}")
    else:
        print(f"Aucun dossier du model à supprimer : {model_dir}")
    print("__________________\n")

def clean_boost_dir(img_dir_boost="../MoviePosters_boost"):
    """
    Supprime le dossier MoviePosters_boost
    """
    print("_____ CLEAN IMG DIR BOOST_____")
    
    if os.path.exists(img_dir_boost):
        try:
            shutil.rmtree(img_dir_boost)
            print(f"Dossier supprimé : {img_dir_boost}")
        except Exception as e:
            print(f"Erreur suppression dossier boost : {e}")
    else:
        print(f"Aucun dossier boost à supprimer : {img_dir_boost}")
    print("__________________\n")

def clean_data_filter(json_filter_path="../data_filtrer.json"):
    """
    Supprime le fichier JSON  
    """
    print("_____ CLEAN DATA FILTER_____")
    
    if os.path.exists(json_filter_path):
        try:
            os.remove(json_filter_path)
            print(f"Fichier supprimé : {json_filter_path}")
        except Exception as e:
            print(f"Erreur suppression fichier json : {e}")
    else:
        print(f"Aucun fichier json à supprimer : {json_filter_path}")
    print("__________________\n")



def prediction(model, use_per_class, images_pour_test, source_json):
    """
    Prédiction pour les tests.
    """
    data = bd.load_json(source_json)
    liste_des_genres = data.get("liste_des_genres")
    if not liste_des_genres:
        raise KeyError("Impossible de trouver 'liste_des_genres' dans le JSON source.")

    seuils_optimaux = None
    if use_per_class:
        seuils_optimaux = data.get("seuils_optimaux")

    y_pred, image_keys = t.predict_from_list(model, images_pour_test)

    preds_list = []
    for i, (key, base_name) in enumerate(image_keys):
        scores_vec = y_pred[i]

        scores_dict = {
            genre: float(scores_vec[j])
            for j, genre in enumerate(liste_des_genres)
        }

        preds_list.append({
            "image": key,
            "scores": scores_dict,
            "display_name": base_name
        })

    return preds_list, seuils_optimaux

def comparaison_repartition_train_avant_apres_boost(source):
    data = bd.load_json(source)

    liste_des_genres = data["liste_des_genres"]

    Y_avant = np.asarray(data["train_Y"])
    Y_boost = np.asarray(data["train_Y_boost"])

    repart_avant = ts.calculs_repartition_themes_vecteur(
        Y_avant, liste_des_genres, print_data=False,
        titre="Répartition train_Y AVANT boost"
    )

    if len(Y_boost) > 0:
        Y_apres = np.concatenate([Y_avant, Y_boost], axis=0)
    else:
        Y_apres = Y_avant

    repart_apres = ts.calculs_repartition_themes_vecteur(
        Y_apres, liste_des_genres, print_data=False,
        titre="Répartition train_Y APRES boost"
    )

    ts.comparaison_repartition(repart_avant, repart_apres, liste_des_genres)