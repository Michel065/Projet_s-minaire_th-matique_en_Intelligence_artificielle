import tensorflow as tf
from tensorflow.keras import mixed_precision
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np
from time import time
import os
import json

import WebLogCallback as w

def define_startegie(build_model,param_model): #=((268,182,3),28)
    mixed_precision.set_global_policy("mixed_float16") # conseil de chat pour optimiser
    strategy = tf.distribute.get_strategy()   
    with strategy.scope():
        model = build_model(param_model)  
        model.compile(#recup dans le cours d'apprentissage données massive
            loss=tf.keras.losses.BinaryCrossentropy(from_logits=False),
            optimizer = tf.keras.optimizers.Adam(learning_rate=1e-4),
            metrics=[
                tf.keras.metrics.AUC(curve="ROC", multi_label=True, name="auc_roc"),
                tf.keras.metrics.AUC(curve="PR",  multi_label=True, name="auc_pr"),
            ],
        )
    return model

def train_model(model,dataset_train,dataset_val,EPOCHS = 50,output_dir="../model"):
    """
    fonction pour train un model, beaucoup de partie recupere dans un autre cours

    Args:
        model:le model 
        dataset_train: donnees d'entrainement
        dataset_val: pour la validation et lacorection en cours de route
        EPOCHS: nbr de passage sur le dataset 

    Returns:
        hitory: l'historique pour faire des graphs
    """
    callbacks = [ #recup dans le cours d'apprentissage données massive
        EarlyStopping(monitor="val_auc_pr", patience=5, mode="max", restore_best_weights=True),
        ModelCheckpoint(
            filepath="best_model.keras",
            monitor="val_auc_pr",
            mode="max",
            save_best_only=True,
            verbose=1
        ),
        w.WebLogCallback(EPOCHS,output_dir),
    ]


    t0 = time()
    history = model.fit(dataset_train,validation_data=dataset_val,epochs=EPOCHS,callbacks=callbacks,verbose=1)
    tt = time() - t0

    h = int(tt // 3600)
    m = int((tt % 3600) // 60)
    s = int(tt % 60)
    print(f"Temps d'entraînement: {h} h {m} min {s} s")
    return history,model

def finds_seuil_pour_chaque_theme(model, dataset_val, liste_des_genres,nb_steps=19, t_min=0.05, t_max=0.95,aff=True):
    """
    Calcule un seuil optimal (par genre) sur le dataset de validation,
    en maximisant le F1-score par classe.

    Args:
        model
        dataset_val
        liste_des_genres
        nb_steps: nombre de seuils testés.
        t_min, t_max: les bornes.
        aff

    Returns:
        seuils_opt
    """

    y_true_list = []
    y_pred_list = []

    for batch_x, batch_y in dataset_val:
        y_true_list.append(batch_y.numpy())
        # prédiction sur le batch
        y_pred_batch = model.predict_on_batch(batch_x)
        y_pred_list.append(y_pred_batch)

    y_true = np.concatenate(y_true_list, axis=0)   # on convertie en tableau numpy pour aller plu vite
    y_pred = np.concatenate(y_pred_list, axis=0)

    _, nb_classes = y_true.shape#on verifie que ca à marché
    assert nb_classes == len(liste_des_genres), "Dimensions Y / liste_des_genres incohérentes."

    #ce qu'on teste:
    seuils_grid = np.linspace(t_min, t_max, nb_steps)

    seuils_opt = np.zeros(nb_classes, dtype=np.float32)
    #Pour chaque classe, on cherche le seuil qui maximise le F1
    for j in range(nb_classes):
        yt = y_true[:, j] #on recup la colone donc le genre que l'on traite
        yp = y_pred[:, j]

        best_f1 = -1.0
        best_t = 0.5
        # si la classe n'apparaît jamais, on garde un seuil par défaut donc 0.5
        yt_sum = yt.sum()
        if yt_sum == 0:
            seuils_opt[j] = best_t
            continue

        for t in seuils_grid:
            yp_bin = (yp >= t).astype(int)

            TP = np.sum((yt == 1) & (yp_bin == 1)) # vrai Positif
            FP = np.sum((yt == 0) & (yp_bin == 1)) # Faux Positif
            FN = np.sum((yt == 1) & (yp_bin == 0)) # Faux Negatif

            denominateur = (2 * TP + FP + FN)
            if denominateur == 0:
                f1 = 0.0
            else:
                f1 = 2 * TP / denominateur

            if f1 > best_f1:
                best_f1 = f1
                best_t = t

        seuils_opt[j] = best_t

        if aff:
            print(f"[{liste_des_genres[j]:<20}] nombre d'aparition={int(yt_sum):5d}  best_t={best_t:.3f}  best_F1={best_f1:.3f}")

    return seuils_opt

def evalution_du_model(model, dataset_test):
    """
    Évaluation standard Keras (loss + métriques compilées).
    """
    results = model.evaluate(dataset_test, return_dict=True)
    print("Résultat après évaluation Keras :")
    for k, v in results.items():
        print(f"{k}: {v:.4f}")
    return results

def evalution_du_model_avec_seuils(model, dataset_test, liste_des_genres, seuils):
    """
    Évaluation complète multi-label en appliquant un seuil par genre.
    - Calcule F1 micro / macro global
    - Calcule F1 / précision / rappel par genre

    LÉGENDE DES MÉTRIQUES:
        -TP  (True Positive)  : vrai positif (bonne détection du genre)
        -FP  (False Positive) : faux positif (erreur : genre prédit alors qu’il n’apparaît pas)
        -FN  (False Negative) : faux négatif (oubli du genre)
        -Support              : nombre d’images ou ce genre est réellement présent
        -Precision            : la proportion qui est correcte 
        -Recall               : proportion des vrais cas détectés
        -F1                   : équilibre entre FP et FN
        -Seuil                : probabilité de detection
    """
    print("_____ EVALUATION AVEC SEUILS PAR GENRE _____")
    #on fait pareil que dans finds_seuil_pour_chaque_theme
    y_true_list = []
    y_pred_list = []
    for batch_x, batch_y in dataset_test:
        y_true_list.append(batch_y.numpy())
        y_pred_batch = model.predict_on_batch(batch_x)
        y_pred_list.append(y_pred_batch)
    y_true = np.concatenate(y_true_list, axis=0)  # (N, K)
    y_pred = np.concatenate(y_pred_list, axis=0)  # (N, K)

    _, nb_classes = y_true.shape
    seuils = np.asarray(seuils).reshape(1, -1)
    assert nb_classes == len(liste_des_genres) == seuils.shape[1], "Dimensions Y / genres / seuils incohérentes."

    #on utilise nos seuils cette fois
    y_pred_bin = (y_pred >= seuils).astype(int)

    #F1 micro global
    # on convertie en un vecteur 1D pour faciliter le caculs des micro
    yt_flat = y_true.ravel()
    yp_flat = y_pred_bin.ravel()

    TP_micro = np.sum((yt_flat == 1) & (yp_flat == 1))
    FP_micro = np.sum((yt_flat == 0) & (yp_flat == 1))
    FN_micro = np.sum((yt_flat == 1) & (yp_flat == 0))

    denom_micro = 2 * TP_micro + FP_micro + FN_micro
    if denom_micro == 0:
        f1_micro = 0.0
    else:
        f1_micro = 2 * TP_micro / denom_micro

    #F1 macro et stats
    f1_par_classe = []
    stats_par_genre = {}

    print("\n____STATISTIQUES_PAR_GENRE____")
    print(f"{'Genre':<20} {'Seuil':>7} {'F1':>7} {'Prec':>7} {'Rec':>7} {'Support':>8}")

    for j, genre in enumerate(liste_des_genres):
        yt = y_true[:, j]
        yp = y_pred_bin[:, j]

        TP = np.sum((yt == 1) & (yp == 1))
        FP = np.sum((yt == 0) & (yp == 1))
        FN = np.sum((yt == 1) & (yp == 0))

        support_pos = int(yt.sum())

        # précision
        denom_prec = TP + FP
        precision = TP / denom_prec if denom_prec > 0 else 0.0

        # rappel
        denom_rec = TP + FN
        recall = TP / denom_rec if denom_rec > 0 else 0.0

        # F1
        denom_f1 = 2 * TP + FP + FN
        f1 = 2 * TP / denom_f1 if denom_f1 > 0 else 0.0

        f1_par_classe.append(f1)
        stats_par_genre[genre] = {
            "seuil": float(seuils[0, j]),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "support": support_pos,
        }

        print(f"{genre:<20} {seuils[0,j]:7.3f} {f1:7.3f} {precision:7.3f} {recall:7.3f} {support_pos:8d}")

    f1_macro = float(np.mean(f1_par_classe)) if len(f1_par_classe) > 0 else 0.0

    print("\n--- METRIQUES GLOBALES ---")
    print(f"F1 micro  : {f1_micro:.4f}")
    print(f"F1 macro  : {f1_macro:.4f}")
    print("___________________________________________")

    resume_global = {
        "f1_micro": f1_micro,
        "f1_macro": f1_macro,
    }
    return resume_global, stats_par_genre

def save_model_entier(model, dossier="save_model", nom="model_final_image_vers_themes"):
    os.makedirs(dossier, exist_ok=True)
    chemin_modele = os.path.join(dossier, f"{nom}.keras")
    model.save(chemin_modele)
    print(f"Modèle sauvegardé dans : {chemin_modele}")

def load_model(nom_model="best_model", dossier="save_model"):
    chemin_modele = os.path.join(dossier, f"{nom_model}.keras")
    return tf.keras.models.load_model(chemin_modele, compile=True)

def save_history(history,output_dir="./models", name="history"):
    """
    Sauvegarde l'historique d'entraînement.
    """
    hist_dict = history.history
    os.makedirs(output_dir, exist_ok=True)
    chemin_hist = os.path.join(output_dir, f"{name}.json")

    with open(chemin_hist, "w", encoding="utf-8") as f:
        json.dump(hist_dict, f, ensure_ascii=False, indent=2)

    print(f"Historique d'entraînement sauvegardé dans '{chemin_hist}'.")

def load_history(output_dir="./models", name="history"):
    """
    Charge l'historique.
    """
    chemin_hist = os.path.join(output_dir, f"{name}.json")
    if not os.path.exists(chemin_hist):
        print(f"load_history : fichier '{chemin_hist}' introuvable.")
        return None

    with open(chemin_hist, "r", encoding="utf-8") as f:
        hist_dict = json.load(f)

    print(f"Historique d'entraînement chargé depuis '{chemin_hist}'.")
    return hist_dict

def load_train_status(output_dir="./models"):
    """
    Charge train_status.
    """
    chemin_hist = os.path.join(output_dir, "train_status.json")
    if not os.path.exists(chemin_hist):
        print(f"load_train_status : fichier '{chemin_hist}' introuvable.")
        return None
    with open(chemin_hist, "r", encoding="utf-8") as f:
        train_status = json.load(f)

    print(f"Train_status chargé depuis '{chemin_hist}'.")
    return train_status