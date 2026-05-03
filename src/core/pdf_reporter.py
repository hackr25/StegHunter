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
    
    def generate_report(self, analysis_results: dict, image_path: str, output_pdf_path: str) -> str:
        """
        Generate comprehensive PDF report from analysis results
        
        Args:
            analysis_results: Complete analysis results from SteganographyAnalyzer
            image_path: Path to the analyzed image
            output_pdf_path: Path where PDF should be saved
            
        Returns:
            Path to generated PDF
        """
        try:
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            
            # Title
            elements.append(Paragraph("🔍 StegHunter Analysis Report", self.title_style))
            elements.append(Paragraph("Professional Steganography Detection Analysis", self.styles['Normal']))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            elements.append(Paragraph(f"Generated on {timestamp}", self.styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Verdict Section
            verdict = analysis_results.get('verdict', 'UNKNOWN')
            confidence = analysis_results.get('confidence_score', 0)
            verdict_color = self._get_verdict_color_hex(verdict)
            
            verdict_data = [
                ['Analysis Verdict', f'{verdict} (Confidence: {confidence:.1f}%)']
            ]
            verdict_table = Table(verdict_data, colWidths=[2*inch, 4.5*inch])
            verdict_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), verdict_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(verdict_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Statistics
            overall_score = analysis_results.get('overall_score', 0)
            stats_data = [
                ['Overall Score', f'{overall_score:.1f}/100'],
                ['Confidence', f'{confidence:.1f}%'],
                ['File', Path(image_path).name]
            ]
            stats_table = Table(stats_data, colWidths=[2*inch, 4.5*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(Paragraph("Overview", self.heading_style))
            elements.append(stats_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Image
            try:
                img = Image.open(image_path)
                # Resize to fit
                img_width = 6*inch
                img_height = (img.height / img.width) * img_width
                if img_height > 4*inch:
                    img_height = 4*inch
                    img_width = (img.width / img.height) * img_height
                
                img_path_temp = str(Path(image_path))
                elements.append(Paragraph("Analyzed Image", self.heading_style))
                elements.append(RLImage(img_path_temp, width=img_width, height=img_height))
                elements.append(Spacer(1, 0.1*inch))
            except:
                elements.append(Paragraph("(Image could not be embedded)", self.normal_style))
            
            # Methods
            elements.append(PageBreak())
            elements.append(Paragraph("Detection Methods", self.heading_style))
            methods = analysis_results.get('methods_used', [])
            methods_data = [['Method', 'Score', 'Description']]
            for method in methods:
                methods_data.append([
                    method.get('name', 'Unknown'),
                    f"{method.get('score', 0):.1f}",
                    method.get('description', '')[:50]
                ])
            methods_table = Table(methods_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
            methods_table.setStyle(TableStyle([
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
            elements.append(methods_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Hiding Locations
            hiding_locs = analysis_results.get('hiding_locations', {})
            if hiding_locs:
                elements.append(Paragraph("Potential Hiding Locations", self.heading_style))
                suspicious_areas = hiding_locs.get('suspicious_areas', [])
                if suspicious_areas:
                    locs_data = [['Location', 'Suspicion', 'Reason']]
                    for area in suspicious_areas[:6]:
                        locs_data.append([
                            area.get('location', 'Unknown'),
                            f"{area.get('suspicion_score', 0):.1f}%",
                            area.get('reason', '')[:40]
                        ])
                    locs_table = Table(locs_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
                    locs_table.setStyle(TableStyle([
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
                    elements.append(locs_table)
                    elements.append(Spacer(1, 0.2*inch))
            
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
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def create_single_image_report(self, image_path: str, analysis_results: dict, heatmap_path: str, output_pdf_path: str) -> str:
        """Backward compatibility method"""
        return self.generate_report(analysis_results, image_path, output_pdf_path)
    
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
