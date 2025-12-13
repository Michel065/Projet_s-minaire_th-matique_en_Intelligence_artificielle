# themes_vers_images/hf_generate.py
import os, time, hashlib, requests
from typing import Optional
from utils import parse_user_themes, GENRES

HF_API_URL = "https://api-inference.huggingface.co/models"
DEFAULT_MODEL_ID = "runwayml/stable-diffusion-v1-5"  # public et robuste

def normalize_theme_key(theme_str: str) -> str:
    toks = [t.strip().lower() for t in theme_str.split(",") if t.strip()]
    toks = sorted(set(toks))
    return ",".join(toks)

def themes_to_prompt_from_string(theme_str: str) -> str:
    
    vec = parse_user_themes(theme_str, binary=True)
    active = [GENRES[i].lower() for i,v in enumerate(vec) if v > 0][:4]
    genres_str = ", ".join(active) if active else "cinematic"
    hints = []
    H = {
        "action": "dynamic action scene, strong contrast, intense motion",
        "adventure": "epic wide shot, adventurous mood, vast landscape",
        "horror": "dark eerie atmosphere, creepy mood, fog, suspense",
        "thriller": "tense mood, chiaroscuro lighting, suspenseful framing",
        "drama": "emotional tone, realistic lighting",
        "romance": "warm soft lighting, intimate moment, pastel colors",
        "comedy": "bright colors, playful composition, high key lighting",
        "sci-fi": "futuristic city, neon lights, advanced technology",
        "fantasy": "mystical forest, magical elements, enchanted mood",
        "crime": "noir city at night, gritty, silhouettes, rain reflections",
    }
    for g in active:
        if g in H: hints.append(H[g])
    if not hints:
        hints = ["cinematic lighting, dramatic composition, realistic details"]
    style_str = ", ".join(hints)
    prompt = (
        f"epic cinematic movie poster, {genres_str}, {style_str}, "
        "centered composition, professional film key art, ultra-detailed, sharp focus, "
        "volumetric lighting, photorealistic, no text, no watermark"
    )
    return prompt

def _safe_filename(theme_key: str) -> str:

    slug = theme_key.replace(",", "_")
    h = hashlib.sha1(theme_key.encode("utf-8")).hexdigest()[:8]
    return f"poster_{slug}_{h}.png"

def generate_via_hf(
    prompt: str,
    output_dir: str = "themes_vers_images/data/generated",
    model_id: str = DEFAULT_MODEL_ID,
    *,
    hf_token: Optional[str] = None,
    num_inference_steps: int = 40,
    guidance_scale: float = 8.0,
    width: int = 512,
    height: int = 704,
    timeout_s: int = 120,
    theme_key_for_name: Optional[str] = None,
) -> str:
    """
    Appelle l'API d'inférence HF (text->image) et sauvegarde le PNG.
    Renvoie le chemin du fichier.
    Lève requests.HTTPError / Timeout si échec réseau/serveur.
    """
    hf_token = hf_token or os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN manquant : définis une variable d'environnement HF_TOKEN ou passe hf_token=...")

    url = f"{HF_API_URL}/{model_id}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "width": width,
            "height": height,
        },
        "options": {"wait_for_model": True},
    }

    os.makedirs(output_dir, exist_ok=True)
    fname = _safe_filename(theme_key_for_name or f"{time.time()}") 
    out_path = os.path.join(output_dir, fname)

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
    if resp.status_code >= 400:
        
        raise requests.HTTPError(f"HF API error {resp.status_code}: {resp.text[:300]}")

    with open(out_path, "wb") as f:
        f.write(resp.content)
    return out_path

