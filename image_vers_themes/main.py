import build_data as bd
import build_model as bm
import tool as t
import train as tr
import tool_stats as ts
import extend_data as ed
import numpy as np
import os

csv_path = "../MovieGenre.csv"
img_dir  = "../MoviePosters/"

json_filter_path = "../data_filtrer.json"
img_dir_boost  = "../MoviePosters_boost"

model = tr.load_model("model_pvt", "../resultat_pvt/")

def corriger_chemins(liste_X, json_path):
    base_dir = os.path.dirname(os.path.abspath(json_path))
    return [os.path.normpath(os.path.join(base_dir, x)) for x in liste_X]

def generer_dataset_test_only(source="../data_filtrer.json", batch_size=64):
    data = bd.load_json(source)

    test_X = corriger_chemins(data["test_X"], source)
    test_Y = np.asarray(data["test_Y"])

    return bd.creation_dataset(test_X, test_Y, batch_size=batch_size, shuffle=False)

model = tr.load_model("model_pvt", "../resultat_pvt/")

dataset_test = generer_dataset_test_only(json_filter_path, batch_size=64)

results = tr.evalution_du_model(model, dataset_test)

print("resume_global:", results)
"""
#si on veux init l'augmentation de data
#ed.construire_data_boost(json_filter_path,img_dir_boost)

#t.clean()
#t.construction_filter_json()
#t.extraction_theme_rare()
#t.fusionner_genres_trop_rares_en_other()
#ts.calculs_repartition_themes_from_data_filter(source_y="Y_full",print_data=True)
#t.split_train_eval_test()
#t.construire_data_boost_train()

print("generer_datasets:")
dataset_train, dataset_val, dataset_test = t.generer_datasets()
print("entrainement:")
model, history = t.entrainement(dataset_train, dataset_val,EPOCHS=2)
print("calculs_seuils:")
seuils = t.calculs_seuils(model,dataset_val)
print("seuil:",seuils)
print("")
print("evaluation:")
resume_global, stats_par_genre = t.evaluation(model,dataset_test)
print("resume_global:",resume_global)
print("")
print("stats_par_genre:",stats_par_genre)
"""
