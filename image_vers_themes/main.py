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

#si on veux init l'augmentation de data
#ed.construire_data_boost(json_filter_path,img_dir_boost)

#t.clean()
#t.construction_filter_json()
#t.extraction_theme_rare()
#t.fusionner_genres_trop_rares_en_other()
#ts.calculs_repartition_themes_from_data_filter(source_y="Y_full",print_data=True)
#t.split_train_eval_test()
#t.construire_data_boost_train()

t.entrainement_complet(EPOCHS=2)