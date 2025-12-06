import os
from typing import List

import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

from utils import GENRES  


MODEL_ID = "openai/clip-vit-base-patch32"

_device = None
_model = None
_processor = None


def get_clip_pipeline():
    """
    Charge paresseusement (lazy) le modèle CLIP pré-entraîné.
    Utilise CPU par défaut (suffisant pour de petits tests).
    """
    global _device, _model, _processor
    if _model is not None and _processor is not None:
        return _device, _model, _processor

    _device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[clip_classifier] Chargement du modèle CLIP sur {_device} ...")

    _model = CLIPModel.from_pretrained(MODEL_ID)
    _processor = CLIPProcessor.from_pretrained(MODEL_ID)

    _model = _model.to(_device)
    _model.eval()

    return _device, _model, _processor


def predict_themes_from_image(image_path: str) -> np.ndarray:
    """
    Analyse une image de poster avec CLIP et renvoie un vecteur (28,)
    de scores alignés avec l'ordre de GENRES.

    Plus le score est élevé, plus CLIP trouve que l'image correspond
    au prompt textuel associé à ce genre.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    device, model, processor = get_clip_pipeline()

    # Préparer l'image
    image = Image.open(image_path).convert("RGB")

    # Construire une description textuelle par genre

    text_prompts: List[str] = [
        f"movie poster of a {genre.lower()} film" for genre in GENRES
    ]

    inputs = processor(
        text=text_prompts,
        images=image,
        return_tensors="pt",
        padding=True,
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        # Similarités image->texte, shape = (1, 28)
        logits_per_image = outputs.logits_per_image[0]  # (28,)

    scores = logits_per_image.detach().cpu().numpy().astype(np.float32)


    min_val = float(scores.min())
    max_val = float(scores.max())
    if max_val > min_val:
        scores = (scores - min_val) / (max_val - min_val)

    return scores  # shape (28,)
