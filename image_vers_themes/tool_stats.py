import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def calculs_repartition_themes(liste_themes_par_image,titre=""):
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
    if(titre!=""):
        print(titre)
    else:
        print("Répartition des thèmes:")
    
    for theme, count in sorted(dico.items(), key=lambda x: x[1], reverse=True):
        pourcentage = (count / total) * 100
        print(f" - {theme:<20}: {pourcentage:.3f}% ({count})")

def calculs_repartition_themes_Y(Y, liste_des_genres,titre=""):
    """
    Calcule et affiche la répartition (%) de chaque thème à partir du vecteur multi-hot Y.
    
    Args:
        Y (np.ndarray): tableau (N x K) contenant les étiquettes multi-hot.
        liste_des_genres (list[str]): noms des thèmes correspondant aux colonnes de Y.
    """
    Y = np.asarray(Y)
    if Y.ndim != 2 or Y.shape[1] != len(liste_des_genres):
        raise ValueError("Dimensions incompatibles entre Y et liste_des_genres.")

    #On Compte
    counts = Y.sum(axis=0)
    total = counts.sum()

    if total == 0:
        print("Aucune donnée trouvée.")
        return

    if(titre!=""):
        print(titre)
    else:
        print("\nRépartition des thèmes à partir de Y :")
    for genre, count in sorted(zip(liste_des_genres, counts), key=lambda x: x[1], reverse=True):
        pourcentage = (count / total) * 100
        print(f" - {genre:<20}: {pourcentage:6.3f}% ({int(count)})")

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