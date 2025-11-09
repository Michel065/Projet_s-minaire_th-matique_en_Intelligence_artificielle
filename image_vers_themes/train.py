import tensorflow as tf
from time import time
from tensorflow.keras import mixed_precision
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

def define_startegie(build_model,param_model=((182,268,3),28)): 
    mixed_precision.set_global_policy("mixed_float16") # conseil de chat pour optimiser
    strategy = tf.distribute.get_strategy()   
    with strategy.scope():
        model = build_model(param_model)  
        model.compile(#recup dans le cours d'apprentissage données massive
            loss=tf.keras.losses.BinaryCrossentropy(from_logits=False),
            optimizer = tf.keras.optimizers.Adam(learning_rate=1e-4),
            metrics=[tf.keras.metrics.AUC(curve="PR", multi_label=True), "accuracy"]
        )
    return model


def train_model(model,dataset_train,dataset_val,EPOCHS = 50):
    """
    fonction pour train un model, beaucoup de partie recupere dans un autre cours

    Args:
        model:le model 
        dataset_train: donnees d'entrainement
        dataset_val: pour la validation et lacorection en cours de route
        EPOCHS: nbr de passage sur le dataset 

    Returns:
        hitory: l'historique pour faire des graphs
    """
    callbacks = [ #recup dans le cours d'apprentissage données massive
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        ModelCheckpoint(
            filepath="best_model.keras",
            monitor="val_loss",
            mode="min",
            save_best_only=True,
            verbose=1
        ),
    ]

    t0 = time()
    history = model.fit(dataset_train,validation_data=dataset_val,epochs=EPOCHS,callbacks=callbacks,verbose=1)
    tt = time() - t0

    h = int(tt // 3600)
    m = int((tt % 3600) // 60)
    s = int(tt % 60)
    print(f"Temps d'entraînement: {h} h {m} min {s} s")
    return history


def evalution_du_model(model,dataset_test):
    results = model.evaluate(dataset_test, return_dict=True)
    print(f"Résultat apres évaluation:")
    for k, v in results.items():
        print(f"{k}: {v:.4f}")
    return results

def load_model(nom_model="./best_model.keras"):
    return tf.keras.models.load_model(nom_model, compile=True)