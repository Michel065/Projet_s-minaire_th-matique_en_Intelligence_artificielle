import os
import sys
from flask import Blueprint, request, jsonify, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv; load_dotenv()

# dossier racine du projet
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# on ajoute themes_vers_images dans le PYTHONPATH
sys.path.append(os.path.join(BASE_DIR, "themes_vers_images"))

from service import generate_from_themes, analyze_poster



# Blueprint au lieu d'une app Flask
clip_bp = Blueprint("clip_bp", __name__)

# Dossier où on sauvegardera les images uploadées pour analyse
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Genres proposés dans l’interface (à adapter si besoin)
AVAILABLE_GENRES = [
    "action", "aventure", "animation", "comédie", "crime", "documentaire",
    "drame", "fantasy", "familial", "guerre", "historique", "horreur",
    "musique", "mystère", "romance", "science-fiction", "thriller",
    "western", "biopic", "film noir", "réalité", "sport"
]

FR_TO_EN = {
    "action": "action",
    "horreur": "horror",
    "comédie": "comedy",
    "comedie": "comedy",
    "drame": "drama",
    "aventure": "adventure",
    "aventura": "adventure",  # pour ton ancienne clé
    "science-fiction": "scifi",
    "science fiction": "scifi",
    "sf": "scifi",
    "fantasy": "fantasy",
    "crime": "crime",
    "famille": "family",
    "familial": "family",
    "musique": "music",
    "historique": "history",
    "histoire": "history",
    "guerre": "war",
    "western": "western",
    "mystère": "mystery",
    "mystere": "mystery",
    "documentaire": "documentary",
    "téléréalité": "realitytv",
    "tele-realite": "realitytv",
    "réalité": "realitytv",
    "reality": "realitytv",
    "sport": "sport",
    "film noir": "filmnoir",
    "talk-show": "talkshow",
    "talkshow": "talkshow",
    "court métrage": "short",
    "court metrage": "short",
    "biopic": "biography",
    "biographie": "biography",
    "romance": "romance",  # identique ici
}


# ---------- Page HTML simple ----------

