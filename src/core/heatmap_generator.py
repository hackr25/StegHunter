"""
Heatmap Generation for Visual Steganography Detection
Enterprise Final Merged Version
"""
import numpy as np
from PIL import Image
import cv2
from typing import Dict, Tuple, Any
from .ml_features import MLFeatureExtractor
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class HeatmapGenerator:
    """Generate enterprise-grade heatmaps showing suspicious regions in images"""

    def __init__(self):
        self.feature_extractor = MLFeatureExtractor()

    # =========================================================
    # BASIC ENTROPY / NORMALIZATION HELPERS
    # =========================================================
    def _calculate_entropy(self, image: np.ndarray) -> float:
        from scipy.stats import entropy
        counts = np.bincount(image.ravel())
        probabilities = counts / (counts.sum() + 1e-8)
        return entropy(probabilities, base=2)

    def _normalize_heatmap(self, heatmap: np.ndarray) -> np.ndarray:
        if np.max(heatmap) == np.min(heatmap):
            return np.zeros_like(heatmap, dtype=np.uint8)
        return ((heatmap - np.min(heatmap)) /
                (np.max(heatmap) - np.min(heatmap)) * 255).astype(np.uint8)

    def _apply_colormap(self, heatmap: np.ndarray) -> np.ndarray:
        return cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    def _blend_images(self, original: Image.Image, heatmap: np.ndarray, alpha: float = 0.5) -> Image.Image:
        original_array = np.array(original)
        heatmap_array = heatmap.copy()

        orig_h, orig_w = original_array.shape[:2]

        if heatmap_array.shape[:2] != (orig_h, orig_w):
            heatmap_array = cv2.resize(heatmap_array, (orig_w, orig_h))

        if len(original_array.shape) == 3 and original_array.shape[2] == 4:
            original_array = cv2.cvtColor(original_array, cv2.COLOR_RGBA2RGB)

        if len(heatmap_array.shape) == 2:
            heatmap_array = cv2.cvtColor(heatmap_array, cv2.COLOR_GRAY2RGB)

        if len(heatmap_array.shape) == 3:
            heatmap_array = cv2.cvtColor(heatmap_array, cv2.COLOR_BGR2RGB)

        original_array = original_array.astype(np.uint8)
        heatmap_array = heatmap_array.astype(np.uint8)

        alpha = max(0.0, min(1.0, alpha))
        beta = 1.0 - alpha

        try:
            blended = cv2.addWeighted(original_array, beta, heatmap_array, alpha, 0)
        except Exception:
            blended = heatmap_array

        return Image.fromarray(blended)

    # =========================================================
    # LSB HEATMAP
    # =========================================================
    def _sliding_window_entropy(self, image: np.ndarray, window_size: int = 16) -> np.ndarray:
        if len(image.shape) == 3:
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

    def generate_lsb_heatmap(self, image_path: str) -> np.ndarray:
        image = Image.open(image_path)
        img_array = np.array(image)

        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        lsb_plane = img_array & 1
        heatmap = self._sliding_window_entropy(lsb_plane, window_size=16)
        heatmap = self._normalize_heatmap(heatmap)

        heatmap_colored = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

        result = self._blend_images(image, heatmap_colored, alpha=0.5)
        return np.array(result)

    # =========================================================
    # ML PATCH HEATMAP
    # =========================================================
    def generate_ml_heatmap(self, image_path: str, model) -> np.ndarray:
        image = Image.open(image_path)
        img_array = np.array(image)

        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

        patch_size = 64
        stride = 32
        h, w = img_array.shape[:2]

        heatmap = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.float32)

        original_n_jobs = None
        if hasattr(model.model, 'n_jobs'):
            original_n_jobs = model.model.n_jobs
            model.model.n_jobs = 1

        for i in range(0, h - patch_size + 1, stride):
            for j in range(0, w - patch_size + 1, stride):
                try:
                    patch = img_array[i:i+patch_size, j:j+patch_size]

                    if hasattr(model.feature_extractor, 'extract_features_from_array'):
                        features = model.feature_extractor.extract_features_from_array(patch)
                    else:
                        continue

                    if model.scaler is not None:
                        features = model.scaler.transform(features.reshape(1, -1))

                    if hasattr(model.model, 'predict_proba'):
                        probability = model.model.predict_proba(features)[0][1]
                    else:
                        probability = float(model.model.predict(features)[0])

                    heatmap[i:i+patch_size, j:j+patch_size] += probability
                    count_map[i:i+patch_size, j:j+patch_size] += 1
                except Exception:
                    continue

        if original_n_jobs is not None:
            model.model.n_jobs = original_n_jobs

        with np.errstate(divide='ignore', invalid='ignore'):
            heatmap = np.divide(heatmap, count_map, out=np.zeros_like(heatmap), where=count_map != 0)

        heatmap = self._normalize_heatmap(heatmap * 255)
        heatmap_colored = cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

        result = self._blend_images(image, heatmap_colored, alpha=0.6)
        return np.array(result)

    # =========================================================
    # LEGACY COMPREHENSIVE MULTI-HEATMAP
    # =========================================================
    def generate_comprehensive_heatmap(self, image_path: str) -> Dict[str, np.ndarray]:
        image = Image.open(image_path)
        img_array = np.array(image)

        if len(img_array.shape) == 3 and img_array.shape[2] == 4:
            img_array_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        else:
            img_array_rgb = img_array

        heatmaps = {}

        try:
            heatmaps['lsb'] = self.generate_lsb_heatmap(image_path)
        except Exception:
            heatmaps['lsb'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        try:
            heatmaps['variance'] = self._generate_variance_heatmap(img_array_rgb)
        except Exception:
            heatmaps['variance'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        try:
            heatmaps['edge'] = self._generate_edge_heatmap(img_array_rgb)
        except Exception:
            heatmaps['edge'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        try:
            heatmaps['combined'] = self._combine_heatmaps(heatmaps)
        except Exception:
            heatmaps['combined'] = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)

        try:
            result = self._blend_images(image, heatmaps['combined'], alpha=0.6)
            heatmaps['blended'] = np.array(result)
        except Exception:
            pass

        return heatmaps

    def _generate_variance_heatmap(self, img_array: np.ndarray) -> np.ndarray:
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        window_size = 16
        h, w = gray.shape
        variance_heatmap = np.zeros((h, w), dtype=np.float32)

        for i in range(0, h - window_size + 1, window_size):
            for j in range(0, w - window_size + 1, window_size):
                window = gray[i:i+window_size, j:j+window_size]
                variance_heatmap[i:i+window_size, j:j+window_size] = np.var(window)

        variance_heatmap = self._normalize_heatmap(variance_heatmap)
        return cv2.applyColorMap(variance_heatmap, cv2.COLORMAP_JET)

    def _generate_edge_heatmap(self, img_array: np.ndarray) -> np.ndarray:
        if len(img_array.shape) == 3:
            if img_array.shape[2] == 4:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGBA2GRAY)
            else:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        edges = cv2.Canny(gray, 100, 200)
        return cv2.applyColorMap(edges, cv2.COLORMAP_JET)

    def _combine_heatmaps(self, heatmaps: Dict[str, np.ndarray]) -> np.ndarray:
        normalized = []

        for _, heatmap in heatmaps.items():
            if len(heatmap.shape) == 3:
                gray = cv2.cvtColor(heatmap, cv2.COLOR_BGR2GRAY)
            else:
                gray = heatmap
            normalized.append(gray.astype(np.float32) / 255.0)

        combined = np.mean(normalized, axis=0)
        combined = (combined * 255).astype(np.uint8)
        return self._apply_colormap(combined)
    
        # =========================================================
    # ERROR LEVEL ANALYSIS HEATMAP
    # =========================================================
    def generate_ela_heatmap(
        self,
        image_path: str,
        quality: int = 95,
        scale: int = 10,
        output_path: str = None
    ) -> np.ndarray:
        orig = Image.open(image_path).convert('RGB')

        buf = BytesIO()
        orig.save(buf, 'JPEG', quality=quality)
        buf.seek(0)

        recomp = Image.open(buf).convert('RGB')

        ela = np.abs(
            np.array(orig, dtype=np.float32) -
            np.array(recomp, dtype=np.float32)
        ) * scale

        ela = np.clip(ela, 0, 255).astype(np.uint8)
        ela_gray = cv2.cvtColor(ela, cv2.COLOR_RGB2GRAY)
        ela_colored = cv2.applyColorMap(ela_gray, cv2.COLORMAP_JET)

        if output_path:
            cv2.imwrite(output_path, ela_colored)

        return ela_colored

    # =========================================================
    # NOISE HEATMAP
    # =========================================================
    def generate_noise_heatmap(
        self,
        image_path: str,
        block_size: int = 32,
        output_path: str = None
    ) -> np.ndarray:
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
                noise_score = np.std(lap)

                noise_map[y:y+block_size, x:x+block_size] = noise_score

        noise_norm = self._normalize_heatmap(noise_map)
        noise_colored = cv2.applyColorMap(noise_norm, cv2.COLORMAP_JET)

        result = self._blend_images(image, noise_colored, alpha=0.55)
        result_arr = np.array(result)
        result_bgr = cv2.cvtColor(result_arr, cv2.COLOR_RGB2BGR)

        if output_path:
            cv2.imwrite(output_path, result_bgr)

        return result_bgr

    # =========================================================
    # LOCAL GRADIENT ANOMALY HEATMAP
    # =========================================================
    def generate_lga_heatmap(
        self,
        image_path: str,
        block_size: int = 16,
        output_path: str = None
    ) -> np.ndarray:
        image = Image.open(image_path).convert('RGB')
        img_arr = np.array(image)
        gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)

        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(gx**2 + gy**2)

        h, w = grad_mag.shape
        lga_map = np.zeros((h, w), dtype=np.float32)

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block = grad_mag[y:y+block_size, x:x+block_size]
                if block.size == 0:
                    continue

                local_mean = np.mean(block)
                local_std = np.std(block)
                anomaly = abs(local_std - local_mean)

                lga_map[y:y+block_size, x:x+block_size] = anomaly

        lga_norm = self._normalize_heatmap(lga_map)
        lga_colored = cv2.applyColorMap(lga_norm, cv2.COLORMAP_JET)

        result = self._blend_images(image, lga_colored, alpha=0.55)
        result_arr = np.array(result)
        result_bgr = cv2.cvtColor(result_arr, cv2.COLOR_RGB2BGR)

        if output_path:
            cv2.imwrite(output_path, result_bgr)

        return result_bgr

    # =========================================================
    # JPEG GHOST HEATMAP
    # =========================================================
    def generate_ghost_heatmap(
        self,
        image_path: str,
        qualities: list = None,
        output_path: str = None
    ) -> Dict:
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

        stack = np.stack(diff_maps, axis=0)
        best_q_idx = np.argmin(stack, axis=0).astype(np.float32)

        ghost_variance = float(np.std(best_q_idx))

        idx_norm = self._normalize_heatmap(best_q_idx)
        ghost_colored = cv2.applyColorMap(idx_norm, cv2.COLORMAP_JET)

        if output_path:
            cv2.imwrite(output_path, ghost_colored)

        return {
            "ghost_map": ghost_colored,
            "ghost_variance": round(ghost_variance, 4),
            "suspicion_score": round(min(100.0, ghost_variance * 15.0), 2),
        }

    # =========================================================
    # DCT FREQUENCY HEATMAP
    # =========================================================
    def generate_dct_heatmap(
        self,
        image_path: str,
        output_path: str = None
    ) -> np.ndarray:
        from scipy import fftpack

        image = Image.open(image_path).convert('L')
        img_arr = np.array(image, dtype=np.float32)

        h, w = img_arr.shape
        block_size = 8

        dct_map = np.zeros((h // block_size, w // block_size), dtype=np.float32)

        for bi in range(h // block_size):
            for bj in range(w // block_size):
                i = bi * block_size
                j = bj * block_size

                block = img_arr[i:i+block_size, j:j+block_size]

                dct_block = fftpack.dct(
                    fftpack.dct(block, axis=0, norm='ortho'),
                    axis=1,
                    norm='ortho'
                )

                ac_mean = float(np.mean(np.abs(dct_block.flatten()[1:])))
                dct_map[bi, bj] = ac_mean

        dct_full = cv2.resize(dct_map, (w, h), interpolation=cv2.INTER_NEAREST)
        dct_norm = self._normalize_heatmap(dct_full)
        dct_colored = cv2.applyColorMap(dct_norm, cv2.COLORMAP_JET)

        if output_path:
            cv2.imwrite(output_path, dct_colored)

        return dct_colored
    
        # =========================================================
    # SAVE / DISPLAY UTILITIES
    # =========================================================
    def save_heatmap(self, heatmap: np.ndarray, output_path: str):
        try:
            if len(heatmap.shape) == 3:
                cv2.imwrite(output_path, cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))
            else:
                cv2.imwrite(output_path, heatmap)
        except Exception:
            pass

    def generate_report_visuals(self, image_path: str, output_prefix: str = "report") -> Dict[str, str]:
        generated = {}

        try:
            lsb = self.generate_lsb_heatmap(image_path)
            path = f"{output_prefix}_lsb.png"
            self.save_heatmap(lsb, path)
            generated["lsb"] = path
        except Exception:
            pass

        try:
            ela = self.generate_ela_heatmap(image_path)
            path = f"{output_prefix}_ela.png"
            self.save_heatmap(ela, path)
            generated["ela"] = path
        except Exception:
            pass

        try:
            noise = self.generate_noise_heatmap(image_path)
            path = f"{output_prefix}_noise.png"
            self.save_heatmap(noise, path)
            generated["noise"] = path
        except Exception:
            pass

        try:
            ghost = self.generate_ghost_heatmap(image_path)
            path = f"{output_prefix}_ghost.png"
            self.save_heatmap(ghost["ghost_map"], path)
            generated["ghost"] = path
        except Exception:
            pass

        try:
            dct = self.generate_dct_heatmap(image_path)
            path = f"{output_prefix}_dct.png"
            self.save_heatmap(dct, path)
            generated["dct"] = path
        except Exception:
            pass

        return generated

    def generate_visual_comparison_sheet(self, image_path: str, output_path: str = "comparison_sheet.png"):
        visuals = self.generate_report_visuals(image_path, "temp_cmp")

        fig = plt.figure(figsize=(14, 8))
        images = []

        try:
            original = np.array(Image.open(image_path).convert("RGB"))
            images.append(("Original", original))
        except Exception:
            pass

        for key in ["lsb", "ela", "noise", "ghost", "dct"]:
            if key in visuals:
                try:
                    images.append((key.upper(), cv2.cvtColor(cv2.imread(visuals[key]), cv2.COLOR_BGR2RGB)))
                except Exception:
                    continue

        total = len(images)
        cols = 3
        rows = int(np.ceil(total / cols))

        for idx, (title, img) in enumerate(images, start=1):
            ax = fig.add_subplot(rows, cols, idx)
            ax.imshow(img)
            ax.set_title(title)
            ax.axis("off")

        plt.tight_layout()
        plt.savefig(output_path)
        plt.close(fig)

    # =========================================================
    # FINAL HYBRID FORENSIC FUSION HEATMAP
    # =========================================================
    def generate_hybrid_heatmap(self, image_path: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master enterprise hybrid forensic heatmap.
        Uses detector suspicion scores to weight only meaningful maps.
        """

        weighted_maps = []
        active_maps = []

        methods = analysis_results.get("methods", {})

        def add_map(generator_func, score, name):
            try:
                if score is not None and score > 20:
                    raw = generator_func(image_path)

                    if isinstance(raw, dict):
                        raw = raw.get("ghost_map", None)
                        if raw is None:
                            return

                    if len(raw.shape) == 3:
                        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
                    else:
                        gray = raw

                    gray = gray.astype(np.float32) / 255.0
                    weighted_maps.append(gray * (score / 100.0))
                    active_maps.append(name)
            except Exception:
                pass

        add_map(self.generate_lsb_heatmap,
                methods.get("lsb", {}).get("lsb_suspicion_score"),
                "LSB")

        add_map(self.generate_ela_heatmap,
                methods.get("ela", {}).get("suspicion_score"),
                "ELA")

        add_map(self.generate_noise_heatmap,
                methods.get("noise", {}).get("suspicion_score"),
                "Noise")

        add_map(self.generate_ghost_heatmap,
                methods.get("jpeg_ghost", {}).get("suspicion_score"),
                "JPEG Ghost")

        add_map(self.generate_dct_heatmap,
                methods.get("dct_analysis", {}).get("suspicion_score"),
                "DCT")

        if not weighted_maps:
            blank = np.zeros((256, 256, 3), dtype=np.uint8)
            return {
                "hybrid_overlay": blank,
                "suspicious_pixel_ratio": 0.0,
                "active_maps": []
            }

        combined = np.mean(np.stack(weighted_maps, axis=0), axis=0)
        combined_uint8 = self._normalize_heatmap(combined * 255)
        colored = cv2.applyColorMap(combined_uint8, cv2.COLORMAP_JET)

        orig = Image.open(image_path).convert("RGB")
        blended = self._blend_images(orig, colored, alpha=0.55)
        blended_arr = np.array(blended)

        suspicious_ratio = float(np.sum(combined > 0.65)) / combined.size * 100.0

        return {
            "hybrid_overlay": blended_arr,
            "suspicious_pixel_ratio": round(suspicious_ratio, 2),
            "active_maps": active_maps,
            "method": "Enterprise Hybrid Multi-Detector Heatmap Fusion"
        }