import io, json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(SCRATCH, "eval_wb.py"), encoding="utf-8").read()
core = src.split("# ---------------- report ----------------")[0]
ns = {"__name__": "core", "__file__": os.path.join(SCRATCH, "eval_wb.py")}
exec(compile(core, "eval_wb_core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]
summary = json.loads(io.open(os.path.join(SCRATCH, "summary.json"), encoding="utf-8").read())

SHEETS = wb["order"]
fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


print("=" * 100)
print("A. LAYOUT OFFSET — column A and row 1 must be empty on every sheet")
print("=" * 100)
for n in SHEETS:
    cells = wb["sheets"][n]["cells"]
    col_a = [(r, c) for r, c, k, v, nf in cells if c == 1]
    row_1 = [(r, c) for r, c, k, v, nf in cells if r == 1]
    merges = wb["sheets"][n]["merges"]
    m_a = [m for m in merges if m[1] == 1]
    m_1 = [m for m in merges if m[0] == 1]
    check(f"{n:<24} col A empty", not col_a and not m_a, f"{len(col_a)} cells / {len(m_a)} merges")
    check(f"{n:<24} row 1 empty", not row_1 and not m_1, f"{len(row_1)} cells / {len(m_1)} merges")

print()
print("=" * 100)
print("B. REPORT TITLES — every sheet's title must sit in B2 and follow the naming rule")
print("=" * 100)
T = summary["titles"]
expect = {"Overall": T["overall"], "Brand Search": T["bs"], "Brand Search Keywords": T["bsk"],
          "Powerlink": T["pl"], "Powerlink Keywords": T["plk"]}
print(f"  prefix = {summary['prefix']!r}   (client + campaign from user input)")
for n in SHEETS:
    got = disp(n, 2, 2)
    check(f"{n:<24} B2", got == expect[n], repr(got))

print()
print("=" * 100)
print("C. KEYWORD SPACER — column G must be empty throughout the data area (rows 5+);")
print("   only the row-2 report title and row-4 subtitle bands span it, as rule 5 permits.")
print("=" * 100)
for n in ("Brand Search Keywords", "Powerlink Keywords"):
    used = [(r, v) for (s, r, c), (k, v) in grid.items() if s == n and c == 7 and r >= 5]
    crossing = [m for m in wb["sheets"][n]["merges"] if m[1] <= 7 <= m[3] and m[0] >= 5]
    check(f"{n:<24} spacer col G", not used and not crossing,
          f"{len(used)} cells / {len(crossing)} merges")

print()
print("=" * 100)
print("D. NUMBERS — cross-sheet consistency after the offset")
print("=" * 100)


def find_rows(sheet, col, pred):
    return sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == sheet and c == col and k == 'v' and isinstance(v, str) and pred(v))


ov = 6            # overview data row  (R0+4)
ms_tot = 17       # media summary total (R0+15)
gt = find_rows('Powerlink Keywords', 2, lambda v: v == 'GRAND TOTAL')[0]
bt = find_rows('Brand Search Keywords', 2, lambda v: v == 'TOTAL')[0]

pairs = [
    ("Overall Total Spent      == Media Summary Total", disp('Overall', 8, 3), disp('Overall', ms_tot, 7)),
    ("Overall Advertising Bgt  == Media Summary Total", disp('Overall', 9, 3), disp('Overall', ms_tot, 6)),
    ("Overall BS Impression    == Sheet2 Overview",     disp('Overall', 15, 8), disp('Brand Search', ov, 7)),
    ("Overall PL Impression    == Sheet4 Overview",     disp('Overall', 16, 8), disp('Powerlink', ov, 7)),
    ("Sheet2 Overview Imp      == Sheet3 TOTAL",        disp('Brand Search', ov, 7),
     disp('Brand Search Keywords', bt, 4) + disp('Brand Search Keywords', bt, 10)),
    ("Sheet4 Overview Imp      == Sheet5 GRAND TOTAL",  disp('Powerlink', ov, 7),
     disp('Powerlink Keywords', gt, 4) + disp('Powerlink Keywords', gt, 10)),
]
for lab, a, b in pairs:
    check(lab, abs(a - b) < 0.01, f"{a:,.2f} vs {b:,.2f}")

for r in find_rows('Powerlink', 2, lambda v: v.startswith('Check')):
    vals = [disp('Powerlink', r, c) for c in (3, 4, 5)]
    check(f"Sheet4 group check row {r}", all(v == "OK" for v in vals), str(vals))

print()
print("=" * 100)
print("E. MERGES + FORMULAS")
print("=" * 100)
bad_merge = 0
for n in SHEETS:
    seen = {}
    for (r1, c1, r2, c2) in wb["sheets"][n]["merges"]:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) in seen:
                    bad_merge += 1
                seen[(r, c)] = 1
check("no overlapping merges", bad_merge == 0, f"{bad_merge} overlaps")

bad, total_f = [], 0
for n, s in wb["sheets"].items():
    for r, c, kind, val, nf in s["cells"]:
        if kind != 'f':
            continue
        total_f += 1
        try:
            raw_val(n, r, c)
        except Exception as ex:
            bad.append((n, r, c, val, repr(ex)))
check(f"all {total_f:,} formulas evaluate", not bad, f"{len(bad)} failed")
for b in bad[:8]:
    print("     ", b)

print()
print("=" * 100)
print("F. SHEET 1 — Overall, as rendered")
print("=" * 100)
for r in range(1, 18):
    row = [str(disp('Overall', r, c))[:19] if not isinstance(disp('Overall', r, c), float)
           else f"{disp('Overall', r, c):,.2f}"[:19] for c in range(1, 13)]
    if any(x.strip() for x in row):
        print(f"{r:>3}| " + " | ".join(x.ljust(19) for x in row).rstrip())

print()
print("=" * 100)
print("G. SHEET 2 — Brand Search, top of the sheet")
print("=" * 100)
for r in range(1, 14):
    row = []
    for c in range(1, 15):
        v = disp('Brand Search', r, c)
        row.append(f"{v:,.2f}" if isinstance(v, float) else str(v)[:11])
    if any(x.strip() for x in row):
        print(f"{r:>3}|" + "|".join(x[:11].ljust(11) for x in row))

print()
print("=" * 100)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails)}")
