"""
PDF Report Generation for StegHunter with Charts
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import tempfile
import atexit

class PDFReporter:
    """Generate professional PDF reports for steganography analysis with charts"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_style = ParagraphStyle(
            'Custom',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            spaceAfter=12,
        )
        self.temp_files = []  # Track temporary files for cleanup
        # Register cleanup function
        atexit.register(self.cleanup_temp_files)
    
    def cleanup_temp_files(self):
        """Clean up any remaining temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
    
    def create_single_image_report(self, image_path: str, analysis_results: Dict, 
                                  heatmap_path: str = None, output_path: str = None) -> str:
        """
        Create a detailed PDF report for a single image analysis with charts
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"report_{Path(image_path).stem}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("StegHunter Analysis Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Basic Image Information
        story.append(self._create_image_info_section(image_path, analysis_results))
        story.append(Spacer(1, 0.2 * inch))
        
        # Analysis Results with Chart
        try:
            story.extend(self._create_analysis_results_with_chart(analysis_results))
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            print(f"Chart creation failed: {e}")
            story.append(Paragraph("<b>Analysis Results:</b>", self.custom_style))
            story.append(self._create_analysis_results_section(analysis_results))
            story.append(Spacer(1, 0.2 * inch))
        
        # Method Details
        story.append(self._create_method_details_section(analysis_results))
        story.append(Spacer(1, 0.2 * inch))
        
        # Heatmap (if available)
        if heatmap_path and os.path.exists(heatmap_path):
            story.append(self._create_heatmap_section(heatmap_path))
            story.append(Spacer(1, 0.2 * inch))
        
        # Risk Assessment
        story.append(self._create_risk_assessment_section(analysis_results))
        story.append(Spacer(1, 0.2 * inch))
        
        # Footer
        story.append(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        return output_path
    
    def create_batch_report(self, batch_results: List[Dict], output_path: str = None) -> str:
        """
        Create a summary PDF report for batch analysis with charts
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"batch_report_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("StegHunter Batch Analysis Report", title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Summary Statistics
        story.append(self._create_batch_summary_section(batch_results))
        story.append(Spacer(1, 0.2 * inch))
        
        # Charts and Visualizations
        try:
            story.extend(self._create_batch_charts_section(batch_results))
            story.append(Spacer(1, 0.2 * inch))
        except Exception as e:
            print(f"Batch chart creation failed: {e}")
            story.append(Paragraph("<b>Analysis Summary:</b>", self.custom_style))
            story.append(self._create_batch_summary_section(batch_results))
            story.append(Spacer(1, 0.2 * inch))
        
        # Detailed Results Table
        story.append(self._create_batch_results_table(batch_results))
        story.append(Spacer(1, 0.2 * inch))
        
        # Footer
        story.append(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        # Clean up temporary files
        self.cleanup_temp_files()
        
        return output_path
    
    def _create_analysis_results_with_chart(self, results: Dict) -> list:
        """Create analysis results section with embedded chart"""
        elements = []
        
        # Results table
        elements.append(self._create_analysis_results_section(results))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Create and embed chart
        try:
            chart_path = self._create_single_image_chart(results)
            if chart_path and os.path.exists(chart_path):
                elements.append(Paragraph("<b>Analysis Visualization:</b>", self.custom_style))
                # Resize image to fit page
                img = Image(chart_path, width=5*inch, height=3*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2 * inch))
                self.temp_files.append(chart_path)  # Track for cleanup
        except Exception as e:
            print(f"Chart creation failed: {e}")
            # Fallback to just the table
            pass
        
        return elements
    
    def _create_single_image_chart(self, results: Dict) -> str:
        """Create a chart for single image analysis"""
        try:
            # Create a temporary file for the chart
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            plt.switch_backend('Agg')  # Use non-interactive backend
            
            if 'methods' in results:
                # Heuristic analysis - create bar chart of method scores
                methods_data = {}
                for method_name, method_results in results['methods'].items():
                    score = method_results.get('lsb_suspicion_score', 
                                            method_results.get('basic_suspicion_score', 0))
                    methods_data[method_name] = score
                
                # Create bar chart
                plt.figure(figsize=(8, 6))
                method_names = list(methods_data.keys())
                scores = list(methods_data.values())
                
                bars = plt.bar(method_names, scores, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
                plt.title('Analysis Method Scores')
                plt.ylabel('Suspicion Score')
                plt.ylim(0, 100)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{height:.1f}', ha='center', va='bottom')
                
                plt.tight_layout()
                plt.savefig(temp_path, dpi=100, bbox_inches='tight')
                plt.close()
                
            else:
                # ML analysis - create probability chart
                probability = results.get('ml_probability', 0) * 100
                confidence = results.get('ml_confidence', 0) * 100
                
                plt.figure(figsize=(8, 6))
                categories = ['Stego Probability', 'Model Confidence']
                values = [probability, confidence]
                colors = ['#ff9999', '#66b3ff']
                
                bars = plt.bar(categories, values, color=colors)
                plt.title('ML Analysis Results')
                plt.ylabel('Percentage (%)')
                plt.ylim(0, 100)
                
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 1,
                            f'{height:.1f}%', ha='center', va='bottom')
                
                plt.tight_layout()
                plt.savefig(temp_path, dpi=100, bbox_inches='tight')
                plt.close()
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
    
    def _create_batch_charts_section(self, results: List[Dict]) -> list:
        """Create charts section for batch report"""
        elements = []
        
        try:
            # Create summary chart
            chart_path = self._create_batch_summary_chart(results)
            if chart_path and os.path.exists(chart_path):
                elements.append(Paragraph("<b>Batch Analysis Summary:</b>", self.custom_style))
                img = Image(chart_path, width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.2 * inch))
                self.temp_files.append(chart_path)
            
            # Create distribution chart
            dist_path = self._create_score_distribution_chart(results)
            if dist_path and os.path.exists(dist_path):
                elements.append(Paragraph("<b>Score Distribution:</b>", self.custom_style))
                img = Image(dist_path, width=6*inch, height=4*inch)
                elements.append(img)
                self.temp_files.append(dist_path)
                
        except Exception as e:
            elements.append(Paragraph(f"<i>Charts unavailable: {str(e)}</i>", self.custom_style))
        
        return elements
    
    def _create_batch_summary_chart(self, results: List[Dict]) -> str:
        """Create a summary chart for batch results"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            plt.switch_backend('Agg')  # Use non-interactive backend
            
            # Count results by category
            categories = {'High Suspicion': 0, 'Low Suspicion': 0}
            for result in results:
                if 'ml_prediction' in result:
                    if result['ml_prediction'] == 1:
                        categories['High Suspicion'] += 1
                    else:
                        categories['Low Suspicion'] += 1
                else:
                    if result.get('final_suspicion_score', 0) >= 50:
                        categories['High Suspicion'] += 1
                    else:
                        categories['Low Suspicion'] += 1
            
            # Create pie chart
            plt.figure(figsize=(8, 6))
            labels = list(categories.keys())
            sizes = list(categories.values())
            colors = ['#ff9999', '#66b3ff']
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title('Suspicion Level Distribution')
            plt.axis('equal')
            
            plt.tight_layout()
            plt.savefig(temp_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating batch chart: {e}")
            return None
    
    def _create_score_distribution_chart(self, results: List[Dict]) -> str:
        """Create score distribution chart"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            plt.switch_backend('Agg')
            
            # Extract scores
            scores = []
            for result in results:
                if 'ml_prediction' in result:
                    scores.append(result.get('ml_probability', 0) * 100)
                else:
                    scores.append(result.get('final_suspicion_score', 0))
            
            # Create histogram
            plt.figure(figsize=(8, 6))
            plt.hist(scores, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Score Distribution')
            plt.xlabel('Suspicion Score')
            plt.ylabel('Number of Images')
            plt.grid(axis='y', alpha=0.75)
            
            plt.tight_layout()
            plt.savefig(temp_path, dpi=100, bbox_inches='tight')
            plt.close()
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating distribution chart: {e}")
            return None
    
    def _create_image_info_section(self, image_path: str, results: Dict) -> Table:
        """Create image information section"""
        image_info = [
            ["Filename:", Path(image_path).name],
            ["File Size:", f"{Path(image_path).stat().st_size:,} bytes"],
            ["Dimensions:", f"{results.get('dimensions', ['N/A'])[0]} x {results.get('dimensions', ['N/A', 'N/A'])[1]}"],
            ["Format:", results.get('format', 'N/A')],
            ["Color Mode:", results.get('mode', 'N/A')],
            ["Analysis Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        table = Table(image_info, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_analysis_results_section(self, results: Dict) -> Table:
        """Create analysis results section"""
        if 'ml_prediction' in results:
            # ML results
            prediction = "Steganography Detected" if results['ml_prediction'] == 1 else "Clean Image"
            confidence = f"{results.get('ml_confidence', 0) * 100:.1f}%"
            score = f"{results.get('ml_probability', 0) * 100:.1f}%"
        else:
            # Heuristic results
            score = results.get('final_suspicion_score', 0)
            confidence = "N/A"
            prediction = "High Suspicion" if score >= 50 else "Low Suspicion"
        
        analysis_data = [
            ["Final Score:", f"{score}/100"],
            ["Prediction:", prediction],
            ["Confidence Level:", confidence],
            ["Analysis Method:", results.get('method', 'Heuristic Analysis')]
        ]
        
        table = Table(analysis_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_method_details_section(self, results: Dict) -> Table:
        """Create method-specific details section"""
        if 'methods' in results:
            # Heuristic methods
            methods_data = []
            for method_name, method_results in results['methods'].items():
                method_data = [
                    [f"{method_name.upper()} Analysis", ""],
                    ["Suspicion Score:", f"{method_results.get('lsb_suspicion_score', method_results.get('basic_suspicion_score', 0)):.1f}/100"]
                ]
                
                # Add method-specific metrics
                if method_name == 'lsb':
                    method_data.append(["LSB Entropy:", f"{method_results.get('entropy', 0):.4f}"])
                    method_data.append(["LSB Balance:", f"{method_results.get('lsb_balance', 0):.4f}"])
                elif method_name == 'chi_square':
                    method_data.append(["Chi-Square P-value:", f"{method_results.get('p_value', 0):.4f}"])
                
                methods_data.extend(method_data)
                methods_data.append(["", ""])  # Add spacing
        else:
            # ML method
            methods_data = [
                ["Machine Learning Analysis", ""],
                ["Prediction Probability:", f"{results.get('ml_probability', 0) * 100:.1f}%"],
                ["Model Confidence:", f"{results.get('ml_confidence', 0) * 100:.1f}%"],
                ["Features Used:", "70+ statistical and frequency features"]
            ]
        
        table = Table(methods_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_heatmap_section(self, heatmap_path: str) -> Paragraph:
        """Create heatmap section"""
        return Paragraph(f"<b>Visual Analysis:</b><br/>Heatmap visualization available at: {heatmap_path}", self.custom_style)
    
    def _create_risk_assessment_section(self, results: Dict) -> Table:
        """Create risk assessment section"""
        if 'ml_prediction' in results:
            risk_level = "HIGH" if results['ml_prediction'] == 1 else "LOW"
            recommendation = "Investigate further" if risk_level == "HIGH" else "No immediate action required"
        else:
            score = results.get('final_suspicion_score', 0)
            if score >= 75:
                risk_level = "HIGH"
                recommendation = "Strong evidence of steganography - investigate immediately"
            elif score >= 50:
                risk_level = "MEDIUM"
                recommendation = "Suspicious - recommend further analysis"
            else:
                risk_level = "LOW"
                recommendation = "No significant evidence of steganography"
        
        risk_data = [
            ["Risk Level:", risk_level],
            ["Recommendation:", recommendation],
            ["Next Steps:", "Consider using additional detection methods for verification"]
        ]
        
        # Color coding based on risk
        color_map = {
            "HIGH": colors.red,
            "MEDIUM": colors.orange,
            "LOW": colors.green
        }
        
        table = Table(risk_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_map.get(risk_level, colors.grey)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_batch_summary_section(self, results: List[Dict]) -> Table:
        """Create batch summary statistics"""
        total_files = len(results)
        
        # Count suspicious files
        suspicious_count = 0
        for result in results:
            if 'ml_prediction' in result:
                if result['ml_prediction'] == 1:
                    suspicious_count += 1
            else:
                if result.get('final_suspicion_score', 0) >= 50:
                    suspicious_count += 1
        
        clean_count = total_files - suspicious_count
        
        summary_data = [
            ["Total Files Analyzed:", str(total_files)],
            ["Suspicious Files:", str(suspicious_count)],
            ["Clean Files:", str(clean_count)],
            ["Suspicion Rate:", f"{(suspicious_count/total_files)*100:.1f}%"],
            ["Analysis Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_batch_results_table(self, results: List[Dict]) -> Table:
        """Create detailed batch results table"""
        table_data = [["Filename", "Method", "Score", "Prediction", "Status"]]
        
        for result in results:
            filename = result.get('filename', 'Unknown')
            
            if 'ml_prediction' in result:
                method = "ML"
                score = f"{result.get('ml_probability', 0) * 100:.1f}%"
                prediction = "STEGO" if result['ml_prediction'] == 1 else "CLEAN"
            else:
                method = "Heuristic"
                score = f"{result.get('final_suspicion_score', 0):.1f}"
                prediction = "HIGH" if result.get('final_suspicion_score', 0) >= 50 else "LOW"
            
            status = "⚠️ Suspicious" if prediction in ["STEGO", "HIGH"] else "✅ Clean"
            
            table_data.append([filename, method, score, prediction, status])
        
        table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_footer(self) -> Paragraph:
        """Create report footer"""
        footer_text = f"Generated by StegHunter v1.0.0 on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}"
        return Paragraph(footer_text, self.custom_style)
