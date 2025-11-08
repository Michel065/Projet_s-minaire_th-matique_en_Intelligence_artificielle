from tensorflow import keras
from tensorflow.keras import layers

def build_model(param_model=((182,268,3),28)):
    """
    notre model
    """
    shape_poster=param_model[0]
    classes_y=param_model[1]
    
    def Conv2D_faux_filtre_5x5(x, nbr_filtre,taille_filtre=3):
        x = layers.Conv2D(nbr_filtre, taille_filtre, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        x = layers.Conv2D(nbr_filtre, taille_filtre, padding="same", use_bias=False)(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        return x

    def MaxPool_et_boost(x,pourcentage_inactifs=0.2):
        x = layers.MaxPool2D()(x)
        x = layers.Dropout(pourcentage_inactifs)(x)
        return x

    inputs = keras.Input(shape=shape_poster)
    
    x = Conv2D_faux_filtre_5x5(inputs, 64,5)
    x = MaxPool_et_boost(x)
    x = Conv2D_faux_filtre_5x5(x, 128,3)
    x = MaxPool_et_boost(x,0.3)
    x = Conv2D_faux_filtre_5x5(x, 256,3)
    x = MaxPool_et_boost(x,0.4)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.4)(x)

    x = layers.Dense(512, activation="relu")(x)
    x = layers.Dropout(0.4)(x)

    outputs = layers.Dense(classes_y, activation="sigmoid", dtype="float32")(x)


    model = keras.Model(inputs, outputs, name="model_poster_vers_theme_cnn")
    return model