INDEX_HTML = """
<!doctype html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <title>Thèmes ⇒ Affiches</title>
    <style>
        :root {
            --bg: #050816;
            --bg-elevated: #0b1120;
            --bg-soft: #111827;
            --border-subtle: #1f2937;
            --accent: #3b82f6;
            --accent-soft: rgba(59,130,246,0.15);
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --pill-bg: #111827;
            --pill-border: #374151;
            --poster-bg: #020617;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                         sans-serif;
            background: radial-gradient(circle at top left, #1e293b 0, #020617 45%, #020617 100%);
            color: var(--text-main);
        }

        .tvi-page {
            max-width: 1280px;
            margin: 0 auto;
            padding: 32px 24px 40px;
        }

        .tvi-header {
            margin-bottom: 32px;
        }

        .tvi-back {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.9rem;
            color: var(--text-muted);
            text-decoration: none;
            margin-bottom: 8px;
            padding: 2px 0;
        }
        .tvi-back:hover {
            color: var(--accent);
        }

        .tvi-title {
            font-size: 1.8rem;
            font-weight: 600;
            letter-spacing: 0.03em;
        }

        .tvi-subtitle {
            margin-top: 8px;
            font-size: 0.95rem;
            color: var(--text-muted);
        }

        .tvi-main {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.3fr);
            gap: 24px;
        }

        @media (max-width: 900px) {
            .tvi-main {
                grid-template-columns: minmax(0, 1fr);
            }
        }

        .tvi-panel {
            background: linear-gradient(145deg, var(--bg-elevated), var(--bg-soft));
            border-radius: 16px;
            border: 1px solid var(--border-subtle);
            padding: 20px 20px 18px;
            box-shadow: 0 18px 45px rgba(15,23,42,0.45);
        }

        .tvi-panel h2 {
            font-size: 1.1rem;
            margin: 0 0 4px;
            font-weight: 600;
        }

        .tvi-panel-sub {
            margin: 0 0 16px;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        /* Genre pills */

        .tvi-genres {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
            max-height: 148px;
            overflow-y: auto;
            padding-right: 4px;
        }

        .tvi-genre-pill {
            border-radius: 999px;
            border: 1px solid var(--pill-border);
            background: var(--pill-bg);
            color: var(--text-main);
            font-size: 0.8rem;
            padding: 6px 10px;
            cursor: pointer;
            transition: background 0.15s ease, border-color 0.15s ease,
                        transform 0.08s ease;
            white-space: nowrap;
        }
        .tvi-genre-pill:hover {
            background: #1f2937;
            border-color: var(--accent);
            transform: translateY(-1px);
        }
        .tvi-genre-pill:active {
            transform: translateY(0);
        }

        /* Formulaire */

        .tvi-form {
            margin-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .tvi-label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 4px;
        }

        .tvi-input {
            width: 100%;
            border-radius: 10px;
            border: 1px solid var(--pill-border);
            background: #020617;
            color: var(--text-main);
            padding: 10px 11px;
            font-size: 0.9rem;
        }
        .tvi-input::placeholder {
            color: #4b5563;
        }
        .tvi-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 1px rgba(59,130,246,0.6);
        }

        .tvi-form-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-top: 4px;
        }

        .tvi-small-input {
            width: 80px;
        }

        .tvi-hint {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .tvi-button {
            border: none;
            border-radius: 999px;
            padding: 9px 18px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: white;
            box-shadow: 0 12px 25px rgba(37,99,235,0.4);
            transition: transform 0.08s ease, box-shadow 0.08s ease,
                        filter 0.12s ease;
            white-space: nowrap;
        }
        .tvi-button:hover {
            filter: brightness(1.05);
            box-shadow: 0 16px 40px rgba(37,99,235,0.5);
            transform: translateY(-1px);
        }
        .tvi-button:active {
            transform: translateY(0);
            box-shadow: 0 10px 24px rgba(37,99,235,0.35);
        }

        /* Panneau résultats */

        .tvi-results-header {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
        }

        .tvi-results-header h2 {
            margin: 0;
        }

        .tvi-results-meta {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .tvi-placeholder {
            font-size: 0.9rem;
            color: var(--text-muted);
            padding: 12px 0 6px;
        }

        .tvi-result-summary {
            font-size: 0.85rem;
            margin-bottom: 12px;
            color: var(--text-muted);
        }

        .tvi-tags {
            display: inline-flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-left: 4px;
        }

        .tvi-tag {
            background: var(--accent-soft);
            color: var(--accent);
            border-radius: 999px;
            padding: 3px 9px;
            font-size: 0.8rem;
        }

        .tvi-posters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 24px;
}


        .tvi-poster-card {
            background: var(--poster-bg);
            border-radius: 14px;
            border: 1px solid #111827;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            min-height: 0;
        }

        .tvi-poster-card img {
            width: 100%;
            display: block;
            object-fit: cover;
            background: #020617;
        }

        .tvi-poster-meta {
            padding: 6px 8px 7px;
            font-size: 0.75rem;
            color: var(--text-muted);
            border-top: 1px solid #111827;
        }

        .tvi-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 999px;
            background: rgba(148,163,184,0.2);
            color: #e5e7eb;
            font-size: 0.7rem;
            margin-bottom: 4px;
        }

        .tvi-path {
            word-break: break-all;
        }

        .tvi-footer-note {
            margin-top: 12px;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
<div class="tvi-page">
    <header class="tvi-header">
        <a href="/" class="tvi-back">← Retour à la console</a>
        <h1 class="tvi-title">Thèmes ⇒ Affiches</h1>
        <p class="tvi-subtitle">
            Compose un ensemble de genres et laisse le système proposer des affiches correspondantes.
        </p>
    </header>

    <main class="tvi-main">
        <!-- COLONNE GAUCHE : sélection des thèmes -->
        <section class="tvi-panel">
            <h2>1. Sélection des thèmes</h2>
            <p class="tvi-panel-sub">
                Clique sur les genres ci-dessous ou saisis-les manuellement, séparés par des virgules.
            </p>

            <div class="tvi-genres">
                {% for g in available_genres %}
                <button type="button" class="tvi-genre-pill" onclick="addGenre('{{ g }}')">
                    {{ g }}
                </button>
                {% endfor %}
            </div>

            <form method="post"
                  action="{{ url_for('clip_bp.route_generate_from_themes') }}"
                  class="tvi-form">
                <div>
                    <label for="themes" class="tvi-label">Thèmes sélectionnés</label>
                    <input type="text"
                           id="themes"
                           name="themes"
                           class="tvi-input"
                           placeholder="ex. horreur, thriller, drame"
                           required>
                </div>

                <div class="tvi-form-footer">
                  
                 <div style="text-align: right;">
    <button type="submit" class="tvi-button">Générer l'affiche</button>
</div>

                <p class="tvi-hint">
                    Astuce : clique plusieurs fois sur un même thème pour tester différentes combinaisons.
                </p>
            </form>
        </section>

        <!-- COLONNE DROITE : résultats -->
        <section class="tvi-panel">
            <div class="tvi-results-header">
                <h2>2. Résultats</h2>
            </div>

            {% if gen_result %}
                {% set themes_to_display = display_themes if display_themes is defined and display_themes else gen_result.input_themes %}
  <p class="tvi-result-summary">
      <span class="tvi-label" style="font-size:0.82rem;">Thèmes :</span>
      <span class="tvi-tags">
          {% for t in themes_to_display.split(',') %}
              {% set tt = t.strip() %}
              {% if tt %}
                  <span class="tvi-tag">{{ tt }}</span>
              {% endif %}
          {% endfor %}
                    </span>
                </p>

                <div class="tvi-posters-grid">
                    {% for p in gen_result.posters %}
                        {% if p is string %}
                          {% set path = p %}
                        {% elif p is sequence and p|length > 2 %}
                          {% set path = p[2] %}
                        {% else %}
                          {% set path = p %}
                        {% endif %}
                        <article class="tvi-poster-card">
                            <img src="{{ url_for('clip_bp.serve_file', filepath=path) }}" alt="Affiche proposée">
                          <div class="tvi-poster-meta">
    <div class="tvi-badge">Affiche proposée</div>
</div>

                        </article>
                    {% endfor %}
                </div>
            {% else %}
                <p class="tvi-placeholder">
                    Aucune affiche pour l’instant. Sélectionne quelques thèmes à gauche puis lance une génération.
                </p>
            {% endif %}

            <p class="tvi-footer-note">
                Les affiches proposées sont issues d’un index pré-calculé à partir de ton corpus de posters.
            </p>
        </section>
    </main>
</div>

<script>
    function addGenre(genre) {
        const input = document.getElementById("themes");
        if (!input) return;

        const current = input.value.split(",")
            .map(s => s.trim())
            .filter(s => s.length > 0);

        if (!current.includes(genre)) {
            current.push(genre);
        }
        input.value = current.join(", ");
        input.focus();
    }
</script>
</body>
</html>
"""



