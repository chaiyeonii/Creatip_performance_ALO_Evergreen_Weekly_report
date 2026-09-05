import io, json, os

SC = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(SC, "eval_wb.py"), encoding="utf-8").read()
ns = {"__name__": "core", "__file__": os.path.join(SC, "eval_wb.py")}
exec(compile(src.split("# ---------------- report ----------------")[0], "core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]
S = json.loads(io.open(os.path.join(SC, "summary.json"), encoding="utf-8").read())

GROUPS = ["Branded", "Shoes", "Competitors", "Generic"]
PC, SP, MO = 2, 9, 10          # column B, I, J
COLS = ['Keyword (EN)', 'Keyword (KO)', 'Spent', 'Imp', 'Click', 'CTR', 'CPC']
fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


def val(sheet, r, c):
    e = grid.get((sheet, r, c))
    return None if e is None else e[1]


print("=" * 100)
print("A. KEYWORD SHEET COLUMNS — EN | KO | Spent | Imp | Click | CTR | CPC  (x2, spacer between)")
print("=" * 100)
for sheet, hdr_row in (("Brand Search Keywords", 7), ("Powerlink Keywords", 9)):
    pc = [disp(sheet, hdr_row, PC + i) for i in range(7)]
    mo = [disp(sheet, hdr_row, MO + i) for i in range(7)]
    check(f"{sheet:<24} PC columns", pc == COLS, str(pc))
    check(f"{sheet:<24} MO columns", mo == COLS, str(mo))
    used = [(r, v) for (s, r, c), (k, v) in grid.items()
            if s == sheet and c == SP and r >= 5 and v not in (None, '')]
    cross = [m for m in wb["sheets"][sheet]["merges"] if m[1] <= SP <= m[3] and m[0] >= 5]
    check(f"{sheet:<24} spacer col I empty", not used and not cross,
          f"{len(used)} cells / {len(cross)} merges")
    w = {int(k): v for k, v in wb["sheets"][sheet]["cols"].items()}
    check(f"{sheet:<24} spacer narrow", w.get(SP, 99) <= 4, str(w.get(SP)))

print()
print("=" * 100)
print("B. TOTAL ROW SITS ABOVE THE KEYWORDS")
print("=" * 100)
# Sheet 3: device band 6, column header 7, TOTAL 8, data 9+
check("Sheet 3 row 6 = device band", disp('Brand Search Keywords', 6, PC) == 'Brand Search_PC')
check("Sheet 3 row 7 = column header", disp('Brand Search Keywords', 7, PC) == 'Keyword (EN)')
check("Sheet 3 row 8 = TOTAL", disp('Brand Search Keywords', 8, PC) == 'TOTAL')
check("Sheet 3 row 9 = first keyword",
      isinstance(val('Brand Search Keywords', 9, PC), str) and val('Brand Search Keywords', 9, PC) != 'TOTAL',
      repr(val('Brand Search Keywords', 9, PC)))
last = max(r for (s, r, c) in grid if s == 'Brand Search Keywords' and c == PC)
check("Sheet 3 has no TOTAL at the bottom", val('Brand Search Keywords', last, PC) != 'TOTAL',
      repr(val('Brand Search Keywords', last, PC)))

print()
print("=" * 100)
print("C. SHEET 5 — per ad group: band, column header, TOTAL, keywords, blank")
print("=" * 100)
band_rows = sorted(r for (s, r, c), (k, v) in grid.items()
                   if s == 'Powerlink Keywords' and c == PC and v in GROUPS)
check("four ad-group bands, in order",
      [disp('Powerlink Keywords', r, PC) for r in band_rows] == GROUPS, str(band_rows))
for g, br in zip(GROUPS, band_rows):
    check(f"{g:<12} band -> column header", disp('Powerlink Keywords', br + 1, PC) == 'Keyword (EN)')
    check(f"{g:<12} column header -> TOTAL",
          disp('Powerlink Keywords', br + 2, PC) == g + ' TOTAL',
          repr(disp('Powerlink Keywords', br + 2, PC)))
    first_kw = val('Powerlink Keywords', br + 3, PC)
    check(f"{g:<12} keywords start right after TOTAL",
          isinstance(first_kw, str) and 'TOTAL' not in first_kw, repr(first_kw))
for i in range(3):
    gap = band_rows[i + 1] - 1
    check(f"blank row before {GROUPS[i+1]}",
          not [1 for (s, r, c), (k, v) in grid.items()
               if s == 'Powerlink Keywords' and r == gap and v not in (None, '')],
          f"row {gap}")

print()
print("=" * 100)
print("D. TOTAL VALUES — SUM of the block, CTR and CPC recalculated")
print("=" * 100)


def block_sum(sheet, base, first, n, off):
    return sum(v for r in range(first, first + n)
               for v in [val(sheet, r, base + off)] if isinstance(v, (int, float)))


def count_rows(sheet, base, first):
    n = 0
    while isinstance(val(sheet, first + n, base), str) and val(sheet, first + n, base):
        n += 1
    return n


for sheet, total_row, label in (("Brand Search Keywords", 8, "Sheet 3"),):
    for base, dev in ((PC, "PC"), (MO, "MO")):
        n = count_rows(sheet, base, total_row + 1)
        for off, name in ((2, "Spent"), (3, "Imp"), (4, "Click")):
            want = block_sum(sheet, base, total_row + 1, n, off)
            got = disp(sheet, total_row, base + off)
            check(f"{label} {dev} TOTAL {name}", abs(got - want) < 0.01, f"{got:,.2f} vs {want:,.2f}")
        ctr, cpc = disp(sheet, total_row, base + 5), disp(sheet, total_row, base + 6)
        imp, clk, cost = (disp(sheet, total_row, base + o) for o in (3, 4, 2))
        check(f"{label} {dev} TOTAL CTR = Click/Imp", abs(ctr - clk / imp) < 1e-9, f"{ctr*100:.2f}%")
        check(f"{label} {dev} TOTAL CPC = Spent/Click", abs(cpc - cost / clk) < 1e-9, f"{cpc:.4f}")

for g, br in zip(GROUPS, band_rows):
    tr = br + 2
    for base, dev in ((PC, "PC"), (MO, "MO")):
        n = count_rows('Powerlink Keywords', base, tr + 1)
        want = block_sum('Powerlink Keywords', base, tr + 1, n, 3)
        got = disp('Powerlink Keywords', tr, base + 3)
        check(f"{g:<12} {dev} TOTAL Imp", abs(got - want) < 0.01, f"{got:,.0f} vs {want:,.0f} ({n} rows)")

print()
print("=" * 100)
print("E. SORT ORDER — Impression DESC under every TOTAL")
print("=" * 100)
for sheet, first, base, lab in (("Brand Search Keywords", 9, PC, "Sheet 3 PC"),
                                ("Brand Search Keywords", 9, MO, "Sheet 3 MO")):
    n = count_rows(sheet, base, first)
    imps = [val(sheet, first + i, base + 3) for i in range(n)]
    check(f"{lab} sorted", all(imps[i] >= imps[i + 1] for i in range(n - 1)), f"{n} rows, top={imps[:3]}")
for g, br in zip(GROUPS, band_rows):
    for base, dev in ((PC, "PC"), (MO, "MO")):
        n = count_rows('Powerlink Keywords', base, br + 3)
        imps = [val('Powerlink Keywords', br + 3 + i, base + 3) for i in range(n)]
        check(f"{g:<12} {dev} sorted", all(imps[i] >= imps[i + 1] for i in range(n - 1)),
              f"{n} rows")

print()
print("=" * 100)
print("F. SPENT TIES OUT")
print("=" * 100)
bs_cost = disp('Brand Search Keywords', 8, PC + 2) + disp('Brand Search Keywords', 8, MO + 2)
check("Sheet 3 TOTAL Spent == Sheet 2 Subtotal Spent",
      abs(bs_cost - disp('Brand Search', 8, 6)) < 0.01,
      f"{bs_cost:,.2f} vs {disp('Brand Search',8,6):,.2f}")
pl_cost = sum(disp('Powerlink Keywords', br + 2, b + 2) for br in band_rows for b in (PC, MO))
check("Sheet 5 group Spent total ~= Sheet 4 Subtotal Spent",
      abs(pl_cost - disp('Powerlink', 8, 6)) < 1.0,
      f"{pl_cost:,.2f} vs {disp('Powerlink',8,6):,.2f}  (Naver rounding)")

print()
print("=" * 100)
print("G. POWERLINK BUDGET currency + formulas + merges")
print("=" * 100)
check("PL budget converted from its own currency",
      abs(disp('Powerlink', 8, 5) - S["plBudget"]["total"]) < 0.01,
      f"{disp('Powerlink',8,5):,.2f}")
bad_merge = 0
for n in wb["order"]:
    seen = set()
    for (r1, c1, r2, c2) in wb["sheets"][n]["merges"]:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) in seen:
                    bad_merge += 1
                seen.add((r, c))
check("no overlapping merges", bad_merge == 0, str(bad_merge))
bad, total_f = [], 0
for n, s in wb["sheets"].items():
    for r, c, kind, v, nf in [(x[0],x[1],x[2],x[3],x[4]) for x in s["cells"]]:
        if kind != 'f':
            continue
        total_f += 1
        try:
            raw_val(n, r, c)
        except Exception as ex:
            bad.append((n, r, c, v, repr(ex)))
check(f"all {total_f:,} formulas evaluate", not bad, f"{len(bad)} failed")
for x in bad[:5]:
    print("     ", x)

print()
print("=" * 100)
print("H. RENDERED — Sheet 3 top and Sheet 5 first group")
print("=" * 100)
for sheet, rows in (("Brand Search Keywords", range(1, 13)),
                    ("Powerlink Keywords", list(range(1, 8)) + list(range(band_rows[0], band_rows[0] + 5)))):
    print(f"--- {sheet} ---")
    for r in rows:
        out = []
        for c in range(1, 17):
            v = disp(sheet, r, c)
            out.append(f"{v:,.1f}" if isinstance(v, float) else str(v)[:11])
        if any(x.strip() for x in out):
            print(f"{r:>4}|" + "|".join(x[:11].ljust(11) for x in out))
    print()

print("=" * 100)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails[:6])}")
