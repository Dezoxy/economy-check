#!/usr/bin/env python3
"""Render a report .md into a styled PDF (the delivery artifact).

  python3 shared/delivery/render_pdf.py <report.md> [--keep-html]

Pipeline: markdown-subset -> house-styled HTML -> Chrome headless print-to-pdf.
Stdlib only; Chrome is a system tool (like pdftotext in ingestion). If Chrome is
missing the HTML is still produced and we exit 3 — delivery falls back to the .md.

Markdown subset handled (all our templates use only this): # ## headings,
- bullets, **bold**, *italic*, <!-- --> comments (chart placeholders: stripped),
[src:provider/date] tags (rendered as small gray superscripts per style-guide.md).
"""
import html
import os
import re
import subprocess
import sys

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
]

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt;
       line-height: 1.55; color: #1a1a1a; margin: 0; padding: 16mm 18mm; }
.masthead { border-bottom: 3px solid #1a1a2e; padding-bottom: 6px; margin-bottom: 14px; }
.masthead .brand { font-family: -apple-system, Helvetica, Arial, sans-serif;
       font-size: 8.5pt; letter-spacing: 2.5px; text-transform: uppercase; color: #8a8a8a; }
h1 { font-size: 19pt; margin: 2px 0 0 0; color: #1a1a2e; line-height: 1.2; }
h2 { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 10.5pt;
     letter-spacing: 1.2px; text-transform: uppercase; color: #1a1a2e;
     border-bottom: 1px solid #d5d5dc; padding-bottom: 3px; margin: 18px 0 7px 0; }
p { margin: 6px 0; text-align: justify; }
ul { margin: 6px 0; padding-left: 17px; }
li { margin: 3px 0; text-align: justify; }
strong { color: #111; }
.src { font-family: -apple-system, Helvetica, Arial, sans-serif; font-size: 6.8pt;
       color: #9a9aa5; vertical-align: super; line-height: 0; white-space: nowrap; }
.lead em { color: #555; }
.footer-note { margin-top: 16px; padding: 8px 11px; background: #f4f4f7;
       border-left: 3px solid #1a1a2e; font-size: 8.8pt; color: #555;
       font-style: italic; text-align: justify; }
"""


def md_to_html(md_text):
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.S)  # chart placeholders

    def inline(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"\[src:([a-z0-9_.-]+)/(\d{4}-\d{2}-\d{2})\]",
                   r'<span class="src">\1/\2</span>', s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
        return s

    out, in_list, first_para_after_h1 = [], False, False
    title = "Report"
    for raw in md_text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        def close_list():
            nonlocal in_list
            if in_list:
                out.append("</ul>")
                in_list = False

        if not stripped:
            close_list()
            continue
        if stripped.startswith("# ") and not stripped.startswith("## "):
            close_list()
            title = stripped[2:].strip()
            out.append('<div class="masthead"><div class="brand">economy-check '
                       '&middot; heti piaci update</div><h1>%s</h1></div>'
                       % inline(title))
            first_para_after_h1 = True
        elif stripped.startswith("## "):
            close_list()
            out.append("<h2>%s</h2>" % inline(stripped[3:].strip()))
            first_para_after_h1 = False
        elif re.match(r"^- ", stripped):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>%s</li>" % inline(stripped[2:].strip()))
        else:
            close_list()
            cls = ' class="lead"' if first_para_after_h1 else ""
            # the closing legal block gets the footer style
            if "nem minősül befektetési tanácsadásnak" in stripped:
                out.append('<p class="footer-note">%s</p>' % inline(stripped))
            else:
                out.append("<p%s>%s</p>" % (cls, inline(stripped)))
            first_para_after_h1 = False
    close_list()
    doc = ("<!DOCTYPE html><html lang=\"hu\"><head><meta charset=\"utf-8\">"
           "<title>%s</title><style>%s</style></head><body>%s</body></html>"
           % (html.escape(title), CSS, "\n".join(out)))
    return doc


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    return None


def render(md_path, keep_html=False):
    md_text = open(md_path, encoding="utf-8").read()
    base = re.sub(r"\.md$", "", md_path)
    html_path, pdf_path = base + ".html", base + ".pdf"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(md_to_html(md_text))
    chrome = find_chrome()
    if chrome is None:
        print("Chrome not found — HTML written to %s, PDF skipped" % html_path,
              file=sys.stderr)
        return None, html_path, 3
    try:
        subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
             "--print-to-pdf=%s" % pdf_path, "file://%s" % os.path.abspath(html_path)],
            capture_output=True, timeout=60, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print("Chrome PDF render failed: %s" % e, file=sys.stderr)
        return None, html_path, 3
    if not keep_html:
        os.remove(html_path)
        html_path = None
    return pdf_path, html_path, 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    md_path = args[0]
    if not os.path.exists(md_path):
        print("no such report: %s" % md_path, file=sys.stderr)
        sys.exit(2)
    pdf, html_out, code = render(md_path, keep_html="--keep-html" in sys.argv)
    if pdf:
        print("PDF: %s (%d bytes)" % (pdf, os.path.getsize(pdf)))
    sys.exit(code)


if __name__ == "__main__":
    main()