# =========================
# ROUTES DU BLUEPRINT
# =========================

@clip_bp.route("/", methods=["GET"])
def index():
    # Page initiale, aucun résultat encore
    return render_template_string(
        INDEX_HTML,
        gen_result=None,
        available_genres=AVAILABLE_GENRES,
    )


@clip_bp.route("/generate_from_themes", methods=["POST"])
def route_generate_from_themes():
    # 1) Saisie utilisateur (FR)
    raw_themes = request.form.get("themes", "").strip()

    # 2) Normalisation pour le backend (EN)
    normalized_themes = normalize_themes_for_backend(raw_themes)

    # On force toujours 1 résultat
    top_k = 1

    try:
        result = generate_from_themes(normalized_themes, top_k=top_k)
    except Exception as e:
        return f"Erreur lors de la génération : {e}", 400

    # 3) On passe à la fois le résultat et la version FR pour l’affichage
    return render_template_string(
        INDEX_HTML,
        gen_result=result,
        available_genres=AVAILABLE_GENRES,
        display_themes=raw_themes or normalized_themes,  # fallback
    )




@clip_bp.route("/analyze_poster", methods=["POST"])
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

    return render_template_string(INDEX_HTML, gen_result=None, an_result=result)


@clip_bp.route("/files/<path:filepath>")
def serve_file(filepath: str):
    """
    Sert un fichier image à partir du projet.
    Exemple: data/posters/331834.jpg
    """
    directory = BASE_DIR
    full_path = os.path.join(directory, filepath)

    if not os.path.exists(full_path):
        return f"Fichier introuvable: {filepath}", 404

    dirname, filename = os.path.split(full_path)
    return send_from_directory(dirname, filename)


