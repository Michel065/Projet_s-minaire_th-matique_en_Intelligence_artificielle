import build_data as bd
import build_model as bm
import train as t
import tool_stats as ts


csv_path = "../MovieGenre.csv"
img_dir  = "../MoviePosters/"

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

def boucle_entrainement_load():
    print("Extraction des couples (lien, thèmes) + liste des genres.")
    liste_liens_image, liste_themes_par_image, liste_des_genres = bd.construction_tuple_image_themes(csv_path, img_dir)
    print("Conversion des thèmes en vecteurs binaires.")
    Y = bd.convertisseur_themes_en_vecteur(liste_themes_par_image, liste_des_genres)
    print("Split train/val/test.")
    (_, _), (_, _), (test_X_liens, test_Y) = bd.partage_les_datas(liste_liens_image, Y)
    print("Création du dataset de test.")
    batch_size = 64
    dataset_test = bd.creation_dataset(test_X_liens, test_Y, batch_size)
    print("Chargement du modèle.")
    model = t.load_model("./best_model.keras")
    print("Évaluation du modèle.")
    t.evalution_du_model(model, dataset_test)

def secondaire():
    model = bm.build_model()
    ts.print_summary_model(model)


boucle_entrainement_complet()
