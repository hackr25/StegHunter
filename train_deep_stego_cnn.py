import os
import cv2
import torch
import random
import numpy as np
from PIL import Image
from tqdm import tqdm
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader

from src.core.deep_stego_cnn import DeepStegoCNN, ResidualPreprocessor


# ============================================================
# DATASET
# ============================================================

class StegoDataset(Dataset):
    def __init__(self, image_paths, labels):
        self.image_paths = image_paths
        self.labels = labels
        self.preprocessor = ResidualPreprocessor()

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert("RGB")
        img = img.resize((128, 128))
        img_array = np.array(img)

        residual = self.preprocessor.process(img_array)
        residual = torch.tensor(residual, dtype=torch.float32)

        label = torch.tensor(self.labels[idx], dtype=torch.long)

        return residual, label


# ============================================================
# DATA LOADER HELPER
# ============================================================

def load_dataset(clean_dir, stego_dir):
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


# ============================================================
# TRAINING LOOP
# ============================================================

def train_model(clean_dir, stego_dir, epochs=15, batch_size=16):
    image_paths, labels = load_dataset(clean_dir, stego_dir)

    X_train, X_val, y_train, y_val = train_test_split(
        image_paths, labels, test_size=0.2, random_state=42, stratify=labels
    )

    train_ds = StegoDataset(X_train, y_train)
    val_ds = StegoDataset(X_val, y_val)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = DeepStegoCNN().to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0005)

    best_acc = 0.0

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for imgs, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            imgs, labels = imgs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        # validation
        model.eval()
        correct = 0
        total = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs, labels = imgs.to(device), labels.to(device)

                outputs = model(imgs)
                _, predicted = torch.max(outputs.data, 1)

                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        acc = 100 * correct / total

        print(f"\nEpoch {epoch+1} Loss: {total_loss:.4f} | Val Accuracy: {acc:.2f}%")

        if acc > best_acc:
            best_acc = acc
            os.makedirs("models", exist_ok=True)
            torch.save(model.state_dict(), "models/deep_stego_cnn.pth")
            print("✔ Saved best model.")

    print(f"\nBest Validation Accuracy: {best_acc:.2f}%")
    print("Training complete.")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    train_model(
        clean_dir="dataset/clean",
        stego_dir="dataset/stego",
        epochs=15,
        batch_size=16
    )