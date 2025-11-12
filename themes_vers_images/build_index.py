import argparse
from pathlib import Path
import pandas as pd
from PIL import Image
import torch, faiss, open_clip, numpy as np
from tqdm import tqdm

def load_model(device='cpu'):
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    model.eval().to(device)
    return model, preprocess

def encode_images(model, preprocess, device, paths):
    embs = []
    with torch.no_grad():
        for p in tqdm(paths, desc='Encoding images'):
            img = Image.open(p).convert('RGB')
            x = preprocess(img).unsqueeze(0).to(device)
            e = model.encode_image(x); e = e / e.norm(dim=-1, keepdim=True)
            embs.append(e.cpu().numpy())
    return np.vstack(embs).astype('float32')

def main(args):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model, preprocess = load_model(device)
    df = pd.read_csv(args.csv)  # colonnes attendues: theme,image_path
    paths = [Path(p) for p in df['image_path'].astype(str)]
    X = encode_images(model, preprocess, device, paths)
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X)
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(Path(args.out_dir) / 'index.faiss'))
    df.to_parquet(Path(args.out_dir) / 'index_meta.parquet', index=False)
    print('OK: index.faiss + index_meta.parquet')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', type=str, default='themes_vers_images/data/themes.csv')
    ap.add_argument('--out_dir', type=str, default='themes_vers_images')
    args = ap.parse_args()
    main(args)