@clip_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

def normalize_themes_for_backend(raw: str) -> str:
    """
    Transforme une chaîne comme 'horreur, drame, comédie'
    en 'horror,drama,comedy' pour le backend.
    """
    tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
    mapped = []

    for t in tokens:
        mapped.append(FR_TO_EN.get(t, t))  # si inconnu, on garde tel quel

    # On garde l'ordre, on évite les doublons simples
    seen = set()
    result = []
    for t in mapped:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return ",".join(result)


# import os
# import sys
# from flask import Blueprint, request, jsonify, render_template_string, send_from_directory
# from werkzeug.utils import secure_filename
# from dotenv import load_dotenv; load_dotenv()

# # dossier racine du projet
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# # on ajoute themes_vers_images dans le PYTHONPATH
# sys.path.append(os.path.join(BASE_DIR, "themes_vers_images"))

# from service import generate_from_themes, analyze_poster

# # Blueprint au lieu d'une app Flask
# clip_bp = Blueprint("clip_bp", __name__)

# # Dossier où on sauvegardera les images uploadées pour analyse
# BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Genres proposés dans l'interface (à adapter si besoin)
# AVAILABLE_GENRES = [
#     "action", "aventure", "animation", "comédie", "crime", "documentaire",
#     "drame", "fantasy", "familial", "guerre", "historique", "horreur",
#     "musique", "mystère", "romance", "science-fiction", "thriller",
#     "western", "biopic", "film noir", "réalité", "sport"
# ]

# FR_TO_EN = {
#     "action": "action",
#     "horreur": "horror",
#     "comédie": "comedy",
#     "comedie": "comedy",
#     "drame": "drama",
#     "aventure": "adventure",
#     "aventura": "adventure",
#     "science-fiction": "scifi",
#     "science fiction": "scifi",
#     "sf": "scifi",
#     "fantasy": "fantasy",
#     "crime": "crime",
#     "famille": "family",
#     "familial": "family",
#     "musique": "music",
#     "historique": "history",
#     "histoire": "history",
#     "guerre": "war",
#     "western": "western",
#     "mystère": "mystery",
#     "mystere": "mystery",
#     "documentaire": "documentary",
#     "téléréalité": "realitytv",
#     "tele-realite": "realitytv",
#     "réalité": "realitytv",
#     "reality": "realitytv",
#     "sport": "sport",
#     "film noir": "filmnoir",
#     "talk-show": "talkshow",
#     "talkshow": "talkshow",
#     "court métrage": "short",
#     "court metrage": "short",
#     "biopic": "biography",
#     "biographie": "biography",
#     "romance": "romance",
# }

# # ---------- Interface HTML Ultra-Moderne ----------

# INDEX_HTML = """
# <!doctype html>
# <html lang="fr">
# <head>
#     <meta charset="utf-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Thèmes vers Images</title>
#     <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
#     <style>
#         * {
#             margin: 0;
#             padding: 0;
#             box-sizing: border-box;
#         }

#         :root {
#             --bg-primary: #0a0a0f;
#             --bg-secondary: #121218;
#             --bg-tertiary: #1a1a24;
#             --accent: #6366f1;
#             --accent-hover: #4f46e5;
#             --accent-glow: rgba(99, 102, 241, 0.3);
#             --text-primary: #ffffff;
#             --text-secondary: #a1a1aa;
#             --text-muted: #71717a;
#             --border: #27272a;
#             --success: #10b981;
#             --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         }

#         body {
#             font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
#             background: var(--bg-primary);
#             color: var(--text-primary);
#             line-height: 1.6;
#             overflow-x: hidden;
#         }

