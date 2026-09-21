"""Auto-encodeur convolutif (TensorFlow/Keras) pour la détection d'anomalies par reconstruction.

Architecture strictement équivalente à `indusense.vision.autoencoder_torch.ConvAutoencoder`
(mêmes tailles de noyau, strides et canaux) afin de comparer équitablement les deux frameworks.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


def build_autoencoder(image_size: int, base_channels: int = 64) -> keras.Model:
    c = base_channels
    inputs = keras.Input(shape=(image_size, image_size, 3))

    x = layers.Conv2D(c, 3, strides=2, padding="same", activation="relu")(inputs)
    x = layers.Conv2D(c * 2, 3, strides=2, padding="same", activation="relu")(x)
    x = layers.Conv2D(c * 4, 3, strides=2, padding="same", activation="relu")(x)

    x = layers.Conv2DTranspose(c * 2, 3, strides=2, padding="same", activation="relu")(x)
    x = layers.Conv2DTranspose(c, 3, strides=2, padding="same", activation="relu")(x)
    outputs = layers.Conv2DTranspose(3, 3, strides=2, padding="same", activation="sigmoid")(x)

    return keras.Model(inputs, outputs, name="conv_autoencoder")


def count_trainable_parameters(model: tf.keras.Model) -> int:
    return int(sum(tf.keras.backend.count_params(w) for w in model.trainable_weights))
