"""
Heatmap Generation for Visual Steganography Detection
"""
import numpy as np
from PIL import Image
import cv2
from typing import Dict, Tuple
from .ml_features import MLFeatureExtractor
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 

class HeatmapGenerator:
    """Generate heatmaps showing suspicious regions in images"""

    def __init__(self):
        self.feature_extractor = MLFeatureExtractor()

    def generate_lsb_heatmap(self, image_path: str) -> np.ndarray:
        """
        Generate heatmap based on LSB entropy
        Returns heatmap as numpy array (no file saving)
        """
        # Load image
        image = Image.open(image_path)
        img_array = np.array(image)

        # Handle RGBA images - convert to RGB for LSB analysis
        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        # Extract LSB plane
        lsb_plane = img_array & 1

        # Calculate local entropy in sliding window
        heatmap = self._sliding_window_entropy(lsb_plane, window_size=16)

        # Normalize to 0-255
        heatmap = self._normalize_heatmap(heatmap)

        # Convert to colormap
        try:
            heatmap_uint8 = heatmap.astype(np.uint8)
            heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
            # Convert BGR to RGB
            heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        except Exception as e:
            # Fallback: convert to RGB
            heatmap_uint8 = heatmap.astype(np.uint8)
            heatmap_colored = cv2.cvtColor(heatmap_uint8, cv2.COLOR_GRAY2RGB)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmap_colored, alpha=0.5)
            result_array = np.array(result)
        except Exception as e:
            # Fallback: just return the heatmap
            result_array = heatmap_colored

        return result_array

    def generate_ml_heatmap(self, image_path: str, model) -> np.ndarray:
        """
        Generate heatmap using ML model predictions on image patches
        Returns heatmap as numpy array (no file saving)
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
                        # Fallback: save to temp file in memory
                        continue  # Skip this patch
                    
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
            heatmap_colored_bgr = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
            # Convert BGR to RGB
            heatmap_colored = cv2.cvtColor(heatmap_colored_bgr, cv2.COLOR_BGR2RGB)
        except Exception as e:
            heatmap_colored = cv2.cvtColor(heatmap.astype(np.uint8), cv2.COLOR_GRAY2RGB)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmap_colored, alpha=0.6)
            result_array = np.array(result)
        except Exception as e:
            result_array = heatmap_colored

        return result_array

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
            heatmap_array = cv2.resize(heatmap_array, (orig_w, orig_h))

        # Handle RGBA images (4 channels)
        if orig_channels == 4:
            # Convert RGBA to RGB (remove alpha channel)
            original_array = cv2.cvtColor(original_array, cv2.COLOR_RGBA2RGB)
            orig_channels = 3

        # Ensure same number of channels
        if heatmap_channels != orig_channels:
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

        try:
            blended = cv2.addWeighted(original_array, beta, heatmap_array, alpha, 0)
        except Exception as e:
            # If blending fails, just show the heatmap
            blended = heatmap_array

        return Image.fromarray(blended)

    def generate_comprehensive_heatmap(self, image_path: str) -> Dict[str, np.ndarray]:
        """
        Generate multiple heatmaps and combine them
        Returns dictionary of different heatmaps (no file saving)
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
            heatmaps['lsb'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Pixel variance heatmap
        try:
            variance_heatmap = self._generate_variance_heatmap(img_array_rgb)
            heatmaps['variance'] = variance_heatmap
        except Exception as e:
            heatmaps['variance'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Edge detection heatmap
        try:
            edge_heatmap = self._generate_edge_heatmap(img_array_rgb)
            heatmaps['edge'] = edge_heatmap
        except Exception as e:
            heatmaps['edge'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Combined heatmap
        try:
            combined_heatmap = self._combine_heatmaps(heatmaps)
            heatmaps['combined'] = combined_heatmap
        except Exception as e:
            heatmaps['combined'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        # Blend with original image
        try:
            result = self._blend_images(image, heatmaps['combined'], alpha=0.6)
            result_array = np.array(result)
            heatmaps['blended'] = result_array
        except Exception as e:
            pass

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
    
    def generate_ela_heatmap(self, image_path: str, quality: int = 95,
                          scale: int = 10, output_path: str = None) -> np.ndarray:
        """
        Error Level Analysis heatmap.
        Re-saves at known JPEG quality, computes |original - recompressed| * scale.
        Regions with different error levels than surroundings = tampering signal.
        Returns BGR numpy array (cv2 convention) for display.
        """
        orig = Image.open(image_path).convert('RGB')
        buf = BytesIO()
        orig.save(buf, 'JPEG', quality=quality)
        buf.seek(0)
        recomp = Image.open(buf).convert('RGB')

        orig_arr   = np.array(orig,   dtype=np.float32)
        recomp_arr = np.array(recomp, dtype=np.float32)

        ela = np.abs(orig_arr - recomp_arr) * scale
        ela = np.clip(ela, 0, 255).astype(np.uint8)

        # Convert to grayscale for colormap
        ela_gray = cv2.cvtColor(ela, cv2.COLOR_RGB2GRAY)
        ela_colored = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)

        if output_path:
            cv2.imwrite(output_path, ela_colored)

        return ela_colored

    def ela_score(self, image_path: str, quality: int = 95, scale: int = 10) -> Dict:
        """
        Compute ELA statistics. Returns mean, max, std and suspicion score.
        High mean = uniform manipulation. High std = localised forgery patch.
        """
        orig = Image.open(image_path).convert('RGB')
        buf = BytesIO()
        orig.save(buf, 'JPEG', quality=quality)
        buf.seek(0)
        recomp = Image.open(buf).convert('RGB')

        ela = np.abs(
            np.array(orig,   dtype=np.float32) -
            np.array(recomp, dtype=np.float32)
        ) * scale

        ela_mean = float(np.mean(ela))
        ela_max  = float(np.max(ela))
        ela_std  = float(np.std(ela))

        # Heuristic: high mean alone = compression artefact, not forgery.
        # High std relative to mean = localised bright patch = suspicious.
        ratio = ela_std / (ela_mean + 1e-8)
        suspicion_score = min(100.0, ela_mean * 1.5 + ratio * 30.0)

        return {
            'ela_mean': round(ela_mean, 3),
            'ela_max':  round(ela_max, 3),
            'ela_std':  round(ela_std, 3),
            'ela_ratio': round(ratio, 4),
            'suspicion_score': round(suspicion_score, 2),
        }

    def generate_noise_heatmap(self, image_path: str,
                                block_size: int = 32, output_path: str = None) -> np.ndarray:
        """
        Laplacian noise estimation map.
        Each block gets a score = std(Laplacian(block)).
        Blocks with anomalous noise vs the image median = splice boundary signal.
        Returns BGR numpy array.
        """
        image = Image.open(image_path).convert('RGB')
        img_arr = np.array(image)
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        noise_map = np.zeros((h, w), dtype=np.float32)

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = gray[y:y+block_size, x:x+block_size]
                if block.size == 0:
                    continue
                lap = cv2.Laplacian(block, cv2.CV_64F)
                noise_map[y:y+block_size, x:x+block_size] = np.std(lap)

        # Normalize and colorize
        noise_norm = self._normalize_heatmap(noise_map)
        noise_colored = cv2.applyColorMap(noise_norm, cv2.COLORMAP_HOT)

        # Blend with original
        result = self._blend_images(image, noise_colored, alpha=0.55)
        result_arr = np.array(result)
        result_bgr = cv2.cvtColor(result_arr, cv2.COLOR_RGB2BGR)

        if output_path:
            cv2.imwrite(output_path, result_bgr)

        return result_bgr

    def generate_lga_heatmap(self, image_path: str, output_path: str = None) -> np.ndarray:
        """
        Local Gradient Analysis (LGA) heatmap using Sobel operator.
        Highlights sharp gradient discontinuities — splice seams show as
        bright lines where the gradient magnitude is anomalously high.
        Returns BGR numpy array.
        """
        image = Image.open(image_path).convert('RGB')
        img_arr = np.array(image)
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)

        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient = np.sqrt(sobel_x**2 + sobel_y**2)

        gradient_norm = self._normalize_heatmap(gradient)
        lga_colored = cv2.applyColorMap(gradient_norm, cv2.COLORMAP_MAGMA)

        if output_path:
            cv2.imwrite(output_path, lga_colored)

        return lga_colored

    def generate_ghost_heatmap(self, image_path: str,
                                qualities: list = None, output_path: str = None) -> Dict:
        """
        JPEG Ghost heatmap.
        Re-compresses at multiple quality levels. Per-pixel minimum error quality
        is mapped as a colour — regions with different origin quality = forgery signal.
        Returns dict with 'ghost_map' (BGR array), 'ghost_quality', 'ghost_variance'.
        Only meaningful for JPEG source images.
        """
        if qualities is None:
            qualities = [50, 65, 75, 85, 95]

        orig = Image.open(image_path).convert('L')
        orig_arr = np.array(orig, dtype=np.float32)

        diff_maps = []
        for q in qualities:
            buf = BytesIO()
            Image.fromarray(orig_arr.astype(np.uint8)).save(buf, 'JPEG', quality=q)
            buf.seek(0)
            recomp = np.array(Image.open(buf), dtype=np.float32)
            diff = (orig_arr - recomp) ** 2
            diff_maps.append(diff)

        stack = np.stack(diff_maps, axis=0)               # (Q, H, W)
        best_q_idx = np.argmin(stack, axis=0).astype(np.float32)  # which Q wins per pixel
        quality_scores = {q: float(np.mean(diff_maps[i]))
                        for i, q in enumerate(qualities)}
        ghost_q = qualities[int(np.argmin([quality_scores[q] for q in qualities]))]
        ghost_variance = float(np.std(best_q_idx))

        # Colorize the best-Q index map
        idx_norm = self._normalize_heatmap(best_q_idx)
        ghost_colored = cv2.applyColorMap(idx_norm, cv2.COLORMAP_RAINBOW)

        if output_path:
            cv2.imwrite(output_path, ghost_colored)

        return {
            'ghost_map': ghost_colored,
            'ghost_quality': ghost_q,
            'ghost_variance': round(ghost_variance, 4),
            'quality_scores': quality_scores,
            'suspicion_score': round(min(100.0, ghost_variance * 15.0), 2),
        }

    def generate_dct_heatmap(self, image_path: str, output_path: str = None) -> np.ndarray:
        """
        DCT energy map heatmap.
        Shows per-block mean absolute AC DCT coefficient energy.
        Blocks with anomalously high energy may indicate embedded data.
        Returns BGR numpy array.
        """
        from scipy import fftpack

        image = Image.open(image_path).convert('L')
        img_arr = np.array(image, dtype=np.float32)
        h, w = img_arr.shape
        block_size = 8
        map_h = h // block_size
        map_w = w // block_size

        dct_map = np.zeros((map_h, map_w), dtype=np.float32)
        for bi in range(map_h):
            for bj in range(map_w):
                i, j = bi * block_size, bj * block_size
                block = img_arr[i:i+block_size, j:j+block_size]
                dct_block = fftpack.dct(
                    fftpack.dct(block, axis=0, norm='ortho'),
                    axis=1, norm='ortho'
                )
                dct_map[bi, bj] = float(np.mean(np.abs(dct_block.flatten()[1:])))

        # Upscale map back to full image size
        dct_full = cv2.resize(dct_map, (w, h), interpolation=cv2.INTER_NEAREST)
        dct_norm = self._normalize_heatmap(dct_full)
        dct_colored = cv2.applyColorMap(dct_norm, cv2.COLORMAP_JET)

        if output_path:
            cv2.imwrite(output_path, dct_colored)

        return dct_colored