#         /* Background animé */
#         .bg-animated {
#             position: fixed;
#             top: 0;
#             left: 0;
#             width: 100%;
#             height: 100%;
#             z-index: 0;
#             opacity: 0.15;
#             background: 
#                 radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
#                 radial-gradient(circle at 80% 80%, rgba(245, 87, 108, 0.15) 0%, transparent 50%);
#             animation: float 20s ease-in-out infinite;
#         }

#         @keyframes float {
#             0%, 100% { transform: translate(0, 0); }
#             50% { transform: translate(30px, -30px); }
#         }

#         /* Container principal */
#         .container {
#             position: relative;
#             z-index: 1;
#             max-width: 1400px;
#             margin: 0 auto;
#             padding: 32px 24px;
#         }

#         /* Header */
#         .header {
#             margin-bottom: 32px;
#             animation: fadeInDown 0.8s ease;
#         }

#         @keyframes fadeInDown {
#             from {
#                 opacity: 0;
#                 transform: translateY(-20px);
#             }
#             to {
#                 opacity: 1;
#                 transform: translateY(0);
#             }
#         }

#         .back-btn {
#             display: inline-flex;
#             align-items: center;
#             gap: 8px;
#             background: var(--bg-secondary);
#             border: 1px solid var(--border);
#             color: var(--text-secondary);
#             padding: 10px 20px;
#             border-radius: 12px;
#             font-size: 14px;
#             font-weight: 500;
#             text-decoration: none;
#             transition: all 0.2s ease;
#             margin-bottom: 20px;
#         }

#         .back-btn:hover {
#             background: var(--bg-tertiary);
#             border-color: var(--accent);
#             color: var(--text-primary);
#             transform: translateX(-4px);
#         }

#         .title {
#             font-size: 28px;
#             font-weight: 700;
#             background: var(--gradient-primary);
#             -webkit-background-clip: text;
#             -webkit-text-fill-color: transparent;
#             background-clip: text;
#             margin-bottom: 8px;
#         }

#         .subtitle {
#             font-size: 15px;
#             color: var(--text-secondary);
#             font-weight: 400;
#         }

#         /* Layout principal */
#         .main-layout {
#             display: grid;
#             grid-template-columns: 380px 1fr;
#             gap: 28px;
#             animation: fadeIn 1s ease;
#         }

#         @keyframes fadeIn {
#             from { opacity: 0; }
#             to { opacity: 1; }
#         }

#         @media (max-width: 1024px) {
#             .main-layout {
#                 grid-template-columns: 1fr;
#             }
#         }

#         /* Panel */
#         .panel {
#             background: var(--bg-secondary);
#             border: 1px solid var(--border);
#             border-radius: 20px;
#             padding: 28px;
#             backdrop-filter: blur(10px);
#             box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
#         }

#         .panel-header {
#             margin-bottom: 20px;
#         }

#         .panel-title {
#             font-size: 18px;
#             font-weight: 600;
#             margin-bottom: 6px;
#         }

#         .panel-desc {
#             font-size: 13px;
#             color: var(--text-secondary);
#         }

#         /* Genre pills */
#         .genres-grid {
#             display: flex;
#             flex-wrap: wrap;
#             gap: 8px;
#             margin-bottom: 20px;
#             max-height: 220px;
#             overflow-y: auto;
#             padding: 4px;
#         }

#         .genres-grid::-webkit-scrollbar {
#             width: 6px;
#         }

#         .genres-grid::-webkit-scrollbar-track {
#             background: var(--bg-tertiary);
#             border-radius: 3px;
#         }

#         .genres-grid::-webkit-scrollbar-thumb {
#             background: var(--accent);
#             border-radius: 3px;
#         }

#         .genre-pill {
#             background: var(--bg-tertiary);
#             border: 1px solid var(--border);
#             color: var(--text-primary);
#             padding: 7px 14px;
#             border-radius: 10px;
#             font-size: 13px;
#             font-weight: 500;
#             cursor: pointer;
#             transition: all 0.2s ease;
#             user-select: none;
#         }

#         .genre-pill:hover {
#             background: var(--accent);
#             border-color: var(--accent);
#             transform: translateY(-2px);
#             box-shadow: 0 4px 16px var(--accent-glow);
#         }

#         .genre-pill:active {
#             transform: translateY(0);
#         }

