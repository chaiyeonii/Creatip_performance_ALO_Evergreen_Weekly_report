import io, json, os, re, warnings
warnings.filterwarnings("ignore")
from py_mini_racer import MiniRacer

SC = os.path.dirname(os.path.abspath(__file__))
D = r"C:\Users\user\my_work\Creatip\performance\ALO\Evergreen_Weekly_Report"
src = io.open(os.path.join(SC, "eval_wb.py"), encoding="utf-8").read()
ns = {"__name__": "core", "__file__": os.path.join(SC, "eval_wb.py")}
exec(compile(src.split("# ---------------- report ----------------")[0], "core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]
S = json.loads(io.open(os.path.join(SC, "summary.json"), encoding="utf-8").read())

# style side-table: (sheet,row,col) -> (fill, fontColor, borderJSON)
style = {}
for n, s in wb["sheets"].items():
    for cell in s["cells"]:
        if len(cell) >= 8:
            style[(n, cell[0], cell[1])] = (cell[5], cell[6], cell[7])

fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


def lum(argb):
    r, g, b = (int(argb[i:i + 2], 16) / 255 for i in (2, 4, 6))
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


print("=" * 100)
print("A. GRIDLINES hidden on every sheet")
print("=" * 100)
for n in wb["order"]:
    v = wb["sheets"][n]["views"]
    check(f"{n:<24} gridlines off", bool(v) and v[0].get("showGridLines") is False, str(v))

print()
print("=" * 100)
print("B. BORDERS are light grey — no heavy black, no brand-tinted lines")
print("=" * 100)
colors = {}
for (n, r, c), (fg, fc, bd) in style.items():
    if not bd:
        continue
    for m in re.finditer(r'"argb":"([0-9A-Fa-f]{8})"', bd):
        colors[m.group(1).upper()] = colors.get(m.group(1).upper(), 0) + 1
print("   border colours in use:", colors)
check("only the two grey border tones are used",
      set(colors) <= {"FFD9DDE4", "FFAEB6C2"}, str(set(colors)))
check("no black border", not any(lum(c) < 0.1 for c in colors))

print()
print("=" * 100)
print("C. BRAND COLOUR drives the headers (harness picked Green)")
print("=" * 100)
ctx = MiniRacer()
ctx.eval(io.open(os.path.join(SC, "harness.js"), encoding="utf-8").read())
ctx.eval(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
                    io.open(os.path.join(D, "index.html"), encoding="utf-8").read(), re.S)[0])
ctx.eval("S.campaign.brandColor='Green'; applyTheme();")
theme = json.loads(ctx.eval("JSON.stringify(THEME)"))
print("   THEME:", {k: v for k, v in theme.items() if k != 'group'})
main = "FF" + theme["main"][1:].upper()
title_fill = style[("Brand Search", 2, 2)][0]
check("Sheet 2 title uses the main colour", title_fill == main, f"{title_fill} vs {main}")
check("Sheet 1 Media Summary header uses the main colour",
      style[("Overall", 13, 2)][0] == main, str(style[("Overall", 13, 2)][0]))
band = "FF" + theme["band"][1:].upper()
check("section band uses the light secondary", style[("Brand Search", 4, 2)][0] == band,
      str(style[("Brand Search", 4, 2)][0]))
pc = "FF" + theme["pc"][1:].upper()
mo = "FF" + theme["mo"][1:].upper()
check("device bands use the PC/MO tints",
      style[("Brand Search", 11, 7)][0] == pc and style[("Brand Search", 11, 11)][0] == mo,
      f"{style[('Brand Search',11,7)][0]} / {style[('Brand Search',11,11)][0]}")
check("secondary is lighter than main", lum(band) > lum(main))
check("PC tint sits between main and secondary", lum(main) <= lum(pc) <= lum(band))

print()
print("=" * 100)
print("D. TEXT CONTRAST on every coloured header cell")
print("=" * 100)
worst, worst_at = 99, None
n_checked = 0
for (n, r, c), (fg, fc, bd) in style.items():
    if not fg or not fc:
        continue
    n_checked += 1
    k = contrast(fg, fc)
    if k < worst:
        worst, worst_at = k, (n, r, c, fg, fc)
check(f"all {n_checked:,} filled cells meet 4.5:1", worst >= 4.5,
      f"worst {worst:.2f}:1 at {worst_at}")

print()
print("=" * 100)
print("E. SECTION HEADER sits directly on top of its table")
print("=" * 100)
lay = [("Overall", 13, 'Media Summary', 'Campaign'),
       ("Brand Search", 5, 'Overview', 'Media'),
       ("Brand Search", 11, 'Daily Breakdown', 'Date'),
       ("Powerlink", 5, 'Overview', 'Media'),
       ("Powerlink", 11, 'Daily Breakdown', 'Date')]
for sheet, band_row, band_txt, first_hdr in lay:
    check(f"{sheet:<13} {band_txt:<18} band row {band_row - 1}",
          disp(sheet, band_row - 1, 2) == band_txt, repr(disp(sheet, band_row - 1, 2)))
    check(f"{sheet:<13} {band_txt:<18} table header right below",
          disp(sheet, band_row, 2) == first_hdr, repr(disp(sheet, band_row, 2)))
GROUPS = ["Branded", "Shoes", "Competitors", "Generic"]
gbands = sorted(r for (s, r, c), (k, v) in grid.items()
                if s == 'Powerlink' and c == 2 and v in GROUPS)
for g, br in zip(GROUPS, gbands):
    check(f"Sheet 4 {g:<12} table header right below the band",
          disp('Powerlink', br + 1, 2) == 'Date', repr(disp('Powerlink', br + 1, 2)))

print()
print("=" * 100)
print("F. BLANK ROW still separates one section from the next")
print("=" * 100)
for sheet in ("Brand Search", "Powerlink"):
    check(f"{sheet:<13} blank row between Overview and Daily Breakdown",
          not [1 for (s, r, c), (k, v) in grid.items()
               if s == sheet and r == 9 and v not in (None, '')], "row 9")
check("Sheet 1 blank row before Media Summary",
      not [1 for (s, r, c), (k, v) in grid.items()
           if s == 'Overall' and r == 11 and v not in (None, '')], "row 11")

print()
print("=" * 100)
print("G. 'Cost' never appears — Spent everywhere")
print("=" * 100)
hits = [(s, r, c) for (s, r, c), (k, v) in grid.items() if v == 'Cost']
check("no 'Cost' label in the workbook", not hits, str(hits[:4]))
for sheet, row in (("Brand Search Keywords", 7), ("Powerlink Keywords", 9)):
    cols = [disp(sheet, row, 2 + i) for i in range(7)]
    check(f"{sheet:<24} column 3 = Spent", cols[2] == 'Spent', str(cols))
check("Daily Breakdown metric 1 = Spent", disp('Brand Search', 12, 3) == 'Spent',
      repr(disp('Brand Search', 12, 3)))

print()
print("=" * 100)
print("H. NUMBERS unchanged + formulas still evaluate")
print("=" * 100)
R_SUB = 8   # overview subtotal row moved up by one
check("Sheet 2 Subtotal Impression", abs(disp('Brand Search', R_SUB, 7) - S["bsImp"]) < 0.01,
      f"{disp('Brand Search',R_SUB,7):,.0f}")
check("Sheet 4 Subtotal Impression", abs(disp('Powerlink', R_SUB, 7) - S["plImp"]) < 0.01,
      f"{disp('Powerlink',R_SUB,7):,.0f}")
check("Overall Total Spent == Media Summary",
      abs(disp('Overall', 7, 3) - disp('Overall', 16, 7)) < 0.01,
      f"{disp('Overall',7,3):,.2f} vs {disp('Overall',16,7):,.2f}")
bad, total_f = [], 0
for n, s in wb["sheets"].items():
    for cell in s["cells"]:
        if cell[2] != 'f':
            continue
        total_f += 1
        try:
            raw_val(n, cell[0], cell[1])
        except Exception as ex:
            bad.append((n, cell[0], cell[1], repr(ex)))
check(f"all {total_f:,} formulas evaluate", not bad, f"{len(bad)} failed")

print()
print("=" * 100)
print("I. EVERY BRAND COLOUR stays readable")
print("=" * 100)
names = json.loads(ctx.eval("JSON.stringify(BRAND_COLORS.map(c=>c[0]))"))
for nm in names:
    ctx.eval(f"S.campaign.brandColor='{nm}'; applyTheme();")
    t = json.loads(ctx.eval("JSON.stringify(THEME)"))
    worst_k = 99
    for key in ("main", "pc", "mo", "mainSub", "pcSub", "moSub", "band", "total"):
        fill = "FF" + t[key][1:].upper()
        tx = json.loads(ctx.eval(f"JSON.stringify(txOf('{fill}'))"))
        worst_k = min(worst_k, contrast(fill, tx))
    check(f"{nm:<10} worst contrast {worst_k:.1f}:1", worst_k >= 4.5)

print()
print("=" * 100)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails[:5])}")
