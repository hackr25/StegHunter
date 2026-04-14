from typing import List, Dict, Any

class ReasoningEngine:
    """
    Translates mathematical suspicion scores into human-readable 
    forensic explanations.
    """
    def __init__(self):
        # Define thresholds for what constitutes "significant" findings
        self.thresholds = {
            "lsb": 40.0,
            "chi_square": 30.0,
            "pixel_differencing": 30.0,
            "ela": 40.0,
            "jpeg_ghost": 30.0,
            "noise": 30.0,
            "color_space": 30.0,
            "metadata": 20.0
        }

    def generate_explanation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the results dict and generates a detailed reasoning report.
        """
        methods = results.get("methods", {})
        findings = []
        critical_flags = []

        # 1. LSB Analysis Reasoning
        if "lsb" in methods:
            lsb = methods["lsb"]
            if lsb.get("lsb_uniformity_reject"):
                findings.append("❌ LSB Uniformity Test failed: The distribution of least-significant bits is too uniform, which is a strong indicator of encrypted data insertion.")
            if lsb.get("entropy", 0) > 0.9:
                findings.append(f"⚠️ High LSB Entropy ({lsb.get('entropy', 0):.2f}): The randomness of the lowest bit plane is abnormally high.")

        # 2. ELA Reasoning
        if "ela" in methods:
            ela_score = methods["ela"].get("suspicion_score", 0)
            if ela_score > self.thresholds["ela"]:
                findings.append(f"❌ Error Level Analysis (ELA) flagged anomalies: Localized areas of the image show inconsistent compression levels, suggesting the image was modified after the original save.")

        # 3. JPEG Ghost Reasoning
        if "jpeg_ghost" in methods:
            ghost_score = methods["jpeg_ghost"].get("suspicion_score", 0)
            if ghost_score > self.thresholds["jpeg_ghost"]:
                findings.append("❌ JPEG Ghost detected: The image shows evidence of double-compression with different quality factors, a common artifact of steganographic embedding.")

        # 4. Color Space Reasoning
        if "color_space" in methods:
            cs_score = methods["color_space"].get("suspicion_score", 0)
            if cs_score > self.thresholds["color_space"]:
                findings.append("⚠️ Chrominance Anomaly: Unusual entropy detected in the Cb/Cr channels. Data is often hidden here as the human eye is less sensitive to color shifts.")

        # 5. Noise Reasoning
        if "noise" in methods:
            noise_score = methods["noise"].get("suspicion_score", 0)
            if noise_score > self.thresholds["noise"]:
                findings.append("⚠️ High-Frequency Noise: The Laplacian variance is higher than expected for a natural image, suggesting artificial noise injection.")

        # 6. Metadata Reasoning
        if "metadata" in methods:
            meta_score = methods["metadata"].get("suspicion_score", 0)
            if meta_score > self.thresholds["metadata"]:
                findings.append("ℹ️ Metadata Irregularity: The image contains suspicious or stripped EXIF data, often seen in tools that cleanse footprints.")

        # --- Final Verdict Logic ---
        final_score = results.get("final_suspicion_score", 0)
        verdict = "Clean"
        if final_score > 70:
            verdict = "Highly Suspicious"
            critical_flags.append("Critical: Multiple high-confidence indicators present.")
        elif final_score > 40:
            verdict = "Suspicious"
            critical_flags.append("Warning: Minor anomalies detected; further manual inspection required.")
        elif final_score > 15:
            verdict = "Low Suspicion"
        else:
            findings.append("✅ No significant steganographic markers detected.")

        return {
            "verdict": verdict,
            "final_score": final_score,
            "detailed_findings": findings,
            "critical_alerts": critical_flags,
            "summary": f"Analysis complete. Verdict: {verdict} ({final_score}%). Found {len(findings)} relevant markers."
        }