#         /* Input moderne */
#         .input-group {
#             margin-bottom: 18px;
#         }

#         .input-label {
#             display: block;
#             font-size: 12px;
#             font-weight: 500;
#             color: var(--text-secondary);
#             margin-bottom: 8px;
#             text-transform: uppercase;
#             letter-spacing: 0.5px;
#         }

#         .input-field {
#             width: 100%;
#             background: var(--bg-tertiary);
#             border: 1px solid var(--border);
#             border-radius: 12px;
#             padding: 12px 14px;
#             color: var(--text-primary);
#             font-size: 14px;
#             font-family: 'Inter', sans-serif;
#             transition: all 0.2s ease;
#         }

#         .input-field:focus {
#             outline: none;
#             border-color: var(--accent);
#             box-shadow: 0 0 0 3px var(--accent-glow);
#         }

#         .input-field::placeholder {
#             color: var(--text-muted);
#         }

#         /* Bouton générateur */
#         .generate-btn {
#             width: 100%;
#             background: var(--gradient-primary);
#             border: none;
#             border-radius: 14px;
#             padding: 14px 28px;
#             color: white;
#             font-size: 15px;
#             font-weight: 600;
#             cursor: pointer;
#             transition: all 0.3s ease;
#             box-shadow: 0 8px 32px var(--accent-glow);
#             position: relative;
#             overflow: hidden;
#         }

#         .generate-btn::before {
#             content: '';
#             position: absolute;
#             top: 0;
#             left: -100%;
#             width: 100%;
#             height: 100%;
#             background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
#             transition: left 0.5s;
#         }

#         .generate-btn:hover::before {
#             left: 100%;
#         }

#         .generate-btn:hover {
#             transform: translateY(-2px);
#             box-shadow: 0 12px 40px var(--accent-glow);
#         }

#         .generate-btn:active {
#             transform: translateY(0);
#         }

#         /* Résultats */
#         .results-empty {
#             text-align: center;
#             padding: 60px 40px;
#             color: var(--text-muted);
#         }

#         .results-empty-icon {
#             font-size: 48px;
#             margin-bottom: 12px;
#             opacity: 0.3;
#         }

#         .results-header {
#             margin-bottom: 20px;
#             display: flex;
#             justify-content: space-between;
#             align-items: center;
#         }

#         .themes-selected {
#             display: flex;
#             flex-wrap: wrap;
#             gap: 8px;
#             margin-bottom: 20px;
#         }

#         .theme-tag {
#             background: var(--accent-glow);
#             color: var(--accent);
#             padding: 5px 11px;
#             border-radius: 8px;
#             font-size: 12px;
#             font-weight: 500;
#             border: 1px solid var(--accent);
#         }

#         /* Grille d'affiches - RÉDUITE */
#         .posters-grid {
#             display: grid;
#             grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
#             gap: 20px;
#         }

#         .poster-card {
#             background: var(--bg-tertiary);
#             border: 1px solid var(--border);
#             border-radius: 14px;
#             overflow: hidden;
#             transition: all 0.3s ease;
#             cursor: pointer;
#         }

#         .poster-card:hover {
#             transform: translateY(-6px);
#             box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
#             border-color: var(--accent);
#         }

#         .poster-image {
#             width: 100%;
#             aspect-ratio: 2/3;
#             object-fit: cover;
#             background: var(--bg-primary);
#         }

#         .poster-info {
#             padding: 12px;
#         }

#         .poster-badge {
#             display: inline-block;
#             background: var(--success);
#             color: white;
#             padding: 3px 9px;
#             border-radius: 6px;
#             font-size: 10px;
#             font-weight: 600;
#             text-transform: uppercase;
#             letter-spacing: 0.5px;
#         }

#         /* Loader animation */
#         .loading {
#             display: none;
#             text-align: center;
#             padding: 40px;
#         }

#         .loading.active {
#             display: block;
#         }

#         .loader {
#             width: 40px;
#             height: 40px;
#             border: 3px solid var(--bg-tertiary);
#             border-top-color: var(--accent);
#             border-radius: 50%;
#             animation: spin 1s linear infinite;
#             margin: 0 auto 12px;
#         }

