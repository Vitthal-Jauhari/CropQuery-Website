#!/usr/bin/env python3
"""Copy the working widget from your OLD page into your NEW page, unchanged.
Nothing is retyped: the card markup, its CSS block and its script are cut out of the old file as-is.
Usage: python merge_widget.py older-index.html index.html [output.html]"""
import re, sys, pathlib

old_path, new_path = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out_path = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else new_path.with_name(new_path.stem + ".patched.html")

def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()

def div_block(text, opener):
    """Return (start, end) of the <div ...> that begins with `opener`, including its matching </div>."""
    start = text.find(opener)
    if start < 0:
        sys.exit("Could not find: " + opener)
    depth = 0
    for m in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if m.group().startswith("<div") else -1
        if depth == 0:
            return start, start + m.end()
    sys.exit("Unbalanced <div> tags after: " + opener)

old, new = read(old_path), read(new_path)
if 'id="upload"' in new:
    sys.exit("The new page already contains the widget.")

# 1) pieces of the old widget, exactly as written
s, e = div_block(old, '<div class="scan" id="scan">')
markup = old[s:e]
a, b = old.find("/* scan widget */"), old.find("/* sections */")
if min(a, b) < 0 or b < a:
    sys.exit("Could not find the '/* scan widget */' CSS block in the old page.")
css = old[a:b]
js_start, js_end = old.rfind("<script>"), old.rfind("</script>") + len("</script>")
if js_start < 0 or js_end < js_start:
    sys.exit("Could not find the widget <script> in the old page.")
widget_js = old[js_start:js_end]

# 2) the new page already styles .actions and .error for its placeholder card; rename the widget's copies
css = re.sub(r"(?m)^(\s*)\.actions(\s*\{)", r"\1.scan-actions\2", css)
css = re.sub(r"(?m)^(\s*)\.error(\s*\{)", r"\1.scan-error\2", css)
markup = markup.replace('class="actions"', 'class="scan-actions"').replace('class="error"', 'class="scan-error"')

# 3) give the widget the old page's colours without touching the new page's :root
theme = """
      /* widget theme: values from the old page, scoped to the widget */
      .scan {
        --forest: #0a4a3c; --forest-2: #073a2f; --leaf: #609048; --leaf-d: #3f6b2c;
        --paper: #f6f8f4; --ink: #15211b; --muted: #465549; --line: #d9e2d7;
        --mint: #eaf2e6; --warn: #7a4e00; --warn-bg: #fff4d6;
      }
      .scan h2 { line-height: 1.6; }
      .scan :focus-visible { outline: 3px solid #2563eb; outline-offset: 3px; }
"""

# 4) put it into the new page
i = new.find("</style>")
if i < 0:
    sys.exit("No </style> in the new page.")
new = new[:i] + "\n      " + css.strip() + "\n" + theme + "    " + new[i:]

s, e = div_block(new, '<div class="scan-card" id="scan">')
new = new[:s] + markup + new[e:]

menu_js = """<script>
      const nav = document.querySelector(".main-nav"),
        menu = document.querySelector(".menu-toggle");
      menu.addEventListener("click", () => {
        const open = nav.classList.toggle("open");
        menu.setAttribute("aria-expanded", open);
      });
      document
        .querySelectorAll(".main-nav a")
        .forEach((a) =>
          a.addEventListener("click", () => nav.classList.remove("open")),
        );
    </script>
    """ + widget_js
pat = re.compile(r'<script>\s*const nav = document\.querySelector\("\.main-nav"\).*?</script>', re.S)
new, n = pat.subn(lambda _m: menu_js, new, count=1)
if n != 1:
    sys.exit("Could not find the new page's script.")

with open(out_path, "w", encoding="utf-8", newline="") as f:
    f.write(new)
print("Wrote", out_path)
