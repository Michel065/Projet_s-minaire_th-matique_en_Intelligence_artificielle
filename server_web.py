import os,sys
from flask import Flask, send_from_directory, jsonify, request
BASE_DIR = os.path.dirname(__file__)
WEB_DIR = os.path.join(BASE_DIR, "web")
sys.path.append(os.path.join(BASE_DIR, "image_vers_themes"))

import tool as tl

from ivt_session import IVTSession


CSV_PATH = "./MovieGenre.csv"
IMG_DIR  = "./MoviePosters/"
IMG_DIR_BOOST  = "./MoviePosters_boost"
MODEL_DIR  = "./Model"
MODEL_NAME  = "cnn"
JSON_FILTER = "./data_filtrer.json"

session = IVTSession(JSON_FILTER)

app = Flask(__name__,static_folder=WEB_DIR,static_url_path="")

# ================
#  PAGES HTML
# ================

@app.route("/")
def home():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/entrainement_ivt")
def page_entrainement_ivt():
    return send_from_directory(WEB_DIR, "entrainement_ivt.html")

# =========================
#  API : PREPROCESS / DATA
# =========================

@app.post("/api/construction_filter_json")
def api_construction_filter_json():
    """
    Bouton : construire data_filtrer.json
    Body JSON attendu: {csv_path, img_dir, output_source}
    """
    data = request.get_json() or {}
    csv_path = data.get("csv_path", CSV_PATH)
    img_dir = data.get("img_dir", IMG_DIR)

    try:
        tl.construction_filter_json(csv_path=csv_path,img_dir=img_dir,output_source=JSON_FILTER)
        return jsonify({"ok": True, "message": "data_filtrer.json construit"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/extraction_theme_rare")
def api_extraction_theme_rare():
    """
    Body: { seuil }
    """
    data = request.get_json() or {}
    seuil = float(data.get("seuil", 2.0))

    try:
        themes_rares = tl.extraction_theme_rare(source=JSON_FILTER, seuil=seuil, aff=False)
        return jsonify({"ok": True, "message": "Statut : Thèmes rares calculés","themes_rares":themes_rares}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/fusionner_other")
def api_fusionner_other():
    """
    Fusionne les genres trop rares en Other.
    Body: { seuil_min_count, nom_other }
    """
    data = request.get_json() or {}
    seuil_min_count = int(data.get("seuil_min_count", 100))
    nom_other = data.get("nom_other", "Other")

    try:
        themes_rares = tl.fusionner_genres_trop_rares_en_other(source=JSON_FILTER,seuil_min_count=seuil_min_count,nom_other=nom_other)
        return jsonify({"ok": True, "message": "Statut : Genres fusionnés en Other","themes_rares":themes_rares}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/split_train_val_test")
def api_split_train_val_test():
    """
    Body: { ratio_val, ratio_test }
    """
    data = request.get_json() or {}
    ratio_val = float(data.get("ratio_val", 0.15))
    ratio_test = float(data.get("ratio_test", 0.15))

    try:
        t_train,t_eval,t_test = tl.split_train_eval_test(source=JSON_FILTER,ratio_val=ratio_val,ratio_test=ratio_test)
        return jsonify({"ok": True, "message": "Statut : Split train/val/test effectué","data":[t_train,t_eval,t_test]}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/boost_train")
def api_boost_train():
    """
    Génère les images boostées sur le TRAIN uniquement.
    Body: {  img_dir_boost, max_variantes_par_image, facteur_cible }
    """
    data = request.get_json() or {}
    img_dir_boost = data.get("img_dir_boost", IMG_DIR_BOOST)
    max_var = int(data.get("max_variantes_par_image", 15))
    facteur_cible = float(data.get("facteur_cible", 0.5))

    try:
        nbr_ajout = tl.construire_data_boost_train(source=JSON_FILTER,img_dir_boost=img_dir_boost,max_variantes_par_image=max_var,facteur_cible=facteur_cible)
        return jsonify({"ok": True, "message": "Données boostées générées","nbr_ajout":nbr_ajout}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# =========================
#  API : ENTRAÎNEMENT / EVAL
# =========================
@app.post("/api/gen_datasets")
def api_gen_datasets():
    """
    Prépare les datasets (train/val/test) dans la session.
    Body: { batch_size, boost }
    """
    data = request.get_json() or {}
    batch_size = int(data.get("batch_size", 64))
    boost = bool(data.get("boost", True))

    try:
        session.generer_datasets(batch_size=batch_size, boost=boost)
        return jsonify({"ok": True, "message": "Datasets préparés (train/val/test)"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/train")
def api_train():
    """
    Lance entrainement
    Body: { EPOCHS, batch_size , model_dir , model_name }
    (Pour l'instant : appel bloquant)
    """
    data = request.get_json() or {}
    epochs = int(data.get("EPOCHS", 50))
    batch_size = int(data.get("batch_size", 64))
    boost = bool(data.get("boost", True))
    model_dir = data.get("model_dir", MODEL_DIR)
    model_name = data.get("model_name", MODEL_NAME)
    try:
        session.train(epochs=epochs,batch_size=batch_size,boost=boost,output_dir=model_dir,name_model=model_name)
        return jsonify({"ok": True, "message": "Entraînement terminé"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/api/train_status")
def api_train_status():
    try:
        train_status = session.load_train_status()
        return jsonify({"ok": True, "status": train_status}), 200
    except:
        return jsonify({"ok": False, "error": "Aucun entraînement en cours"}), 200

@app.post("/api/find_seuils")
def api_find_seuils():
    """
    Calcule les seuils par genre sur le dataset de validation.
    Body: {model_dir , model_name}
    """
    data = request.get_json() or {}
    model_dir = data.get("model_dir", MODEL_DIR)
    model_name = data.get("model_name", MODEL_NAME)
    try:
        session.compute_seuils(model_dir,model_name)
        return jsonify({"ok": True,"message": "Seuils calculés"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/eval_test")
def api_eval_test():
    """
    Évaluation sur dataset_test avec les seuils.
    Body: {}
    """
    try:
        results = session.eval_test_avec_seuils()
        return jsonify({"ok": True, "results": results}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/generate_graphs")
def api_generate_graphs():
    data = request.get_json() or {}
    model_dir  = data.get("model_dir", "../resultats/model")

    try:
        output_paths = tl.creation_courbe_from_history(model_dir)
        return jsonify({"ok": True, "message": "Courbes générées", "output_paths": output_paths}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# =========================
#  API : CLEAN
# =========================
@app.post("/api/clean_all")
def api_clean_all():
    """
    Juste on supp tout
    Body: {img_dir_boost , model_dir}
    """
    data = request.get_json() or {}
    img_dir_boost = data.get("img_dir_boost", IMG_DIR_BOOST)
    model_dir = data.get("model_dir", MODEL_DIR)
    try:
        tl.clean_all(JSON_FILTER,img_dir_boost,model_dir)
        return jsonify({"ok": True,"message": "Suppression terminée"}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/api/clean_filter")
def api_clean_filter():
    try:
        tl.clean_data_filter(json_filter_path=JSON_FILTER)
        return jsonify({"ok": True, "message": "data_filtrer.json supprimé."}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/clean_boost")
def api_clean_boost():
    data = request.get_json() or {}
    img_dir_boost = data.get("img_dir_boost", IMG_DIR_BOOST)
    try:
        tl.clean_boost_dir(img_dir_boost=img_dir_boost)
        return jsonify({"ok": True, "message": f"Dossier d’augmentation nettoyé ({img_dir_boost})."}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.post("/api/clean_model")
def api_clean_model():
    data = request.get_json() or {}
    model_dir = data.get("model_dir", MODEL_DIR)
    try:
        tl.clean_model_dir(model_dir=model_dir)
        return jsonify({"ok": True, "message": f"Dossier modèle nettoyé ({model_dir})."}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500












if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
