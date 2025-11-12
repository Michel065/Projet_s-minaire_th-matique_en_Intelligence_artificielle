import argparse
from pathlib import Path
import pandas as pd
import torch, faiss, open_clip, numpy as np

def load_model(device='cpu'):
    model, _, _ = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tok = open_clip.get_tokenizer('ViT-B-32')
    model.eval().to(device)
    return model, tok

def encode_text(model, tok, device, text):
    with torch.no_grad():
        t = tok([text]).to(device)
        e = model.encode_text(t); e = e / e.norm(dim=-1, keepdim=True)
        return e.cpu().numpy().astype('float32')

def main(args):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model, tok = load_model(device)
    index = faiss.read_index(str(Path(args.index_dir) / 'index.faiss'))
    meta = pd.read_parquet(Path(args.index_dir) / 'index_meta.parquet')
    q = encode_text(model, tok, device, args.query)
    D, I = index.search(q, args.k)
    for idx, score in zip(I[0], D[0]):
        row = meta.iloc[int(idx)]
        print(f"{score:.3f}\t{row['theme']}\t{row['image_path']}")

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--query', type=str, required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--index_dir', type=str, default='themes_vers_images')
    args = ap.parse_args()
    main(args)
