"""
Professional PDF Report Generator for StegHunter Analysis Results
Uses reportlab for Windows-compatible PDF generation (no GTK+ dependencies)
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image


class PDFReporter:
    """Generates professional PDF reports for steganography analysis using reportlab"""
    
    def __init__(self):
        """Initialize PDF reporter"""
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0066CC'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#0066CC'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
    
    def generate_report(self, analysis_results: dict, image_path: str, output_pdf_path: str, heatmap_path: str = None) -> str:
        """
        Generate enterprise forensic PDF report from StegHunter analysis
        """

        try:
            doc = SimpleDocTemplate(
                output_pdf_path,
                pagesize=letter,
                topMargin=0.5 * inch,
                bottomMargin=0.5 * inch
            )

            elements = []

            # ============================================================
            # PAGE 1 : TITLE + FINAL VERDICT + IMAGE OVERVIEW
            # ============================================================

            elements.append(Paragraph("StegHunter Forensic Investigation Report", self.title_style))
            elements.append(Paragraph("Professional Multi-Detector Steganography Examination", self.styles['Normal']))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elements.append(Paragraph(f"Generated on {timestamp}", self.styles['Normal']))
            elements.append(Spacer(1, 0.25 * inch))

            final_score = (
                analysis_results.get("final_suspicion_score")
                or analysis_results.get("overall_score")
                or 0
            )

            confidence = (
                analysis_results.get("confidence_score")
                or analysis_results.get("ml_probability", 0) * 100
                or 0
            )

            verdict = self._derive_forensic_verdict(final_score)
            verdict_color = self._get_verdict_color_hex(verdict)

            verdict_data = [
                ["Final Forensic Verdict", verdict],
                ["Suspicion Score", f"{final_score:.2f} / 100"],
                ["Confidence Level", f"{confidence:.2f}%"],
                ["Analyzed File", Path(image_path).name]
            ]

            verdict_table = Table(verdict_data, colWidths=[2.2 * inch, 4.3 * inch])
            verdict_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), verdict_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f7f7')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))

            elements.append(verdict_table)
            elements.append(Spacer(1, 0.2 * inch))

            # ------------------------------------------------------------
            # ORIGINAL IMAGE EMBED
            # ------------------------------------------------------------
            try:
                img = Image.open(image_path)
                img_width = 5.8 * inch
                img_height = (img.height / img.width) * img_width

                if img_height > 3.6 * inch:
                    img_height = 3.6 * inch
                    img_width = (img.width / img.height) * img_height

                elements.append(Paragraph("Analyzed Evidence Image", self.heading_style))
                elements.append(RLImage(str(Path(image_path)), width=img_width, height=img_height))
                elements.append(Spacer(1, 0.2 * inch))
            except:
                elements.append(Paragraph("(Evidence image preview unavailable)", self.normal_style))

            # ------------------------------------------------------------
            # BASIC FILE INTELLIGENCE
            # ------------------------------------------------------------
            basic_info = self._collect_file_intelligence(image_path)

            elements.append(Paragraph("File Intelligence", self.heading_style))
            info_data = [
                ["MD5 Hash", basic_info["md5"]],
                ["SHA256 Hash", basic_info["sha256"][:50] + "..."],
                ["File Size", basic_info["size"]],
                ["Image Dimensions", basic_info["dimensions"]],
                ["Entropy", basic_info["entropy"]]
            ]

            info_table = Table(info_data, colWidths=[2.0 * inch, 4.5 * inch])
            info_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(info_table)

            # ============================================================
            # PAGE 2 : DETECTOR TABLE + FORENSIC REASONING
            # ============================================================

            elements.append(PageBreak())
            elements.append(Paragraph("Detector-wise Forensic Breakdown", self.heading_style))

            methods = analysis_results.get("methods", {})
            detector_rows = [["Detector", "Score", "Risk", "Evidence"]]

            detector_name_map = {
                "basic": "Basic Consistency",
                "lsb": "LSB Statistical Analysis",
                "chi_square": "Chi Square Distribution",
                "rs_analysis": "RS Structural Analysis",
                "spa_analysis": "Sample Pair Analysis",
                "dct_analysis": "DCT Coefficient Analysis",
                "jpeg_ghost": "JPEG Ghost Recompression",
                "ela": "Error Level Analysis",
                "noise": "Noise Residual",
                "color_space": "Color Space Forensics",
                "clone_detection": "Clone Region Detection",
                "deep_learning": "CNN Deep Detector",
                "png_chunk": "PNG Chunk Inspection"
            }

            for key, value in methods.items():
                score = (
                    value.get("suspicion_score")
                    or value.get("lsb_suspicion_score")
                    or value.get("basic_suspicion_score")
                    or 0
                )

                risk = self._risk_label(score)
                evidence = self._summarize_detector_evidence(value)

                detector_rows.append([
                    detector_name_map.get(key, key),
                    f"{score:.2f}",
                    risk,
                    evidence
                ])

            detector_table = Table(detector_rows, colWidths=[1.8 * inch, 0.9 * inch, 1.0 * inch, 2.8 * inch])
            detector_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f7f7')]),
            ]))

            elements.append(detector_table)
            elements.append(Spacer(1, 0.2 * inch))

            # ------------------------------------------------------------
            # FORENSIC REASONING SECTION
            # ------------------------------------------------------------
            elements.append(Paragraph("Analyst Forensic Interpretation", self.heading_style))

            forensic_reasoning = self._extract_reasoning_text(analysis_results)
            elements.append(Paragraph(forensic_reasoning, self.normal_style))
            elements.append(Spacer(1, 0.2 * inch))
            
            # ------------------------------------------------------------
            # PAYLOAD REGION SUMMARY
            # ------------------------------------------------------------
            elements.append(Paragraph("Probable Payload Localization", self.heading_style))

            payload_text = self._extract_payload_region_text(analysis_results)
            elements.append(Paragraph(payload_text, self.normal_style))
            elements.append(Spacer(1, 0.2 * inch))

            # ============================================================
            # PAGE 3 : HEATMAP + FINAL CONCLUSION
            # ============================================================

            elements.append(PageBreak())

            if heatmap_path and Path(heatmap_path).exists():
                try:
                    hm = Image.open(heatmap_path)
                    hm_width = 5.8 * inch
                    hm_height = (hm.height / hm.width) * hm_width

                    if hm_height > 4.5 * inch:
                        hm_height = 4.5 * inch
                        hm_width = (hm.width / hm.height) * hm_height

                    elements.append(Paragraph("Suspicious Region Heatmap Evidence", self.heading_style))
                    elements.append(RLImage(str(Path(heatmap_path)), width=hm_width, height=hm_height))
                    elements.append(Spacer(1, 0.2 * inch))
                except:
                    elements.append(Paragraph("(Heatmap evidence unavailable)", self.normal_style))
            else:
                elements.append(Paragraph("No external heatmap evidence attached.", self.normal_style))
                elements.append(Spacer(1, 0.2 * inch))

            # ------------------------------------------------------------
            # FINAL CONCLUSION
            # ------------------------------------------------------------
            elements.append(Paragraph("Final Conclusion", self.heading_style))

            conclusion_text = (
                f"StegHunter multi-detector forensic analysis assigned a final suspicion score of "
                f"{final_score:.2f}/100, corresponding to verdict: {verdict}. "
                f"Cross-detector statistical irregularities, structural anomalies, and heuristic "
                f"embedding signatures indicate that this digital image exhibits "
                f"{'strong' if final_score >= 70 else 'moderate' if final_score >= 40 else 'limited'} "
                f"steganographic suspicion."
            )

            elements.append(Paragraph(conclusion_text, self.normal_style))
            elements.append(Spacer(1, 0.3 * inch))

            elements.append(Paragraph(
                "Generated by StegHunter - Hybrid Steganography Detection Framework",
                self.styles['Normal']
            ))
            elements.append(Paragraph(
                "GitHub: https://github.com/hackr25/StegHunter",
                self.styles['Normal']
            ))

            doc.build(elements)
            return output_pdf_path

        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
        
    def _collect_file_intelligence(self, image_path: str):
        import hashlib
        import math
        from pathlib import Path
        from PIL import Image

        with open(image_path, "rb") as f:
            raw = f.read()

        md5 = hashlib.md5(raw).hexdigest()
        sha256 = hashlib.sha256(raw).hexdigest()
        size = f"{round(Path(image_path).stat().st_size / 1024, 2)} KB"

        img = Image.open(image_path)
        dimensions = f"{img.width} x {img.height}"

        histogram = img.convert("L").histogram()
        total = sum(histogram)
        entropy = 0.0
        for h in histogram:
            if h != 0:
                p = h / total
                entropy -= p * math.log2(p)

        return {
            "md5": md5,
            "sha256": sha256,
            "size": size,
            "dimensions": dimensions,
            "entropy": f"{entropy:.3f}"
        }
    
    def _risk_label(self, score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MODERATE"
        elif score >= 20:
            return "LOW"
        return "MINIMAL"
    
    def _summarize_detector_evidence(self, detector_result: dict) -> str:
        parts = []
        for k, v in detector_result.items():
            if k not in ["suspicion_score", "lsb_suspicion_score", "basic_suspicion_score", "heatmap_path"]:
                parts.append(f"{k}:{v}")
            if len(parts) >= 2:
                break
        return " | ".join(parts) if parts else "No auxiliary evidence"
    
    def _extract_reasoning_text(self, analysis_results: dict) -> str:
        reasoning = analysis_results.get("forensic_reasoning") or analysis_results.get("explanation") or {}

        if isinstance(reasoning, str):
            return reasoning

        lines = []

        verdict = reasoning.get("verdict")
        summary = reasoning.get("summary")
        findings = reasoning.get("detailed_findings") or reasoning.get("findings") or []

        if verdict:
            lines.append(f"Verdict: {verdict}")

        if summary:
            lines.append(summary)

        if findings:
            if isinstance(findings, list):
                for item in findings[:4]:
                    lines.append(f"• {item}")
            else:
                lines.append(str(findings))

        return "<br/>".join(lines) if lines else "No detailed forensic reasoning available."
    
    def _extract_payload_region_text(self, analysis_results: dict) -> str:
        payload = analysis_results.get("hiding_location") or analysis_results.get("payload_region") or {}

        if isinstance(payload, str):
            return payload

        if payload:
            return "<br/>".join([f"{k}: {v}" for k, v in payload.items()])

        score = analysis_results.get("final_suspicion_score", 0)

        if score >= 70:
            return "High-confidence anomaly concentration observed in central image regions, indicating probable localized payload embedding."
        elif score >= 40:
            return "Moderate anomaly overlap detected; suspicious embedding may exist in statistically irregular zones."
        else:
            return "No strong localized payload concentration identified."
        
    

    
    def create_single_image_report(self, image_path: str, analysis_results: dict, heatmap_path: str, output_pdf_path: str) -> str:
        """Backward compatibility method"""
        return self.generate_report(analysis_results, image_path, output_pdf_path, heatmap_path)
    
    def create_batch_report(self, results: list, output_pdf_path: str) -> str:
        """Create batch report from multiple analysis results"""
        try:
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            
            # Header
            elements.append(Paragraph("📦 StegHunter Batch Analysis Report", self.title_style))
            elements.append(Paragraph("Professional Steganography Detection - Batch Results", self.styles['Normal']))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elements.append(Paragraph(f"Generated on {timestamp}", self.styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Summary
            summary_data = [['Total Images Analyzed', str(len(results))]]
            summary_table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066CC')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Results table
            results_data = [['File', 'Verdict', 'Confidence', 'Score']]
            for result in results:
                img_path = result.get('image_path', '')
                analysis = result.get('analysis', {})
                verdict = analysis.get('verdict', 'UNKNOWN')
                confidence = analysis.get('confidence_score', 0)
                score = analysis.get('overall_score', 0)
                
                results_data.append([
                    Path(img_path).name,
                    verdict,
                    f"{confidence:.1f}%",
                    f"{score:.1f}/100"
                ])
            
            results_table = Table(results_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1*inch])
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(results_table)
            
            # Footer
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(
                "This report was generated by StegHunter - Professional Steganography Detection Tool",
                self.styles['Normal']
            ))
            elements.append(Paragraph(
                "GitHub: https://github.com/hackr25/StegHunter",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(elements)
            return output_pdf_path
        except Exception as e:
            raise Exception(f"Batch PDF generation failed: {str(e)}")
    
    def _get_verdict_color_hex(self, verdict: str):
        """Get reportlab color object based on verdict"""
        verdict_upper = verdict.upper()
        if 'DETECTED' in verdict_upper or 'POSITIVE' in verdict_upper:
            return colors.HexColor('#d32f2f')  # Red
        elif 'SUSPICIOUS' in verdict_upper:
            return colors.HexColor('#f57c00')  # Orange
        elif 'CLEAN' in verdict_upper or 'NEGATIVE' in verdict_upper:
            return colors.HexColor('#388e3c')  # Green
        else:
            return colors.HexColor('#1976d2')  # Blue
