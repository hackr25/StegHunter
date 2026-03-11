"""
Deep Learning-based Steganalysis using CNN
"""
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import os
from pathlib import Path
import time
import json  # Ensure json is imported

class CNNSteganalysis:
    """CNN-based steganalysis model"""
    
    def __init__(self):
        # CRITICAL FIX: Define img_size before using it
        self.img_size = 128
        self.model = self._build_model()
        self.history = None
        self.batch_size = 32
        self.epochs = 20
    
    def _build_model(self):
        """Build CNN model architecture"""
        model = models.Sequential([
            layers.Conv2D(32, (3, 3), activation='relu', input_shape=(self.img_size, self.img_size, 3)),
            layers.BatchNormalization(),
            layers.MaxPooling2D(2, 2),
            layers.Conv2D(64, (3, 3), activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling2D(2, 2),
            layers.Conv2D(128, (3, 3), activation='relu'),
            layers.BatchNormalization(),
            layers.MaxPooling2D(2, 2),
            layers.Flatten(),
            layers.Dense(256, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _load_and_preprocess_image(self, image_path, label):
        """Load and preprocess a single image"""
        try:
            img = Image.open(image_path)
            img = img.resize((self.img_size, self.img_size))
            img_array = np.array(img)
            
            # Convert to 3 channels if needed
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array]*3, axis=-1)
            elif img_array.shape[2] == 1:
                img_array = np.concatenate([img_array]*3, axis=-1)
            
            img_array = img_array / 255.0
            return img_array, label
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            return None, None
    
    def _create_datasets(self, clean_images, stego_images):
        """Create training and validation datasets"""
        # Prepare data
        all_images = []
        all_labels = []
        
        # Add clean images (label 0)
        for img_path in clean_images:
            img, label = self._load_and_preprocess_image(img_path, 0)
            if img is not None:
                all_images.append(img)
                all_labels.append(label)
        
        # Add stego images (label 1)
        for img_path in stego_images:
            img, label = self._load_and_preprocess_image(img_path, 1)
            if img is not None:
                all_images.append(img)
                all_labels.append(label)
        
        # Convert to arrays
        X = np.array(all_images)
        y = np.array(all_labels)
        
        # Split into training and validation
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        return X_train, X_val, y_train, y_val
    
    def train_model(self, clean_images, stego_images):
        """Train the CNN model"""
        start_time = time.time()
        
        # Create datasets
        X_train, X_val, y_train, y_val = self._create_datasets(clean_images, stego_images)
        
        # Data augmentation
        datagen = ImageDataGenerator(
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest'
        )
        
        # Train model
        self.history = self.model.fit(
            datagen.flow(X_train, y_train, batch_size=self.batch_size),
            steps_per_epoch=len(X_train) // self.batch_size,
            epochs=self.epochs,
            validation_data=(X_val, y_val)
        )
        
        # Calculate metrics
        train_loss, train_acc = self.model.evaluate(X_train, y_train, verbose=0)
        val_loss, val_acc = self.model.evaluate(X_val, y_val, verbose=0)
        
        # Generate predictions for metrics
        y_pred = (self.model.predict(X_val) > 0.5).astype("int32").flatten()
        
        # Calculate metrics
        from sklearn.metrics import precision_score, recall_score, f1_score
        
        metrics = {
            'accuracy': val_acc,
            'precision': precision_score(y_val, y_pred, zero_division=0),
            'recall': recall_score(y_val, y_pred, zero_division=0),
            'f1_score': f1_score(y_val, y_pred, zero_division=0),
            'train_accuracy': train_acc,
            'validation_accuracy': val_acc,
            'training_time': time.time() - start_time
        }
        
        return metrics
    
    def predict(self, image_path):
        """Predict if image contains steganography"""
        try:
            # Load and preprocess image
            img = Image.open(image_path)
            img = img.resize((self.img_size, self.img_size))
            
            # Convert to array and normalize
            img_array = np.array(img)
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array]*3, axis=-1)
            elif img_array.shape[2] == 1:
                img_array = np.concatenate([img_array]*3, axis=-1)
            
            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            
            # Predict
            prediction = self.model.predict(img_array, verbose=0)[0][0]
            return float(prediction)
            
        except Exception as e:
            print(f"Error predicting {image_path}: {e}")
            return 0.5
    
    def save_model(self, path):
        """Save the CNN model"""
        self.model.save(path)
    
    def load_model(self, path):
        """Load a saved CNN model"""
        self.model = tf.keras.models.load_model(path)
