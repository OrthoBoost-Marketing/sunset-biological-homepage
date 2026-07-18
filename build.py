#!/usr/bin/env python3
"""Universal partials build for the Sunset Biological Dentistry static site.

Single source of truth for the site-wide header and footer. Edit
partials/header.html or partials/footer.html, then run `python build.py`
to propagate the change into every *.html page in this folder.

Managed regions are delimited by markers and refilled from partials/:
    <!-- HEADER:START ... HEADER:END -->
    <!-- FOOTER:START ... FOOTER:END -->
    <!-- FINDMAP:START ... FINDMAP:END -->   (office map; form pages only)
On the FIRST run (before markers exist) the script finds each page's raw
<header class="site-header"> / <footer class="site-footer"> block and wraps
it in markers. The FINDMAP block is auto-inserted just before </main> on any
page that has the lead form (class="lead-form") but no existing map embed
(output=embed) - so the 11 service pages plus schedule/why-choose/meet-dr get
it, while contact-us and index (which already show a map) are left alone.
Idempotent: running twice produces no further changes.

build.py and partials/ are SOURCE - they are excluded from deployment via
.vercelignore. Usage: python build.py [--check]
"""
import re, glob, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
CHECK = "--check" in sys.argv

def load(p):
    return open(p, encoding="utf-8").read().strip("\n")

HEADER = load("partials/header.html")
FOOTER = load("partials/footer.html")
FINDMAP = load("partials/findmap.html")

def block(name, body):
    start = ("<!-- " + name + ":START - universal region from partials/" + name.lower()
             + ".html. Edit the partial then run build.py. Do not edit between markers. -->")
    return start + "\n" + body + "\n<!-- " + name + ":END -->"

H_BLOCK = block("HEADER", HEADER)
F_BLOCK = block("FOOTER", FOOTER)
FIND_BLOCK = block("FINDMAP", FINDMAP)

# Marker regions (idempotent re-runs)
M_HEADER = re.compile(r"<!-- HEADER:START.*?HEADER:END -->", re.S)
M_FOOTER = re.compile(r"<!-- FOOTER:START.*?FOOTER:END -->", re.S)
M_FIND   = re.compile(r"<!-- FINDMAP:START.*?FINDMAP:END -->", re.S)
# Raw blocks (first run, before markers exist)
R_HEADER = re.compile(r'<header class="site-header">.*?</header>', re.S)
R_FOOTER = re.compile(r'<footer class="site-footer">.*?</footer>', re.S)
# Strip orphan label comments (the bare <!-- HEADER --> / <!-- FOOTER --> tags)
R_ORPHAN = re.compile(r'^[ \t]*<!--\s*(?:HEADER|FOOTER|TOP ?BAR|NAV)\s*-->[ \t]*\n', re.M)

def once(pat, repl, s):
    return pat.subn(lambda m: repl, s, count=1)

def do_region(s, key, marked, raw, blk):
    if key in s:
        return once(marked, blk, s)
    if raw.search(s):
        return once(raw, blk, s)
    return s, 0

results = []
# Root pages AND blog posts (blog/*.html) — one universal header/footer everywhere.
# Blog pages have no markers on first run; the raw-block regex adopts them and wraps
# them in markers. Partials use root-relative (/...) links so they work at any depth.
for page in sorted(glob.glob("*.html")) + sorted(glob.glob("blog/*.html")):
    s0 = open(page, encoding="utf-8").read()
    s = s0
    s, nh = do_region(s, "HEADER:START", M_HEADER, R_HEADER, H_BLOCK)
    s, nf = do_region(s, "FOOTER:START", M_FOOTER, R_FOOTER, F_BLOCK)
    s = R_ORPHAN.sub("", s)
    # FINDMAP: refill if present; else auto-insert before </main> on form pages
    # that don't already show a map. Optional - never causes a SKIP.
    nfm = 0
    if "FINDMAP:START" in s:
        s, nfm = once(M_FIND, FIND_BLOCK, s)
    elif 'class="lead-form"' in s and "output=embed" not in s and "</main>" in s:
        s, nfm = once(re.compile(r"</main>"), FIND_BLOCK + "\n\n  </main>", s)
    if nh != 1 or nf != 1:
        results.append((page, "SKIP", "header=%s footer=%s (region not found)" % (nh, nf)))
        continue
    if s != s0 and not CHECK:
        open(page, "w", encoding="utf-8", newline="").write(s)
    results.append((page, "OK" if s != s0 else "UNCHANGED", "map=%d" % nfm))

w = max(len(r[0]) for r in results)
for name, status, note in results:
    print("%-*s  %-9s %s" % (w, name, status, note))
skipped = [r for r in results if r[1] == "SKIP"]
print("\nBUILD: %d written, %d unchanged, %d skipped." % (
    sum(1 for r in results if r[1] == "OK"),
    sum(1 for r in results if r[1] == "UNCHANGED"),
    len(skipped)))
if skipped:
    print("Skipped:", ", ".join(r[0] for r in skipped))
