from typing import List
import os

import torch
from diffusers import StableDiffusionPipeline

from utils import parse_user_themes, GENRES


MODEL_ID = "runwayml/stable-diffusion-v1-5"
_pipe = None


def themes_to_prompt_from_vector(theme_vector) -> str:
    active_indices = [i for i, v in enumerate(theme_vector) if v > 0]

    if not active_indices:
        base_genres_str = "movie poster, cinematic, dramatic lighting"
    else:
        active_genres = [GENRES[i].lower() for i in active_indices]
        active_genres = active_genres[:4]
        genres_str = ", ".join(active_genres)
        base_genres_str = (
            f"movie poster, {genres_str}, cinematic lighting, highly detailed, dramatic composition"
        )

    prompt = base_genres_str + ", film still, high quality, 4k"
    return prompt


def themes_to_prompt_from_string(theme_str: str) -> str:
    vec = parse_user_themes(theme_str, binary=True)
    return themes_to_prompt_from_vector(vec)


def get_pipeline(device: str | None = None) -> StableDiffusionPipeline:
    global _pipe
    if _pipe is not None:
        return _pipe

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[generate_diffusion] Chargement du modèle {MODEL_ID} sur {device} ...")
    pipe = StableDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    )
    pipe = pipe.to(device)
    _pipe = pipe
    return _pipe


def generate_image_from_prompt(
    prompt: str,
    output_path: str = "data/generated/poster_from_themes.png",
    num_inference_steps: int = 30,
    guidance_scale: float = 7.5,
    height: int = 512,
    width: int = 384,
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pipe = get_pipeline()

    print(f"[generate_diffusion] Prompt : {prompt}")
    with torch.autocast(pipe.device.type):
        image = pipe(
            prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width,
        ).images[0]

    image.save(output_path)
    print(f"[generate_diffusion] Image sauvegardée dans {output_path}")
    return output_path


def generate_image_from_themes_string(
    theme_str: str,
    output_path: str = "data/generated/poster_from_themes.png",
    **kwargs,
) -> str:
    prompt = themes_to_prompt_from_string(theme_str)
    return generate_image_from_prompt(prompt, output_path=output_path, **kwargs)


def main():
    print("=== Génération d'affiche par diffusion (thèmes -> image) ===")
    theme_str = input("Entrez vos thèmes (ex: 'action, horreur, drame'): ")
    out_path = "data/generated/poster_from_themes.png"
    generate_image_from_themes_string(theme_str, output_path=out_path)
    print(f"Image générée : {out_path}")


if __name__ == "__main__":
    main()
