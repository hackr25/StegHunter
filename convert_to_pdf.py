#!/usr/bin/env python3
"""
Convert STEGHUNTER_PROFESSIONAL_REPORT.md to PDF
This script downloads Pandoc if not available
"""

import pypandoc
import os
import sys

def convert_to_pdf():
    """Convert markdown report to PDF"""
    input_file = "STEGHUNTER_PROFESSIONAL_REPORT.md"
    output_file = "STEGHUNTER_PROFESSIONAL_REPORT.pdf"
    
    # Check if markdown file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found in current directory")
        return False
    
    try:
        print(f"📝 Converting {input_file} to PDF...")
        print("⏳ First run may take a minute (downloading Pandoc)...")
        
        # Download pandoc if not available
        try:
            pypandoc.download_pandoc()
            print("✅ Pandoc downloaded successfully")
        except Exception as e:
            print(f"⚠️ Could not download Pandoc: {e}")
            print("Will attempt conversion anyway...")
        
        # Try to convert (with correct Pandoc 2.x arguments)
        pypandoc.convert_file(
            input_file,
            'pdf',
            outputfile=output_file,
            extra_args=[
                '--toc',
                '--number-sections',
                '--variable', 'geometry:margin=1in'
            ]
        )
        
        # Check if file was created successfully
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            print(f"✅ SUCCESS! PDF created successfully!")
            print(f"📊 File: {output_file}")
            print(f"📈 Size: {file_size:.2f} MB")
            print(f"\n🎉 Your professional report is ready!")
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        print("\n📌 Alternative Methods:")
        print("   1. Use VS Code: Open file → Markdown Preview → Print → Save as PDF (Easiest!)")
        print("   2. Use online converter: https://cloudconvert.com/md-to-pdf")
        print("   3. Use Pandoc: https://pandoc.org/installing.html")
        return False

if __name__ == "__main__":
    success = convert_to_pdf()
    sys.exit(0 if success else 1)
