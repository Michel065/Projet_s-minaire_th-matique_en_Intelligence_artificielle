from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras import regularizers

def Conv2D_et_MaxPool(x, nbr_filtre=64,taille_filtre=3,pourcentage_inactifs=0.2):
    x = layers.Conv2D(nbr_filtre, taille_filtre, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.Conv2D(nbr_filtre, taille_filtre, padding="same", use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    x = layers.MaxPool2D()(x)
    if pourcentage_inactifs > 0:
        x = layers.Dropout(pourcentage_inactifs)(x)
    return x

def build_model(param_model):  # param_model = ((182,268,3), 28)
    """
    Modèle CNN pour prédire les genres à partir des posters.
    """
    shape_poster = param_model[0]
    classes_y    = param_model[1]

    inputs = keras.Input(shape=shape_poster)

    # Bloc 1
    x=Conv2D_et_MaxPool(inputs,64,5,0)
    # Bloc 2
    x=Conv2D_et_MaxPool(x,128,3,0.15)
    # Bloc 3
    x=Conv2D_et_MaxPool(x,256,3,0.25)

    # Tête
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(512, activation="relu",kernel_regularizer=regularizers.l2(1e-4))(x)
    x = layers.Dropout(0.3)(x)

    # a voir si ca marche pas l'actuel
    #x = layers.Dense(256, activation="relu",kernel_regularizer=regularizers.l2(1e-4))(x)
    #x = layers.Dropout(0.2)(x)

    outputs = layers.Dense(classes_y, activation="sigmoid", dtype="float32")(x)

    model = keras.Model(inputs, outputs, name="model_poster_vers_theme_cnn")
    return model
