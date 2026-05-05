from typing import Dict, Any, List


class ReasoningEngine:
    """
    Advanced Hybrid Forensic Reasoning Engine.
    Converts multi-detector numerical evidence into human-readable
    forensic conclusions with confidence-aware interpretation.
    """

    def __init__(self):
        self.thresholds = {
            "lsb": 45.0,
            "chi_square": 35.0,
            "pixel_differencing": 35.0,
            "ela": 40.0,
            "jpeg_ghost": 35.0,
            "noise": 35.0,
            "color_space": 35.0,
            "metadata": 20.0,
            "clone_detection": 30.0,
            "rs_analysis": 35.0,
            "spa_analysis": 35.0,
            "dct_analysis": 35.0,
            "deep_learning": 50.0,
            "png_chunk_analysis": 20.0,
        }

    @staticmethod
    def _safe_get_float(value):
        """Safely convert value to float, handling None and NaN."""
        if value is None:
            return 0.0
        try:
            f = float(value)
            return f if not (f != f) else 0.0  # Check for NaN
        except (TypeError, ValueError):
            return 0.0

    def generate_explanation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        methods = results.get("methods", {})
        findings: List[str] = []
        critical_flags: List[str] = []

        # ---------------------------------------------------------
        # LSB FORENSICS
        # ---------------------------------------------------------
        if "lsb" in methods:
            lsb_score = self._safe_get_float(methods["lsb"].get("lsb_suspicion_score", 0))
            if lsb_score > self.thresholds["lsb"]:
                findings.append(
                    f"❌ LSB forensic anomaly detected ({lsb_score:.2f}%): "
                    f"least-significant bit randomness, spatial correlation disruption, and bit-plane balance suggest hidden payload insertion."
                )

        if "rs_analysis" in methods:
            rs_score = self._safe_get_float(methods["rs_analysis"].get("suspicion_score", 0))
            if rs_score > self.thresholds["rs_analysis"]:
                findings.append(
                    f"⚠️ RS statistical imbalance anomaly ({rs_score:.2f}%): "
                    f"Regular/Singular group equilibrium suggests probable least-significant-bit embedding disturbance."
                )

        if "spa_analysis" in methods:
            spa_score = self._safe_get_float(methods["spa_analysis"].get("suspicion_score", 0))
            if spa_score > self.thresholds["spa_analysis"]:
                findings.append(
                    f"⚠️ Sample Pair transition anomaly ({spa_score:.2f}%): "
                    f"neighboring grayscale parity relationships indicate probable LSB replacement behavior."
                )

        # ---------------------------------------------------------
        # CHI SQUARE / STATISTICAL
        # ---------------------------------------------------------
        if "chi_square" in methods:
            score = self._safe_get_float(methods["chi_square"].get("suspicion_score", 0))
            if score > self.thresholds["chi_square"]:
                findings.append(
                    f"⚠️ Histogram pair-frequency irregularity observed ({score:.2f}%): "
                    f"grayscale statistical consistency deviates from natural image behavior."
                )

        if "pixel_differencing" in methods:
            score = self._safe_get_float(methods["pixel_differencing"].get("suspicion_score", 0))
            if score > self.thresholds["pixel_differencing"]:
                findings.append(
                    f"⚠️ Residual pixel differencing anomaly ({score:.2f}%): "
                    f"adjacent pixel transition smoothness is disrupted beyond normal expectations."
                )

        # ---------------------------------------------------------
        # ELA
        # ---------------------------------------------------------
        if "ela" in methods:
            score = self._safe_get_float(methods["ela"].get("suspicion_score", 0))
            if score > self.thresholds["ela"]:
                findings.append(
                    f"❌ Error Level Analysis inconsistency ({score:.2f}%): "
                    f"localized recompression signatures indicate possible manipulated or embedded regions."
                )

        # ---------------------------------------------------------
        # JPEG GHOST
        # ---------------------------------------------------------
        if "jpeg_ghost" in methods:
            score = self._safe_get_float(methods["jpeg_ghost"].get("suspicion_score", 0))
            if score > self.thresholds["jpeg_ghost"]:
                findings.append(
                    f"⚠️ JPEG recompression ghost evidence ({score:.2f}%): "
                    f"double-compression irregularities detected across spatial blocks."
                )

        # ---------------------------------------------------------
        # NOISE
        # ---------------------------------------------------------
        if "noise" in methods:
            score = self._safe_get_float(methods["noise"].get("suspicion_score", 0))
            if score > self.thresholds["noise"]:
                findings.append(
                    f"⚠️ Residual noise inconsistency ({score:.2f}%): "
                    f"high-frequency residual entropy and local noise patterns appear artificially disturbed."
                )

        # ---------------------------------------------------------
        # COLOR SPACE
        # ---------------------------------------------------------
        if "color_space" in methods:
            score = self._safe_get_float(methods["color_space"].get("suspicion_score", 0))
            if score > self.thresholds["color_space"]:
                findings.append(
                    f"⚠️ Chromatic embedding anomaly ({score:.2f}%): "
                    f"YCbCr entropy, luminance correlation, and saturation consistency indicate unnatural chrominance modification."
                )

        # ---------------------------------------------------------
        # DCT ANALYSIS
        # ---------------------------------------------------------
        if "dct_analysis" in methods:
            dct_score = self._safe_get_float(methods["dct_analysis"].get("suspicion_score", 0))
            if dct_score > self.thresholds["dct_analysis"]:
                findings.append(
                    f"⚠️ JPEG frequency-domain coefficient anomaly ({dct_score:.2f}%): "
                    f"AC coefficient population statistics indicate probable transform-domain embedding disturbance."
                )

        # ---------------------------------------------------------
        # METADATA
        # ---------------------------------------------------------
        if "metadata" in methods:
            score = self._safe_get_float(methods["metadata"].get("suspicion_score", 0))
            if score > self.thresholds["metadata"]:
                findings.append(
                    f"ℹ️ Metadata irregularity ({score:.2f}%): "
                    f"EXIF/metadata structure suggests prior editing, stripping, or processing."
                )

        # ---------------------------------------------------------
        # PNG STRUCTURAL FORENSICS
        # ---------------------------------------------------------
        if "png_chunk_analysis" in methods:
            png_score = self._safe_get_float(methods["png_chunk_analysis"].get("suspicion_score", 0))
            if png_score > self.thresholds["png_chunk_analysis"]:
                findings.append(
                    f"⚠️ PNG structural chunk anomaly ({png_score:.2f}%): "
                    f"ancillary metadata chunk abuse or appended binary payload suggests non-visual concealment."
                )

        # ---------------------------------------------------------
        # CLONE DETECTION
        # ---------------------------------------------------------
        if "clone_detection" in methods:
            score = self._safe_get_float(methods["clone_detection"].get("suspicion_score", 0))
            if score > self.thresholds["clone_detection"]:
                findings.append(
                    f"❌ Clone-pattern similarity detected ({score:.2f}%): "
                    f"duplicated visual descriptors suggest copy-move style localized manipulation."
                )

        # ---------------------------------------------------------
        # DEEP CNN LEARNING
        # ---------------------------------------------------------
        if "deep_learning" in methods:
            dl_score = self._safe_get_float(methods["deep_learning"].get("deep_learning_score", 0))
            dl_conf = self._safe_get_float(methods["deep_learning"].get("deep_learning_confidence", 0))

            if dl_score > self.thresholds["deep_learning"]:
                findings.append(
                    f"🚨 Deep CNN steganalyzer flagged embedded artifact probability ({dl_score:.2f}%) "
                    f"with confidence {dl_conf:.2f}%. Learned residual signatures are consistent with hidden-data embedding."
                )

        # ---------------------------------------------------------
        # DETECTOR FAMILY CONVERGENCE ANALYSIS
        # ---------------------------------------------------------
        lsb_family = 0
        jpeg_family = 0
        manipulation_family = 0

        if self._safe_get_float(methods.get("lsb", {}).get("lsb_suspicion_score", 0)) > self.thresholds["lsb"]:
            lsb_family += 1
        if self._safe_get_float(methods.get("rs_analysis", {}).get("suspicion_score", 0)) > self.thresholds["rs_analysis"]:
            lsb_family += 1
        if self._safe_get_float(methods.get("spa_analysis", {}).get("suspicion_score", 0)) > self.thresholds["spa_analysis"]:
            lsb_family += 1

        if self._safe_get_float(methods.get("jpeg_ghost", {}).get("suspicion_score", 0)) > self.thresholds["jpeg_ghost"]:
            jpeg_family += 1
        if self._safe_get_float(methods.get("dct_analysis", {}).get("suspicion_score", 0)) > self.thresholds["dct_analysis"]:
            jpeg_family += 1

        if self._safe_get_float(methods.get("ela", {}).get("suspicion_score", 0)) > self.thresholds["ela"]:
            manipulation_family += 1
        if self._safe_get_float(methods.get("noise", {}).get("suspicion_score", 0)) > self.thresholds["noise"]:
            manipulation_family += 1
        if self._safe_get_float(methods.get("clone_detection", {}).get("suspicion_score", 0)) > self.thresholds["clone_detection"]:
            manipulation_family += 1

        if lsb_family >= 2:
            critical_flags.append(
                "High-confidence convergence: multiple independent LSB statistical detectors simultaneously indicate hidden bit-plane disturbance."
            )

        if jpeg_family >= 2:
            critical_flags.append(
                "High-confidence convergence: JPEG recompression and DCT frequency detectors jointly indicate transform-domain embedding artifacts."
            )

        if manipulation_family >= 2:
            critical_flags.append(
                "High-confidence convergence: residual, recompression, and structural manipulation detectors reveal localized forensic inconsistencies."
            )

        if (
            self._safe_get_float(methods.get("deep_learning", {}).get("deep_learning_score", 0)) > self.thresholds["deep_learning"]
            and len(findings) >= 3
        ):
            critical_flags.append(
                "Deep-learning agreement: learned residual steganalyzer confirms multiple handcrafted forensic detector anomalies."
            )

        # ---------------------------------------------------------
        # FINAL VERDICT
        # ---------------------------------------------------------
        final_score = results.get("final_suspicion_score", 0)

        if final_score >= 80:
            verdict = "Highly Suspicious"
            critical_flags.append("Critical: Multiple independent forensic detectors strongly converge toward hidden-content likelihood.")
        elif final_score >= 60:
            verdict = "Suspicious"
            critical_flags.append("Warning: Several medium-to-high confidence anomalies detected across detector families.")
        elif final_score >= 35:
            verdict = "Moderate Suspicion"
            critical_flags.append("Notice: Some weak forensic inconsistencies present; manual verification recommended.")
        elif final_score >= 15:
            verdict = "Low Suspicion"
        else:
            verdict = "Clean"

        if not findings:
            findings.append("✅ No major forensic anomalies detected across hybrid detector ensemble.")

        return {
            "verdict": verdict,
            "final_score": round(final_score, 2),
            "detailed_findings": findings,
            "critical_alerts": critical_flags,
            "summary": f"Hybrid forensic analysis complete. Verdict: {verdict} ({final_score:.2f}%). Detected {len(findings)} notable forensic indicators."
        }