#         @keyframes spin {
#             to { transform: rotate(360deg); }
#         }

#         /* Stats badge */
#         .stats-badge {
#             display: inline-flex;
#             align-items: center;
#             gap: 6px;
#             background: var(--bg-tertiary);
#             border: 1px solid var(--border);
#             padding: 5px 11px;
#             border-radius: 8px;
#             font-size: 11px;
#             color: var(--text-secondary);
#         }

#         .stats-number {
#             color: var(--accent);
#             font-weight: 600;
#         }

#         .hint {
#             margin-top: 14px;
#             text-align: center;
#             color: var(--text-muted);
#             font-size: 11px;
#         }

#         /* Responsive */
#         @media (max-width: 768px) {
#             .container {
#                 padding: 20px 16px;
#             }

#             .panel {
#                 padding: 20px;
#             }

#             .title {
#                 font-size: 24px;
#             }

#             .posters-grid {
#                 grid-template-columns: 1fr;
#             }
#         }
#     </style>
# </head>
# <body>
#     <div class="bg-animated"></div>
    
#     <div class="container">
#         <!-- Header -->
#         <header class="header">
#             <a href="/" class="back-btn">
#                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
#                     <path d="M19 12H5M12 19l-7-7 7-7"/>
#                 </svg>
#                 Retour au menu
#             </a>
#             <h1 class="title">Thèmes vers Images</h1>
#             <p class="subtitle">
#                 Compose un ensemble de genres et découvre les affiches correspondantes
#             </p>
#         </header>

#         <!-- Layout principal -->
#         <div class="main-layout">
#             <!-- Panneau de contrôle -->
#             <div class="panel">
#                 <div class="panel-header">
#                     <h2 class="panel-title">Sélection des thèmes</h2>
#                     <p class="panel-desc">
#                         Clique sur les genres ci-dessous
#                     </p>
#                 </div>

#                 <!-- Grille de genres -->
#                 <div class="genres-grid">
#                     {% for g in available_genres %}
#                     <button type="button" class="genre-pill" onclick="addGenre('{{ g }}')">
#                         {{ g }}
#                     </button>
#                     {% endfor %}
#                 </div>

#                 <!-- Formulaire -->
#                 <form method="post" action="{{ url_for('clip_bp.route_generate_from_themes') }}" id="generateForm">
#                     <div class="input-group">
#                         <label for="themes" class="input-label">Genres sélectionnés</label>
#                         <input 
#                             type="text" 
#                             id="themes" 
#                             name="themes" 
#                             class="input-field"
#                             placeholder="ex: horreur, thriller, drame"
#                             required
#                         >
#                     </div>

#                     <button type="submit" class="generate-btn">
#                         Générer l'affiche
#                     </button>
#                 </form>

#                 <div class="hint">
#                     Clique plusieurs fois sur un même thème pour différentes variantes
#                 </div>
#             </div>

#             <!-- Panneau de résultats -->
#             <div class="panel">
#                 <div class="panel-header">
#                     <div class="results-header">
#                         <h2 class="panel-title">Résultat</h2>
#                         {% if gen_result %}
#                         <div class="stats-badge">
#                             <span class="stats-number">{{ gen_result.posters|length }}</span>
#                             affiche{{ 's' if gen_result.posters|length > 1 else '' }}
#                         </div>
#                         {% endif %}
#                     </div>
#                 </div>

#                 {% if gen_result %}
#                     <!-- Thèmes sélectionnés -->
#                     {% set themes_to_display = display_themes if display_themes is defined and display_themes else gen_result.input_themes %}
#                     <div class="themes-selected">
#                         {% for t in themes_to_display.split(',') %}
#                             {% set tt = t.strip() %}
#                             {% if tt %}
#                                 <span class="theme-tag">{{ tt }}</span>
#                             {% endif %}
#                         {% endfor %}
#                     </div>

