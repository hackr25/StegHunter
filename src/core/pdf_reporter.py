"""
Professional PDF Report Generator for StegHunter Analysis Results
Generates attractive, comprehensive PDF reports using WeasyPrint
"""

import base64
from pathlib import Path
from datetime import datetime


class PDFReporter:
    """Generates professional PDF reports for steganography analysis"""
    
    def __init__(self):
        """Initialize PDF reporter"""
        try:
            from weasyprint import HTML, CSS
            self.HTML = HTML
            self.CSS = CSS
        except ImportError:
            raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")
    
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
        # Generate HTML content
        html_content = self._generate_html(analysis_results, image_path)
        
        # Generate PDF
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(output_pdf_path)
            return output_pdf_path
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _generate_html(self, analysis_results: dict, image_path: str) -> str:
        """Generate professional HTML for PDF"""
        
        # Encode image to base64
        image_base64 = self._encode_image_to_base64(image_path)
        
        # Extract analysis data
        verdict = analysis_results.get('verdict', 'UNKNOWN')
        confidence = analysis_results.get('confidence_score', 0)
        methods_used = analysis_results.get('methods_used', [])
        overall_score = analysis_results.get('overall_score', 0)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get hiding locations if available
        hiding_locs = analysis_results.get('hiding_locations', {})
        
        # Build sections
        verdict_color = self._get_verdict_color(verdict)
        verdict_border_color = self._get_verdict_border_color(verdict)
        methods_html = self._build_methods_section(analysis_results)
        locations_html = self._build_locations_section(hiding_locs)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    color: #333;
                    line-height: 1.6;
                }}
                
                .page {{
                    background-color: white;
                    page-break-after: always;
                    padding: 40px;
                }}
                
                .header {{
                    border-bottom: 3px solid #0066CC;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #0066CC;
                    margin-bottom: 10px;
                }}
                
                .subtitle {{
                    font-size: 12px;
                    color: #666;
                }}
                
                .timestamp {{
                    font-size: 11px;
                    color: #999;
                    margin-top: 10px;
                }}
                
                .verdict-section {{
                    background-color: {verdict_color};
                    border-left: 5px solid {verdict_border_color};
                    padding: 20px;
                    margin-bottom: 30px;
                    border-radius: 4px;
                    color: white;
                }}
                
                .verdict-title {{
                    font-size: 14px;
                    font-weight: bold;
                    text-transform: uppercase;
                    margin-bottom: 10px;
                }}
                
                .verdict-content {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                
                .verdict-text {{
                    font-size: 16px;
                    font-weight: bold;
                }}
                
                .confidence {{
                    font-size: 18px;
                    font-weight: bold;
                }}
                
                .section {{
                    margin-bottom: 30px;
                }}
                
                .section-title {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #0066CC;
                    border-bottom: 2px solid #0066CC;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }}
                
                .image-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                
                .image-container img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .image-label {{
                    font-size: 11px;
                    color: #666;
                    margin-top: 5px;
                    font-style: italic;
                }}
                
                .grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                
                .stat-box {{
                    background-color: #f9f9f9;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 15px;
                }}
                
                .stat-label {{
                    font-size: 11px;
                    color: #666;
                    text-transform: uppercase;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                
                .stat-value {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #0066CC;
                }}
                
                .methods-list {{
                    background-color: #f9f9f9;
                    border-left: 4px solid #0066CC;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 2px;
                }}
                
                .method-item {{
                    margin-bottom: 10px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                
                .method-item:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                    padding-bottom: 0;
                }}
                
                .method-name {{
                    font-weight: bold;
                    color: #333;
                    font-size: 12px;
                }}
                
                .method-score {{
                    font-size: 11px;
                    color: #0066CC;
                }}
                
                .method-desc {{
                    font-size: 11px;
                    color: #666;
                    margin-top: 3px;
                }}
                
                .locations-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                
                .location-box {{
                    background-color: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 12px;
                    font-size: 11px;
                }}
                
                .location-title {{
                    font-weight: bold;
                    color: #0066CC;
                    margin-bottom: 5px;
                }}
                
                .location-info {{
                    color: #666;
                    margin-bottom: 3px;
                }}
                
                .suspicion-high {{
                    color: #d32f2f;
                    font-weight: bold;
                }}
                
                .suspicion-medium {{
                    color: #f57c00;
                    font-weight: bold;
                }}
                
                .suspicion-low {{
                    color: #388e3c;
                    font-weight: bold;
                }}
                
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 10px;
                    color: #999;
                    text-align: center;
                }}
                
                .progress-bar {{
                    background-color: #e0e0e0;
                    border-radius: 3px;
                    height: 20px;
                    overflow: hidden;
                    margin-top: 5px;
                }}
                
                .progress-fill {{
                    background-color: #0066CC;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <!-- Header -->
                <div class="header">
                    <div class="logo">🔍 StegHunter Analysis Report</div>
                    <div class="subtitle">Professional Steganography Detection Analysis</div>
                    <div class="timestamp">Generated on {timestamp}</div>
                </div>
                
                <!-- Verdict Section -->
                <div class="verdict-section">
                    <div class="verdict-title">Analysis Verdict</div>
                    <div class="verdict-content">
                        <div class="verdict-text">{verdict}</div>
                        <div class="confidence">Confidence: {confidence:.1f}%</div>
                    </div>
                </div>
                
                <!-- Overview Statistics -->
                <div class="section">
                    <div class="section-title">📊 Analysis Overview</div>
                    <div class="grid">
                        <div class="stat-box">
                            <div class="stat-label">Overall Score</div>
                            <div class="stat-value">{overall_score:.1f}/100</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {overall_score}%">{overall_score:.0f}%</div>
                            </div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-label">Confidence Level</div>
                            <div class="stat-value">{confidence:.1f}%</div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {confidence}%">{confidence:.0f}%</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Image Analysis -->
                <div class="section">
                    <div class="section-title">🖼️ Analyzed Image</div>
                    <div class="image-container">
                        <img src="data:image/jpeg;base64,{image_base64}" alt="Analyzed Image">
                        <div class="image-label">File: {Path(image_path).name}</div>
                    </div>
                </div>
                
                <!-- Methods Used -->
                <div class="section">
                    <div class="section-title">🔬 Detection Methods</div>
                    {methods_html}
                </div>
                
                <!-- Hiding Locations -->
                {locations_html}
                
                <!-- Footer -->
                <div class="footer">
                    <p>This report was generated by StegHunter - Professional Steganography Detection Tool</p>
                    <p>For more information, visit: https://github.com/hackr25/StegHunter</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _build_methods_section(self, analysis_results: dict) -> str:
        """Build methods section HTML"""
        methods = analysis_results.get('methods_used', [])
        
        if not methods:
            return "<p>No detection methods applied.</p>"
        
        html = '<div class="methods-list">'
        for method in methods:
            name = method.get('name', 'Unknown Method')
            score = method.get('score', 0)
            description = method.get('description', '')
            
            html += f"""
            <div class="method-item">
                <div class="method-name">• {name}</div>
                <div class="method-score">Score: {score:.1f}/100</div>
                <div class="method-desc">{description}</div>
            </div>
            """
        
        html += '</div>'
        return html
    
    def _build_locations_section(self, hiding_locations: dict) -> str:
        """Build hiding locations section HTML"""
        
        if not hiding_locations:
            return ""
        
        html = '<div class="section"><div class="section-title">📍 Potential Hiding Locations</div>'
        
        # Channel Analysis
        channel_analysis = hiding_locations.get('channel_analysis', {})
        if channel_analysis:
            html += '<div><strong>Channel Analysis:</strong></div>'
            rgb_lsb = channel_analysis.get('rgb_lsb', {})
            for channel, data in rgb_lsb.items():
                if data.get('suspicious'):
                    suspicion = data.get('suspicion_level', 'MEDIUM')
                    html += f'<div class="location-info">• <strong>{channel}:</strong> {suspicion} suspicion</div>'
        
        # Suspicious Areas
        suspicious_areas = hiding_locations.get('suspicious_areas', [])
        if suspicious_areas:
            html += '<div style="margin-top: 15px;"><strong>Specific Areas:</strong></div>'
            html += '<div class="locations-grid">'
            for area in suspicious_areas[:4]:  # Show top 4
                location = area.get('location', 'Unknown')
                score = area.get('suspicion_score', 0)
                reason = area.get('reason', '')
                
                suspicion_class = 'suspicion-high' if score > 75 else 'suspicion-medium' if score > 50 else 'suspicion-low'
                
                html += f"""
                <div class="location-box">
                    <div class="location-title">{location}</div>
                    <div class="location-info">
                        Suspicion: <span class="{suspicion_class}">{score:.1f}%</span>
                    </div>
                    <div class="location-info">{reason}</div>
                </div>
                """
            html += '</div>'
        
        html += '</div>'
        return html
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for embedding in HTML"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
        except Exception:
            # Return a placeholder if image can't be read
            return ""
    
    def _get_verdict_color(self, verdict: str) -> str:
        """Get background color based on verdict"""
        verdict_upper = verdict.upper()
        if 'DETECTED' in verdict_upper or 'POSITIVE' in verdict_upper:
            return '#d32f2f'  # Red - steganography detected
        elif 'SUSPICIOUS' in verdict_upper:
            return '#f57c00'  # Orange - possibly suspicious
        elif 'CLEAN' in verdict_upper or 'NEGATIVE' in verdict_upper:
            return '#388e3c'  # Green - clean
        else:
            return '#1976d2'  # Blue - neutral
    
    def _get_verdict_border_color(self, verdict: str) -> str:
        """Get border color based on verdict"""
        verdict_upper = verdict.upper()
        if 'DETECTED' in verdict_upper or 'POSITIVE' in verdict_upper:
            return '#b71c1c'  # Darker red
        elif 'SUSPICIOUS' in verdict_upper:
            return '#e65100'  # Darker orange
        elif 'CLEAN' in verdict_upper or 'NEGATIVE' in verdict_upper:
            return '#1b5e20'  # Darker green
        else:
            return '#0d47a1'  # Darker blue
