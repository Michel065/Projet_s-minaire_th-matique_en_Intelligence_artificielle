import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import build_data as bd
import os


def calculs_repartition_themes(liste_themes_par_image, liste_des_genres, titre="", print_data=False):
    """
    Calcule la répartition % de chaque thème à partir de la liste de thèmes par image.

    Retourne un dict : { theme: [pourcentage, count], ... }
    """
    # Conversion liste de thèmes
    Y = bd.convertisseur_themes_en_vecteur(liste_themes_par_image, liste_des_genres)
    repartition = calculs_repartition_themes_vecteur(Y, liste_des_genres,print_data=print_data, titre=titre)
    return repartition

def calculs_repartition_themes_vecteur(vecteurs, liste_des_genres, print_data=False,titre=""):
    """
    Calcule et (optionnellement) affiche la répartition (%) de chaque thème
    à partir du vecteur multi-hot.

    Retourne un dict : { theme: [pourcentage, count], ... }
    """
    #Vérif le nombre de dimensions
    vecteurs = np.asarray(vecteurs)
    if vecteurs.ndim != 2:
        raise ValueError(
            f"Dimensions incompatibles : vecteurs.ndim={vecteurs.ndim}, "
            f"vecteurs.shape={vecteurs.shape}, len(liste_des_genres)={len(liste_des_genres)}"
        )

    # Vérif le nombre de colonnes
    if vecteurs.shape[1] != len(liste_des_genres):
        raise ValueError(
            f"Dimensions incompatibles entre Y({vecteurs.shape[1]}) "
            f"et liste_des_genres({len(liste_des_genres)}), c'est louche !!"
        )
    
    # On compte le nombre d'occurrences par thème
    counts = vecteurs.sum(axis=0)
    total = counts.sum()

    if total == 0:
        if print_data:
            print("Aucune donnée trouvée.")
        return {}

    repartition = {}
    for genre, count in zip(liste_des_genres, counts):
        pourcentage = float(count / total * 100)
        repartition[genre] = [pourcentage, int(count)]

    if print_data:
        if titre != "":
            print(titre)
        else:
            print("\nRépartition des thèmes :")

        for genre, count in sorted(zip(liste_des_genres, counts), key=lambda x: x[1], reverse=True):
            pourcentage = repartition[genre][0]
            print(f" - {genre:<20}: {pourcentage:6.3f}% ({int(count)})")

    return repartition

def construire_index_genres_vecteur(vecteurs, liste_des_genres):
    """
    À partir d'un vecteur multi-hot et de la liste_des_genres,
    renvoie:
      - counts
      - dico_genre_vers_idx { genre: [indices_images] }
    """
    vecteurs = np.asarray(vecteurs)
    if vecteurs.ndim != 2 or vecteurs.shape[1] != len(liste_des_genres):
        raise ValueError("Dimensions incompatibles entre Y et liste_des_genres, c'est louche !!")

    nb_images = vecteurs.shape[0]
    counts = vecteurs.sum(axis=0)

    dico_genre_vers_idx = {genre: [] for genre in liste_des_genres}
    for idx_img in range(nb_images):
        row = vecteurs[idx_img]
        for j, val in enumerate(row):
            if val == 1:
                genre = liste_des_genres[j]
                dico_genre_vers_idx[genre].append(idx_img)

    return counts, dico_genre_vers_idx

def creation_courbe_from_history(history,output_dir="../model", output_prefix="courbe"):
    """
    Génère 2 courbes à partir de l'historique d'entraînement :

      1. Loss (train / val)
      2. AUC (ROC & PR, train / val)

    Sauvegarde :
      - <output_dir>/<output_prefix>_loss.png
      - <output_dir>/<output_prefix>_auc.png
    """

    if isinstance(history, dict):
        epochs      = list(range(1, len(history.get("loss", [])) + 1))
        loss        = history.get("loss", [])
        val_loss    = history.get("val_loss", [])
        auc_roc     = history.get("auc_roc", [])
        val_auc_roc = history.get("val_auc_roc", [])
        auc_pr      = history.get("auc_pr", [])
        val_auc_pr  = history.get("val_auc_pr", [])
    else:
        raise TypeError("history doit être un dict.")

    path_loss=os.path.join(output_dir, f"{output_prefix}_loss.png")
    path_ARP=os.path.join(output_dir, f"{output_prefix}_auc.png")

    # --------- Courbe de loss ---------
    plt.figure()
    if loss:
        plt.plot(epochs[:len(loss)], loss, label="train loss")
    if val_loss:
        plt.plot(epochs[:len(val_loss)], val_loss, label="val loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Loss entraînement")
    plt.grid(True)
    plt.legend()
    plt.savefig(path_loss, bbox_inches="tight")
    plt.close()

    # --------- Courbe AUC (ROC + PR) ----------
    plt.figure()
    if auc_roc:
        plt.plot(epochs[:len(auc_roc)], auc_roc, label="train AUC ROC")
    if val_auc_roc:
        plt.plot(epochs[:len(val_auc_roc)], val_auc_roc, label="val AUC ROC")

    if auc_pr:
        plt.plot(epochs[:len(auc_pr)], auc_pr, label="train AUC PR")
    if val_auc_pr:
        plt.plot(epochs[:len(val_auc_pr)], val_auc_pr, label="val AUC PR")

    plt.xlabel("Epoch")
    plt.ylabel("AUC")
    plt.title("AUC ROC / PR")
    plt.grid(True)
    plt.legend()
    plt.savefig(path_ARP, bbox_inches="tight")
    plt.close()
    print(f"Courbes sauvegardées : {output_prefix}_loss.png, {output_prefix}_auc.png")
    return (path_loss,path_ARP)

def print_nbr_param_model(model):
    liste=list([(v.shape) for v in model.trainable_weights])
    nbr_param=0
    for elt in liste:
        tmp=1
        for i in elt:
            tmp*=i
        nbr_param+=tmp
    print("nbr de param possible", nbr_param)
    
def print_summary_model(model):
    model.summary()

def comparaison_repartition(repart_avant, repart_apres, liste_des_genres,titre="Train"):
    """
    Affiche genre par genre :
    - pourcentage avant
    - pourcentage après
    - différence (+/-)
    """
    print(f"\n______ COMPARAISON AVANT / APRÈS BOOST {titre} ________")
    print(f"{'Genre':<20} {'Avant %':>10} {'Après %':>10} {'Diff %':>10}")

    lignes = []
    for genre in liste_des_genres:
        if genre in repart_avant and genre in repart_apres:
            av = repart_avant[genre][0]
            ap = repart_apres[genre][0]
            diff = ap - av
            lignes.append((genre, av, ap, diff))

    lignes.sort(key=lambda x: x[2], reverse=True) 
    for genre, av, ap, diff in lignes:
        print(f"{genre:<20} {av:10.3f} {ap:10.3f} {diff:+10.3f}")

    print("\n_____________________________________________")

def calculs_repartition_themes_from_data_filter(source="../data_filtrer.json",source_y="Y_full", titre="", print_data=False):
    """
    Calcule la répartition % de chaque thème à partir de la liste de thèmes par image mais a partir du json.

    Retourne un dict : { theme: [pourcentage, count], ... }
    """
    data = bd.load_json(source)
    Y = data[source_y]
    liste_des_genres = data["liste_des_genres"]
    repartition = calculs_repartition_themes_vecteur(Y, liste_des_genres,print_data=print_data, titre=titre)
    return repartition

