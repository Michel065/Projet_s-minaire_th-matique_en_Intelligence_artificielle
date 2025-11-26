import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import build_data as bd


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
    vecteurs = np.asarray(vecteurs)
    if vecteurs.ndim != 2 or vecteurs.shape[1] != len(liste_des_genres):
        raise ValueError("Dimensions incompatibles entre Y et liste_des_genres, c'est louche !!")

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

def creation_courbe_accuracy_loss_from_hitory(history):
    # Accuracy
    plt.figure()
    plt.plot(history.get("accuracy", []), label="train acc")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Accuracy Entrainement")
    plt.grid(True)
    plt.legend()
    plt.savefig("courbe_accuracy.png", bbox_inches="tight")
    plt.close()

    # Loss
    plt.figure()
    plt.plot(history.get("loss", []), label="train loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Loss Entrainement")
    plt.grid(True)
    plt.legend()
    plt.savefig("courbe_loss.png", bbox_inches="tight")
    plt.close()
    print("Courbes sauvegardées : courbe_accuracy.png, courbe_loss.png")

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

def comparaison_repartition(repart_avant, repart_apres, liste_des_genres):
    """
    Affiche genre par genre :
    - pourcentage avant
    - pourcentage après
    - différence (+/-)
    """
    print("\n______ COMPARAISON AVANT / APRÈS BOOST ________")
    print(f"{'Genre':<20} {'Avant %':>10} {'Après %':>10} {'Diff %':>10}")

    for genre in liste_des_genres:
        if genre in repart_avant and genre in repart_apres:
            av = repart_avant[genre][0]
            ap = repart_apres[genre][0]
            diff = ap - av
            print(f"{genre:<20} {av:10.3f} {ap:10.3f} {diff:10.3f}")
    print("\n_____________________________________________")
