from pathlib import Path
def ensure_parent(p):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True); return p
