"""
Heatmap Generation for Visual Steganography Detection
"""
import numpy as np
from PIL import Image
import cv2
from typing import Dict, Tuple
from .ml_features import MLFeatureExtractor

class HeatmapGenerator:
    """Generate heatmaps showing suspicious regions in images"""

    def __init__(self):
        self.feature_extractor = MLFeatureExtractor()

    def generate_lsb_heatmap(self, image_path: str, output_path: str = None) -> np.ndarray:
        """
        Generate heatmap based on LSB entropy
        Returns heatmap as numpy array
        """
        # Load image
        image = Image.open(image_path)
        img_array = np.array(image)

        print(f"DEBUG: Original image shape: {img_array.shape}")

        # Handle RGBA images - convert to RGB for LSB analysis
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            print(f"DEBUG: Converted RGBA to RGB: {img_array.shape}")

        # Extract LSB plane
        lsb_plane = img_array & 1

        # Calculate local entropy in sliding window
        heatmap = self._sliding_window_entropy(lsb_plane, window_size=16)

        print(f"DEBUG: Heatmap before normalization: {heatmap.shape}, dtype: {heatmap.dtype}")

        # Normalize to 0-255
        heatmap = self._normalize_heatmap(heatmap)

        print(f"DEBUG: Heatmap after normalization: {heatmap.shape}, dtype: {heatmap.dtype}, range: {heatmap.min()}-{heatmap.max()}")

        # Convert to colormap
        try:
            heatmap_uint8 = heatmap.astype(np.uint8)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            print(f"DEBUG: Colormap applied, shape: {heatmap_colored.shape}")
        except Exception as e:
            print(f"ERROR: Could not apply colormap: {e}")
            # Fallback: convert to RGB
            heatmap_colored = cv2.cvtColor(heatmap_uint8, cv2.COLOR_GRAY2RGB)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmap_colored, alpha=0.5)
            print(f"DEBUG: Result shape: {np.array(result).shape}")
        except Exception as e:
            print(f"ERROR: Blend failed: {e}")
            # Fallback: just return the heatmap
            result = Image.fromarray(heatmap_colored)

        if output_path:
            try:
                result.save(output_path)
                print(f"DEBUG: Saved heatmap to {output_path}")
            except Exception as e:
                print(f"ERROR: Failed to save heatmap: {e}")

        return heatmap_colored

    def generate_ml_heatmap(self, image_path: str, model, output_path: str = None) -> np.ndarray:
        """
        Generate heatmap using ML model predictions on image patches
        """
        # Load image
        image = Image.open(image_path)
        img_array = np.array(image)

        # Handle RGBA images
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        # Divide image into patches
        patch_size = 64
        stride = 32
        h, w = img_array.shape[:2]

        # Initialize heatmap
        heatmap = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.float32)

        # Disable parallel processing temporarily if possible
        original_n_jobs = None
        if hasattr(model.model, 'n_jobs'):
            original_n_jobs = model.model.n_jobs
            model.model.n_jobs = 1

        # Process patches
        for i in range(0, h - patch_size + 1, stride):
            for j in range(0, w - patch_size + 1, stride):
                try:
                    # Extract patch
                    patch = img_array[i:i+patch_size, j:j+patch_size]

                    # Skip if patch is too small
                    if patch.shape[0] < patch_size or patch.shape[1] < patch_size:
                        continue

                    # Extract features directly without saving to disk
                    if hasattr(model.feature_extractor, 'extract_features_from_array'):
                        features = model.feature_extractor.extract_features_from_array(patch)
                    else:
                        # Fallback: save to temp file
                        patch_img = Image.fromarray(patch)
                        temp_path = f'temp_patch_{i}_{j}.png'
                        try:
                            patch_img.save(temp_path)
                            result = model.predict(temp_path)
                            probability = result['probability']
                        finally:
                            import os
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        # Add to heatmap
                        end_i = min(i+patch_size, h)
                        end_j = min(j+patch_size, w)
                        heatmap[i:end_i, j:end_j] += probability
                        count_map[i:end_i, j:end_j] += 1
                        continue
                    
                    # Scale features
                    if model.scaler is not None:
                        features = model.scaler.transform(features.reshape(1, -1))
                    
                    # Get prediction
                    if hasattr(model.model, 'predict_proba'):
                        probability = model.model.predict_proba(features)[0][1]  # Probability of stego
                    else:
                        probability = float(model.model.predict(features)[0])
                    
                    # Add to heatmap
                    end_i = min(i+patch_size, h)
                    end_j = min(j+patch_size, w)
                    heatmap[i:end_i, j:end_j] += probability
                    count_map[i:end_i, j:end_j] += 1
                    
                except Exception as e:
                    print(f"ERROR: Failed to process patch at ({i}, {j}): {e}")
                    continue

        # Restore original n_jobs
        if original_n_jobs is not None:
            model.model.n_jobs = original_n_jobs

        # Average overlapping patches
        with np.errstate(divide='ignore', invalid='ignore'):
            heatmap = np.divide(heatmap, count_map, out=np.zeros_like(heatmap), where=count_map!=0)

        # Normalize to 0-255
        heatmap = self._normalize_heatmap(heatmap * 255)

        # Apply colormap
        try:
            heatmap_colored = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
        except Exception as e:
            print(f"ERROR: Could not apply colormap: {e}")
            heatmap_colored = cv2.cvtColor(heatmap.astype(np.uint8), cv2.COLOR_GRAY2RGB)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmap_colored, alpha=0.6)
        except Exception as e:
            print(f"ERROR: Blend failed: {e}")
            result = Image.fromarray(heatmap_colored)

        if output_path:
            try:
                result.save(output_path)
            except Exception as e:
                print(f"ERROR: Failed to save heatmap: {e}")

        return heatmap_colored

    def _sliding_window_entropy(self, image: np.ndarray, window_size: int = 16) -> np.ndarray:
        """Calculate entropy in sliding windows"""
        if len(image.shape) == 3:
            # Convert to grayscale if needed
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        h, w = gray.shape
        heatmap = np.zeros((h, w), dtype=np.float32)

        for i in range(0, h - window_size + 1, window_size):
            for j in range(0, w - window_size + 1, window_size):
                window = gray[i:i+window_size, j:j+window_size]
                entropy_val = self._calculate_entropy(window)
                heatmap[i:i+window_size, j:j+window_size] = entropy_val

        return heatmap

    def _calculate_entropy(self, image: np.ndarray) -> float:
        """Calculate entropy of image region"""
        from scipy.stats import entropy
        counts = np.bincount(image.ravel())
        probabilities = counts / counts.sum()
        return entropy(probabilities, base=2)

    def _normalize_heatmap(self, heatmap: np.ndarray) -> np.ndarray:
        """Normalize heatmap to 0-255"""
        if np.max(heatmap) == np.min(heatmap):
            return np.zeros_like(heatmap, dtype=np.uint8)
        return ((heatmap - np.min(heatmap)) / (np.max(heatmap) - np.min(heatmap)) * 255).astype(np.uint8)

    def _apply_colormap(self, heatmap: np.ndarray) -> np.ndarray:
        """Apply jet colormap to heatmap"""
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        return heatmap_colored

    def _blend_images(self, original: Image.Image, heatmap: np.ndarray, alpha: float = 0.5) -> Image.Image:
        """Blend original image with heatmap"""
        original_array = np.array(original)
        heatmap_array = heatmap.copy()

        # Get original dimensions
        orig_h, orig_w = original_array.shape[:2]
        orig_channels = len(original_array.shape) if len(original_array.shape) == 3 else 1

        # Ensure heatmap has same dimensions
        heatmap_h, heatmap_w = heatmap_array.shape[:2]
        heatmap_channels = len(heatmap_array.shape) if len(heatmap_array.shape) == 3 else 1

        # Resize heatmap to match original dimensions
        if heatmap_h != orig_h or heatmap_w != orig_w:
            print(f"DEBUG: Resizing heatmap from ({heatmap_h}, {heatmap_w}) to ({orig_h}, {orig_w})")
            heatmap_array = cv2.resize(heatmap_array, (orig_w, orig_h))

        # Handle RGBA images (4 channels)
        if orig_channels == 4:
            print("DEBUG: Converting RGBA to RGB")
            # Convert RGBA to RGB (remove alpha channel)
            original_array = cv2.cvtColor(original_array, cv2.COLOR_RGBA2RGB)
            orig_channels = 3

        # Ensure same number of channels
        if heatmap_channels != orig_channels:
            print(f"DEBUG: Converting from {heatmap_channels} to {orig_channels} channels")
            if orig_channels == 1:
                # Convert to grayscale
                if heatmap_channels == 3:
                    heatmap_array = cv2.cvtColor(heatmap_array, cv2.COLOR_BGR2GRAY)
                else:
                    heatmap_array = heatmap_array.astype(np.uint8)
            else:  # orig_channels == 3
                # Convert to RGB
                if heatmap_channels == 1:
                    heatmap_array = cv2.cvtColor(heatmap_array, cv2.COLOR_GRAY2RGB)
                elif heatmap_channels == 3:
                    # Ensure RGB format (convert from BGR if needed)
                    heatmap_array = cv2.cvtColor(heatmap_array, cv2.COLOR_BGR2RGB)

        # Ensure same data type
        heatmap_array = heatmap_array.astype(np.uint8)
        original_array = original_array.astype(np.uint8)

        # Blend with proper alpha range (0.0 to 1.0)
        alpha = max(0.0, min(1.0, alpha))
        beta = 1.0 - alpha

        print(f"DEBUG: Blending shapes - Original: {original_array.shape}, Heatmap: {heatmap_array.shape}")
        print(f"DEBUG: Alpha: {alpha}, Beta: {beta}")

        try:
            blended = cv2.addWeighted(original_array, beta, heatmap_array, alpha, 0)
            print("DEBUG: Blend successful")
        except Exception as e:
            print(f"ERROR: Blend failed: {e}")
            # If blending fails, just show the heatmap
            blended = heatmap_array

        return Image.fromarray(blended)

    def generate_comprehensive_heatmap(self, image_path: str, output_path: str = None) -> Dict[str, np.ndarray]:
        """
        Generate multiple heatmaps and combine them
        Returns dictionary of different heatmaps
        """
        image = Image.open(image_path)
        img_array = np.array(image)

        # Handle RGBA images
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        else:
            img_array_rgb = img_array

        heatmaps = {}

        # LSB entropy heatmap
        try:
            lsb_heatmap = self.generate_lsb_heatmap(image_path)
            heatmaps['lsb'] = lsb_heatmap
        except Exception as e:
            print(f"WARNING: LSB heatmap generation failed: {e}")
            heatmaps['lsb'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Pixel variance heatmap
        try:
            variance_heatmap = self._generate_variance_heatmap(img_array_rgb)
            heatmaps['variance'] = variance_heatmap
        except Exception as e:
            print(f"WARNING: Variance heatmap generation failed: {e}")
            heatmaps['variance'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Edge detection heatmap
        try:
            edge_heatmap = self._generate_edge_heatmap(img_array_rgb)
            heatmaps['edge'] = edge_heatmap
        except Exception as e:
            print(f"WARNING: Edge heatmap generation failed: {e}")
            heatmaps['edge'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Combined heatmap
        try:
            combined_heatmap = self._combine_heatmaps(heatmaps)
            heatmaps['combined'] = combined_heatmap
        except Exception as e:
            print(f"WARNING: Combined heatmap generation failed: {e}")
            heatmaps['combined'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmaps['combined'], alpha=0.6)
        except Exception as e:
            print(f"WARNING: Failed to blend combined heatmap: {e}")
            result = Image.fromarray(heatmaps['combined'])

        if output_path:
            try:
                result.save(output_path)
            except Exception as e:
                print(f"WARNING: Failed to save combined heatmap: {e}")

        return heatmaps

    def _generate_variance_heatmap(self, img_array: np.ndarray) -> np.ndarray:
        """Generate heatmap based on pixel variance"""
        # Calculate local variance
        if len(img_array.shape) == 3:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Calculate variance using sliding window
        window_size = 16
        h, w = gray.shape
        variance_heatmap = np.zeros((h, w), dtype=np.float32)

        for i in range(0, h - window_size + 1, window_size):
            for j in range(0, w - window_size + 1, window_size):
                window = gray[i:i+window_size, j:j+window_size]
                variance = np.var(window)
                variance_heatmap[i:i+window_size, j:j+window_size] = variance

        # Normalize to 0-255 and convert to uint8
        if np.max(variance_heatmap) == np.min(variance_heatmap):
            variance_heatmap = np.zeros((h, w), dtype=np.uint8)
        else:
            variance_heatmap = ((variance_heatmap - np.min(variance_heatmap)) / 
                               (np.max(variance_heatmap) - np.min(variance_heatmap)) * 255).astype(np.uint8)

        # Apply colormap
        try:
            variance_heatmap_colored = cv2.applyColorMap(variance_heatmap, cv2.COLORMAP_JET)
        except Exception as e:
            print(f"ERROR: Could not apply colormap: {e}")
            variance_heatmap_colored = cv2.cvtColor(variance_heatmap, cv2.COLOR_GRAY2RGB)

        return variance_heatmap_colored

    def _generate_edge_heatmap(self, img_array: np.ndarray) -> np.ndarray:
        """Generate heatmap based on edge detection"""
        if len(img_array.shape) == 3:
            # Handle RGBA images
            if img_array.shape[2] == 4:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)
            else:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Calculate edges
        edges = cv2.Canny(gray, 100, 200)

        # Apply colormap
        edge_heatmap = cv2.applyColorMap(edges, cv2.COLORMAP_HOT)
        return edge_heatmap

    def _combine_heatmaps(self, heatmaps: Dict[str, np.ndarray]) -> np.ndarray:
        """Combine multiple heatmaps"""
        # Normalize all heatmaps
        normalized = []
        for name, heatmap in heatmaps.items():
            if len(heatmap.shape) == 3:
                # Convert to grayscale
                gray = cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY)
            else:
                gray = heatmap
            normalized.append(gray.astype(np.float32) / 255.0)

        # Average
        combined = np.mean(normalized, axis=0)

        # Scale back to 0-255
        combined = (combined * 255).astype(np.uint8)

        # Apply colormap
        return self._apply_colormap(combined)