#                     <!-- Grille d'affiches -->
#                     <div class="posters-grid">
#                         {% for p in gen_result.posters %}
#                             {% if p is string %}
#                                 {% set path = p %}
#                             {% elif p is sequence and p|length > 2 %}
#                                 {% set path = p[2] %}
#                             {% else %}
#                                 {% set path = p %}
#                             {% endif %}
#                             <div class="poster-card">
#                                 <img 
#                                     src="{{ url_for('clip_bp.serve_file', filepath=path) }}" 
#                                     alt="Affiche générée"
#                                     class="poster-image"
#                                 >
#                                 <div class="poster-info">
#                                     <span class="poster-badge">Générée par IA</span>
#                                 </div>
#                             </div>
#                         {% endfor %}
#                     </div>
#                 {% else %}
#                     <!-- État vide -->
#                     <div class="results-empty">
#                         <div class="results-empty-icon">···</div>
#                         <h3 style="color: var(--text-secondary); margin-bottom: 6px;">Aucune affiche générée</h3>
#                         <p style="font-size: 13px;">Sélectionne des genres et lance la génération</p>
#                     </div>
#                 {% endif %}

#                 <!-- Loader -->
#                 <div class="loading" id="loader">
#                     <div class="loader"></div>
#                     <p style="color: var(--text-secondary); font-size: 13px;">Génération en cours...</p>
#                 </div>
#             </div>
#         </div>
#     </div>

#     <script>
#         function addGenre(genre) {
#             const input = document.getElementById("themes");
#             if (!input) return;

#             const current = input.value.split(",")
#                 .map(s => s.trim())
#                 .filter(s => s.length > 0);

#             if (!current.includes(genre)) {
#                 current.push(genre);
#             }
            
#             input.value = current.join(", ");
#             input.focus();
#         }

#         document.getElementById('generateForm').addEventListener('submit', function() {
#             document.getElementById('loader').classList.add('active');
#         });
#     </script>
# </body>
# </html>
# """

# # =========================
# # ROUTES DU BLUEPRINT
# # =========================

# @clip_bp.route("/", methods=["GET"])
# def index():
#     return render_template_string(
#         INDEX_HTML,
#         gen_result=None,
#         available_genres=AVAILABLE_GENRES,
#     )


# @clip_bp.route("/generate_from_themes", methods=["POST"])
# def route_generate_from_themes():
#     raw_themes = request.form.get("themes", "").strip()
#     normalized_themes = normalize_themes_for_backend(raw_themes)
#     top_k = 1

#     try:
#         result = generate_from_themes(normalized_themes, top_k=top_k)
#     except Exception as e:
#         return f"Erreur lors de la génération : {e}", 400

#     return render_template_string(
#         INDEX_HTML,
#         gen_result=result,
#         available_genres=AVAILABLE_GENRES,
#         display_themes=raw_themes or normalized_themes,
#     )


# @clip_bp.route("/analyze_poster", methods=["POST"])
# def route_analyze_poster():
#     if "poster" not in request.files:
#         return "Aucun fichier reçu.", 400

#     file = request.files["poster"]
#     if file.filename == "":
#         return "Nom de fichier vide.", 400

#     filename = secure_filename(file.filename)
#     save_path = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(save_path)

#     top_k_str = request.form.get("top_k", "5")
#     try:
#         top_k = int(top_k_str)
#     except ValueError:
#         top_k = 5

#     try:
#         result = analyze_poster(save_path, top_k=top_k)
#     except Exception as e:
#         return f"Erreur lors de l'analyse : {e}", 400

#     return render_template_string(INDEX_HTML, gen_result=None, an_result=result)


# @clip_bp.route("/files/<path:filepath>")
# def serve_file(filepath: str):
#     directory = BASE_DIR
#     full_path = os.path.join(directory, filepath)

#     if not os.path.exists(full_path):
#         return f"Fichier introuvable: {filepath}", 404

#     dirname, filename = os.path.split(full_path)
#     return send_from_directory(dirname, filename)


# @clip_bp.route("/health", methods=["GET"])
# def health():
#     return jsonify({"status": "ok"})


# def normalize_themes_for_backend(raw: str) -> str:
#     tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
#     mapped = []

#     for t in tokens:
#         mapped.append(FR_TO_EN.get(t, t))

#     seen = set()
#     result = []
#     for t in mapped:
#         if t not in seen:
#             seen.add(t)
#             result.append(t)
#     return ",".join(result)