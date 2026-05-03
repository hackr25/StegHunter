import os
import cv2
import random
import numpy as np
import tensorflow as tf
from PIL import Image
from tqdm import tqdm
from sklearn.model_selection import train_test_split

from src.core.deep_stego_cnn import ResidualPreprocessor


# ---------------------------------------------------------
# DATASET LOADING
# ---------------------------------------------------------

def collect_images(clean_dir, stego_dir):
    image_paths = []
    labels = []

    for f in os.listdir(clean_dir):
        fp = os.path.join(clean_dir, f)
        if os.path.isfile(fp):
            image_paths.append(fp)
            labels.append(0)

    for f in os.listdir(stego_dir):
        fp = os.path.join(stego_dir, f)
        if os.path.isfile(fp):
            image_paths.append(fp)
            labels.append(1)

    combined = list(zip(image_paths, labels))
    random.shuffle(combined)

    image_paths, labels = zip(*combined)
    return list(image_paths), list(labels)


# ---------------------------------------------------------
# PREPROCESS
# ---------------------------------------------------------

def preprocess_dataset(paths):
    prep = ResidualPreprocessor()
    X = []

    for p in tqdm(paths, desc="Preprocessing Images"):
        try:
            img = Image.open(p).convert("RGB")
            img = img.resize((128, 128))
            img_array = np.array(img)

            residual = prep.process(img_array)
            X.append(residual)
        except Exception:
            continue

    return np.array(X, dtype=np.float32)


# ---------------------------------------------------------
# MODEL
# ---------------------------------------------------------

def build_model():
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(128, 128, 3)),

        tf.keras.layers.Conv2D(16, (3,3), padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2,2)),

        tf.keras.layers.Conv2D(32, (3,3), padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2,2)),

        tf.keras.layers.Conv2D(64, (3,3), padding="same", activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.MaxPooling2D((2,2)),

        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(2, activation="softmax")
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    return model


# ---------------------------------------------------------
# TRAINING
# ---------------------------------------------------------

def train(clean_dir="dataset/clean", stego_dir="dataset/stego", epochs=12):
    image_paths, labels = collect_images(clean_dir, stego_dir)

    X = preprocess_dataset(image_paths)
    y = np.array(labels[:len(X)])

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = build_model()

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=16
    )

    os.makedirs("models", exist_ok=True)
    model.save_weights("models/deep_stego_cnn.h5")

    print("\n✔ Model saved to models/deep_stego_cnn.h5")


if __name__ == "__main__":
    train()