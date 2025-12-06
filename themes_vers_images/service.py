# themes_vers_images/service.py
from typing import Dict, Any
from routeur import predict_posters_from_themes
from clip_classifier import predict_themes_from_image
from utils import GENRES

def _as_list_of_str(x):
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    out = []
    for e in x:
        out.append(e[-1] if isinstance(e, tuple) else e)
    return out

def generate_from_themes(theme_str: str, top_k: int = 3) -> Dict[str, Any]:
    mode, image_paths, msg = predict_posters_from_themes(theme_str, top_k_baseline=top_k)
    image_paths = _as_list_of_str(image_paths)   
    return {
        "input_themes": theme_str,
        "mode": mode,
        "message": msg,
        "posters": image_paths,
    }


def analyze_poster(image_path: str, top_k: int = 5) -> Dict[str, Any]:
    scores = predict_themes_from_image(image_path)
    scored = [(GENRES[i], float(scores[i])) for i in range(len(GENRES))]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = [{"genre": g, "score": s} for g, s in scored[:top_k]]
    return {"image_path": image_path, "top_k": top}
