# How to Convert STEGHUNTER_PROFESSIONAL_REPORT.md to PDF

You now have a professional markdown report that can be converted to a beautiful PDF document, similar to your NFSU_XAI_IDS_Report.pdf.

---

## Quick Start (Fastest Method)

### Method 1: VS Code Print to PDF (No Installation Needed) ⭐

**Steps:**
1. Open VS Code
2. Open file: `STEGHUNTER_PROFESSIONAL_REPORT.md`
3. Press `Ctrl+K Ctrl+P` (or `Cmd+K Cmd+P` on Mac)
4. In the command palette, type: `Markdown: Open Preview to the Side`
5. Right-click the preview → **Print** (or `Ctrl+P`)
6. Select: **Save as PDF**
7. Click "Save"

**Result:** Professional PDF with table of contents, formatting, and styling.

---

## Method 2: Online Converter (No Installation)

### Using Markdown to PDF Online Tools

**Option A: Pandoc Online**
1. Visit: https://pandoc.org/try/
2. Copy entire markdown content (Ctrl+A on the markdown file)
3. Paste into "Input" box
4. Select output: "PDF"
5. Click "Convert"
6. Click "Download PDF"

**Option B: CloudConvert**
1. Visit: https://cloudconvert.com/md-to-pdf
2. Upload: `STEGHUNTER_PROFESSIONAL_REPORT.md`
3. Click "Convert"
4. Download the PDF

---

## Method 3: Pandoc (Professional Quality) ⭐⭐

### Install Pandoc

**Windows (via Chocolatey):**
```bash
choco install pandoc
```

**Windows (via Direct Download):**
1. Visit: https://pandoc.org/installing.html
2. Download Windows installer
3. Run installer

**macOS:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install pandoc
```

### Convert to PDF (Basic)

```bash
cd C:\Users\Soumya Dubey\OneDrive\Desktop\Shubham\StegHunter\
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf
```

### Convert to PDF (Professional Quality)

```bash
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md \
  -o STEGHUNTER_PROFESSIONAL_REPORT.pdf \
  --listings \
  --number-sections \
  --toc \
  --highlight-style espresso
```

### Convert with Custom Styling (Advanced)

```bash
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md \
  -o STEGHUNTER_PROFESSIONAL_REPORT.pdf \
  --metadata title="StegHunter: Professional Forensic Analysis Suite" \
  --metadata author="Shubham" \
  --metadata date="April 2026" \
  --listings \
  --number-sections \
  --toc \
  --template eisvogel \
  --highlight-style github
```

**Note:** If you get "eisvogel" template not found error, use the basic version above (still looks great!).

---

## Method 4: Using Python

### Install pypandoc

```bash
pip install pypandoc
```

### Convert with Python Script

```python
import pypandoc

output = pypandoc.convert_file(
    'STEGHUNTER_PROFESSIONAL_REPORT.md',
    'pdf',
    outputfile='STEGHUNTER_PROFESSIONAL_REPORT.pdf',
    extra_args=[
        '--listings',
        '--number-sections',
        '--toc',
        '--highlight-style=github'
    ]
)
print(f"PDF created successfully! Output: {output}")
```

**Run:**
```bash
python convert_to_pdf.py
```

---

## Method 5: Git Hub's Built-in PDF Viewer

1. Commit and push the markdown file to GitHub
2. Visit: https://github.com/hackr25/StegHunter/blob/main/STEGHUNTER_PROFESSIONAL_REPORT.md
3. Right-click anywhere on the page
4. Click **Print** (or press `Ctrl+P`)
5. Select printer: **Save as PDF**
6. Save the file

---

## Recommended Approach

### For Best Results:

**Step 1:** Use **Pandoc** (professional quality)
```bash
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf --toc --number-sections
```

**Step 2:** Check the output PDF
- Open in Adobe Reader or your PDF viewer
- Verify formatting looks good
- Check table of contents

**Step 3:** If you want further customization:
- Install Pandoc template: `eisvogel`
- Or use online tools for additional styling

---

## Customization Options

### Add a Cover Page

**Option 1: Using Metadata**
```bash
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md \
  -o STEGHUNTER_PROFESSIONAL_REPORT.pdf \
  --metadata title="StegHunter: Professional Forensic Analysis Suite" \
  --metadata author="Shubham" \
  --metadata date="April 2026" \
  --toc \
  --number-sections
```

**Option 2: Create Separate Cover Page (cover.md)**

Create `cover.md`:
```markdown
---
title: StegHunter
subtitle: Professional Forensic Analysis Suite
author: Shubham
date: April 2026
---
```

Then convert both files:
```bash
pandoc cover.md STEGHUNTER_PROFESSIONAL_REPORT.md \
  -o STEGHUNTER_PROFESSIONAL_REPORT.pdf \
  --toc \
  --number-sections
```

---

## Troubleshooting

### "Command not found: pandoc"
**Solution:** Pandoc is not installed. Use Method 1 (VS Code) or Method 2 (online) instead.

### PDF looks ugly / formatting is off
**Solution:** 
1. Try Method 1 (VS Code) instead
2. Or install the `eisvogel` template for Pandoc:
   ```bash
   pandoc -D latex > eisvogel.latex
   ```

### Markdown symbols/tables not displaying
**Solution:** This is normal for complex markdown. The PDF will still be readable. If needed:
1. Use online converter (CloudConvert)
2. Or manually format as PDF using Word

### File path issues
**Solution:** Use full absolute path:
```bash
pandoc "C:\Users\Soumya Dubey\OneDrive\Desktop\Shubham\StegHunter\STEGHUNTER_PROFESSIONAL_REPORT.md" \
  -o "C:\Users\Soumya Dubey\OneDrive\Desktop\Shubham\StegHunter\STEGHUNTER_PROFESSIONAL_REPORT.pdf"
```

---

## File Organization After Conversion

After creating the PDF, your StegHunter folder will have:

```
StegHunter/
├── STEGHUNTER_PROFESSIONAL_REPORT.md          (Markdown source)
├── STEGHUNTER_PROFESSIONAL_REPORT.pdf         (PDF output) ⭐ NEW
├── PDF_CONVERSION_GUIDE.md                    (This file)
├── NFSU_XAI_IDS_Report.pdf                    (Your reference)
├── README.md
├── src/
├── tests/
└── ...
```

---

## Next Steps

1. **Convert to PDF** using one of the methods above
2. **Review the PDF** — verify formatting and content
3. **Use for presentation** — share with stakeholders, professors, etc.
4. **Customize further** if needed (add your branding, logos, etc.)

---

## Example Commands Summary

**Windows CMD:**
```cmd
REM Using Pandoc (basic)
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf

REM Using Pandoc (professional)
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf --toc --number-sections --listings
```

**PowerShell:**
```powershell
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf `
  --toc --number-sections
```

**Linux/macOS:**
```bash
pandoc STEGHUNTER_PROFESSIONAL_REPORT.md -o STEGHUNTER_PROFESSIONAL_REPORT.pdf \
  --toc --number-sections --listings
```

---

**Questions? Need help?**

Feel free to ask! The markdown document is fully formatted and ready for conversion. Choose whichever method works best for you. Method 1 (VS Code) is the easiest if you have VS Code installed.

Good luck with your presentation! 🎉
