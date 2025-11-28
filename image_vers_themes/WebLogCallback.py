import json
import keras
import os

class WebLogCallback(keras.callbacks.Callback):
    def __init__(self, total_epochs,output_dir="../model", name="train_status.json"):
        super().__init__()

        os.makedirs(output_dir, exist_ok=True)
        self.path = os.path.join(output_dir, name)
        self.total_epochs = total_epochs

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"epoch": 0, "total": total_epochs, "percent": 0}, f)

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}

        percent = int(((epoch + 1) / self.total_epochs) * 100)

        payload = {
            "epoch": int(epoch + 1),
            "total": int(self.total_epochs),
            "percent": percent,
            "logs": {k: float(v) for k, v in logs.items()}
        }

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
