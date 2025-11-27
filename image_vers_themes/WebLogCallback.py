import json
import keras
import os

class WebLogCallback(keras.callbacks.Callback):
    def __init__(self, path="train_status.json"):
        super().__init__()
        self.path = path

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        payload = {
            "epoch": int(epoch),
            "logs": {k: float(v) for k, v in logs.items()}
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
