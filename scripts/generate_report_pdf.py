import os
import re
import subprocess

MD_PATH = "/Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.md"
HTML_PATH = "/Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.html"
PDF_PATH = "/Users/parthbiradar/ACE/Elevance-project/docs/INTERNSHIP_REPORT.pdf"

with open(MD_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# Simple markdown to HTML parser for standard report elements
lines = text.split("\n")
html_lines = []
in_table = False
table_headers = []

for line in lines:
    line_str = line.strip()

    # Table handling
    if "|" in line_str and ("---" in line_str or in_table or line_str.startswith("|")):
        if "---" in line_str:
            continue
        cells = [c.strip() for c in line_str.split("|")[1:-1]]
        if not in_table:
            in_table = True
            html_lines.append("<div class='table-container'><table><thead><tr>")
            for c in cells:
                html_lines.append(f"<th>{c}</th>")
            html_lines.append("</tr></thead><tbody>")
        else:
            html_lines.append("<tr>")
            for c in cells:
                # bold formatting inside table
                c_fmt = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", c)
                c_fmt = re.sub(r"\*(.*?)\*", r"<em>\1</em>", c_fmt)
                html_lines.append(f"<td>{c_fmt}</td>")
            html_lines.append("</tr>")
        continue
    elif in_table:
        in_table = False
        html_lines.append("</tbody></table></div>")

    if not line_str:
        html_lines.append("<br>")
        continue

    # Headers
    if line_str.startswith("# "):
        html_lines.append(f"<h1 class='report-title'>{line_str[2:]}</h1>")
    elif line_str.startswith("## "):
        html_lines.append(f"<h2 class='section-title'>{line_str[3:]}</h2>")
    elif line_str.startswith("### "):
        html_lines.append(f"<h3 class='subsection-title'>{line_str[4:]}</h3>")
    elif line_str.startswith("#### "):
        html_lines.append(f"<h4 class='subsubsection-title'>{line_str[5:]}</h4>")
    elif line_str == "---":
        html_lines.append("<hr class='divider'>")
    elif line_str.startswith("- "):
        content = line_str[2:]
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        html_lines.append(f"<li>{content}</li>")
    elif re.match(r"^\d+\.\s", line_str):
        num, content = re.match(r"^(\d+)\.\s(.*)", line_str).groups()
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        html_lines.append(f"<p class='numbered-item'><strong>{num}.</strong> {content}</p>")
    else:
        content = line_str
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*(.*?)\*", r"<em>\1</em>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        html_lines.append(f"<p>{content}</p>")

if in_table:
    html_lines.append("</tbody></table></div>")

body_content = "\n".join(html_lines)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ElevanceSkills Internship Final Report - Parth Biradar</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm 15mm 20mm 15mm;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      line-height: 1.6;
      font-size: 11pt;
      background: #ffffff;
      padding: 20px 40px;
    }}
    .report-title {{
      font-size: 22pt;
      color: #0f172a;
      text-align: center;
      margin-bottom: 4px;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .section-title {{
      font-size: 14pt;
      color: #1e3a8a;
      border-bottom: 2px solid #3b82f6;
      padding-bottom: 6px;
      margin-top: 24pt;
      margin-bottom: 12pt;
      page-break-after: avoid;
    }}
    .subsection-title {{
      font-size: 12pt;
      color: #0369a1;
      margin-top: 14pt;
      margin-bottom: 6pt;
      page-break-after: avoid;
    }}
    .divider {{
      border: 0;
      height: 1px;
      background: #cbd5e1;
      margin: 20px 0;
    }}
    p {{
      margin: 6px 0;
      text-align: justify;
    }}
    li {{
      margin: 4px 0;
    }}
    code {{
      background: #f1f5f9;
      color: #0f172a;
      padding: 2px 5px;
      border-radius: 4px;
      font-family: Menlo, Monaco, Consolas, monospace;
      font-size: 9.5pt;
      border: 1px solid #e2e8f0;
    }}
    .table-container {{
      margin: 14px 0;
      page-break-inside: avoid;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
      font-size: 9.5pt;
    }}
    th {{
      background: #f8fafc;
      color: #0f172a;
      font-weight: 700;
      border: 1px solid #cbd5e1;
      padding: 8px 10px;
      text-align: left;
    }}
    td {{
      border: 1px solid #cbd5e1;
      padding: 8px 10px;
      vertical-align: top;
    }}
    tr:nth-child(even) {{
      background: #f8fafc;
    }}
  </style>
</head>
<body>
{body_content}
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated HTML report at: {HTML_PATH}")

# Convert to PDF via headless Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cmd = [
    chrome_path,
    "--headless",
    "--disable-gpu",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]
subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"Generated PDF report at: {PDF_PATH}")
