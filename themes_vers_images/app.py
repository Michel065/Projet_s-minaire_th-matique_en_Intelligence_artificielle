import os
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv; load_dotenv()


from service import generate_from_themes, analyze_poster



app = Flask(__name__)

# Dossier où on sauvegardera les images uploadées pour analyse
UPLOAD_FOLDER = "data/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- Page HTML simple ----------

INDEX_HTML = """
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Thèmes & Affiches - Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 20px auto; }
        h1 { margin-bottom: 0.2em; }
        form { margin-bottom: 2em; padding: 1em; border: 1px solid #ddd; border-radius: 8px; }
        .results { margin-top: 1em; }
        img { max-height: 250px; margin-right: 10px; margin-bottom: 10px; border: 1px solid #ccc; }
        .poster-container { display: flex; flex-wrap: wrap; }
        label { display: block; margin-bottom: 0.4em; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 0.4em; }
        input[type="submit"] { padding: 0.5em 1em; }
        ul { padding-left: 1.2em; }
    </style>
</head>
<body>

<h1>Demo - Thèmes & Affiches</h1>
<p>Tu peux soit générer des affiches à partir de thèmes (baseline), soit analyser une affiche existante.</p>

<hr>

<h2>1. Thèmes → Affiches (baseline)</h2>
<form method="post" action="/generate_from_themes">
    <label for="themes">Thèmes (ex: "action, horreur, drame") :</label>
    <input type="text" id="themes" name="themes" placeholder="action, horreur, drame" required>
    <br><br>
    <label for="top_k">Nombre de résultats (top_k) :</label>
    <input type="number" id="top_k" name="top_k" value="3" min="1" max="10">
    <br><br>
    <input type="submit" value="Générer (baseline)">
</form>

{% if gen_result %}
<div class="results">
  <h3>Résultats - Thèmes → Affiches</h3>
  <p><strong>Thèmes saisis :</strong> {{ gen_result.input_themes }}</p>
  <p><strong>Mode :</strong> {{ gen_result.mode }} — {{ gen_result.message }}</p>
  <div class="poster-container">
  {% for p in gen_result.posters %}
    {% if p is string %}
      {% set path = p %}
    {% elif p is sequence and p|length > 2 %}
      {% set path = p[2] %}
    {% else %}
      {% set path = p %}
    {% endif %}
    <div>
      <img src="{{ url_for('serve_file', filepath=path) }}" alt="poster">
      <div style="font-size: 0.8em;">{{ path }}</div>
    </div>
  {% endfor %}
  </div>
</div>
{% endif %}



<hr>

<h2>2. Affiche → Thèmes (analyse CLIP)</h2>
<form method="post" action="/analyze_poster" enctype="multipart/form-data">
    <label for="poster">Choisis une affiche (fichier .jpg / .png) :</label>
    <input type="file" id="poster" name="poster" accept="image/*" required>
    <br><br>
    <label for="top_k2">Top-k thèmes à afficher :</label>
    <input type="number" id="top_k2" name="top_k" value="5" min="1" max="10">
    <br><br>
    <input type="submit" value="Analyser l'affiche">
</form>

{% if an_result %}
<div class="results">
    <h3>Résultats - Affiche → Thèmes</h3>
    <img src="{{ url_for('serve_file', filepath=an_result.image_path) }}" alt="uploaded poster">
    <h4>Top thèmes détectés :</h4>
    <ul>
    {% for item in an_result.top_k %}
        <li>{{ item.genre }} — score: {{ "%.3f"|format(item.score) }}</li>
    {% endfor %}
    </ul>
</div>
{% endif %}

<hr>
<p style="font-size: 0.8em; color: #777;">
Serveur de démo pour ton projet IA - thèmes & affiches.
</p>

</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    # Affiche juste la page sans résultats
    return render_template_string(INDEX_HTML, gen_result=None, an_result=None)


@app.route("/generate_from_themes", methods=["POST"])
def route_generate_from_themes():
    themes = request.form.get("themes", "").strip()
    top_k_str = request.form.get("top_k", "3")

    try:
        top_k = int(top_k_str)
    except ValueError:
        top_k = 3

    try:
        # HF -> pré-généré -> baseline (géré côté service/routeur)
        result = generate_from_themes(themes, top_k=top_k)
    except Exception as e:
        return f"Erreur lors de la génération : {e}", 400

    return render_template_string(INDEX_HTML, gen_result=result, an_result=None)



@app.route("/analyze_poster", methods=["POST"])
def route_analyze_poster():
    if "poster" not in request.files:
        return "Aucun fichier reçu.", 400

    file = request.files["poster"]
    if file.filename == "":
        return "Nom de fichier vide.", 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    top_k_str = request.form.get("top_k", "5")
    try:
        top_k = int(top_k_str)
    except ValueError:
        top_k = 5

    try:
        result = analyze_poster(save_path, top_k=top_k)
    except Exception as e:
        return f"Erreur lors de l'analyse : {e}", 400

    # On réaffiche la page avec an_result rempli
    return render_template_string(INDEX_HTML, gen_result=None, an_result=result)


# ---------- Servir les fichiers d'images (posters + uploads) ----------

@app.route("/files/<path:filepath>")
def serve_file(filepath: str):
    """
    Sert un fichier image à partir du projet.
    Exemple: data/posters/331834.jpg
    """
    # On renvoie depuis le répertoire courant du projet
    directory = os.path.abspath(".")
    full_path = os.path.join(directory, filepath)

    if not os.path.exists(full_path):
        return f"Fichier introuvable: {filepath}", 404

    # dirname = dossier contenant le fichier, filename = nom
    dirname, filename = os.path.split(full_path)
    return send_from_directory(dirname, filename)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Pour le développement local
    app.run(host="127.0.0.1", port=5000, debug=True)
