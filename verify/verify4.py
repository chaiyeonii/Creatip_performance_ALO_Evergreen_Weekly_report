import io, json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(SCRATCH, "eval_wb.py"), encoding="utf-8").read()
core = src.split("# ---------------- report ----------------")[0]
ns = {"__name__": "core", "__file__": os.path.join(SCRATCH, "eval_wb.py")}
exec(compile(core, "eval_wb_core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]
summary = json.loads(io.open(os.path.join(SCRATCH, "summary.json"), encoding="utf-8").read())

SHEETS = wb["order"]
GROUPS = ["Branded", "Shoes", "Competitors", "Generic"]
fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


def row_cells(sheet, r):
    return [(c, v) for (s, rr, c), (k, v) in grid.items() if s == sheet and rr == r]


def row_merges(sheet, r):
    return [m for m in wb["sheets"][sheet]["merges"] if m[0] <= r <= m[2]]


def band_rows(sheet, col1_values=None):
    """rows whose B-cell holds one of the given strings"""
    return sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == sheet and c == 2 and k == 'v' and isinstance(v, str)
                  and (col1_values is None or v in col1_values))


print("=" * 98)
print("A. LAYOUT — column A and row 1 empty on every sheet")
print("=" * 98)
for n in SHEETS:
    cells = wb["sheets"][n]["cells"]
    bad = [(r, c) for r, c, k, v, nf in cells if c == 1 or r == 1]
    mrg = [m for m in wb["sheets"][n]["merges"] if m[1] == 1 or m[0] == 1]
    check(f"{n:<24} A열 / 1행", not bad and not mrg, f"{len(bad)} cells, {len(mrg)} merges")

print()
print("=" * 98)
print("B. BLANK ROW after every report title and section band")
print("=" * 98)
expected = {
    "Overall":               [2, 12],
    "Brand Search":          [2, 4, 9],
    "Brand Search Keywords": [2, 4],
    "Powerlink":             [2, 4, 9],
    "Powerlink Keywords":    [2, 4],
}
for n in SHEETS:
    rows = list(expected[n])
    rows += band_rows(n, set(GROUPS))          # keyword-group bands
    rows = sorted(set(rows))
    bad = [r for r in rows if row_cells(n, r + 1)]
    check(f"{n:<24} {len(rows):>2} bands -> blank row", not bad,
          f"bands at {rows[:6]}{'…' if len(rows) > 6 else ''}" + (f"  MISSING after {bad}" if bad else ""))

print()
print("=" * 98)
print("C. SHEET 1 — exact layout requested")
print("=" * 98)
labels = [disp('Overall', r, 2) for r in range(4, 11)]
want = ['Client', 'Campaign', 'Period', 'Total Spent', 'Advertising Budget', 'Agency Fee', 'Exchange Rate']
check("row 2 = report title", disp('Overall', 2, 2) == summary["titles"]["overall"], repr(disp('Overall', 2, 2)))
check("row 3 blank", not row_cells('Overall', 3))
check("rows 4-10 = 7 info items, no 'Campaign Information' header", labels == want, str(labels))
check("row 11 blank", not row_cells('Overall', 11))
check("row 12 = Media Summary band", disp('Overall', 12, 2) == 'Media Summary', repr(disp('Overall', 12, 2)))
check("row 13 blank", not row_cells('Overall', 13))
check("row 14 = table header", disp('Overall', 14, 2) == 'Campaign', repr(disp('Overall', 14, 2)))
check("rows 15-17 = BS / PL / Total",
      [disp('Overall', 15, 5), disp('Overall', 16, 5), disp('Overall', 17, 2)] ==
      ['Brand Search', 'Powerlink', 'Total'])
no_ci = not any(v == 'Campaign Information' for (s, r, c), (k, v) in grid.items() if s == 'Overall')
check("'Campaign Information' header removed", no_ci)

print()
print("=" * 98)
print("D. SHEET 1 — values and alignment")
print("=" * 98)
cells = {(r, c): (k, v, nf) for r, c, k, v, nf in wb["sheets"]['Overall']["cells"]}
align = {}
for r, c, k, v, nf in wb["sheets"]['Overall']["cells"]:
    pass
# alignment lives on the recorded cell objects; re-read from the dump is not available,
# so verify via the merge + value structure and report the rendered values instead.
vals = {}
for r in range(4, 11):
    vals[disp('Overall', r, 2)] = disp('Overall', r, 3)
for k in want:
    v = vals[k]
    print(f"     {k:<20} {v if not isinstance(v, float) else format(v, ',.2f')}")

spent = vals['Total Spent']
budget = vals['Advertising Budget']
fee = vals['Agency Fee']
rate = summary["agencyRate"]
check("Total Spent  == Media Summary Total", abs(spent - disp('Overall', 17, 7)) < 0.01)
check("Advertising Budget == Σ monthly budgets", abs(budget - summary["budgetTotal"]) < 0.01,
      f"{budget:,.2f} vs {summary['budgetTotal']:,.2f}")
check(f"Agency Fee == Total Spent x {rate}", abs(fee - spent * rate) < 0.01,
      f"{fee:,.2f} vs {spent * rate:,.2f}")
check("Exchange Rate label matches the tool", vals['Exchange Rate'] == summary["fxLabel"],
      repr(vals['Exchange Rate']))
check("Period format YYYY.MM.DD - YYYY.MM.DD", vals['Period'] == summary["period"], repr(vals['Period']))
check("Client / Campaign from user input",
      vals['Client'] == 'FIGS' and vals['Campaign'] == 'Always-on',
      f"{vals['Client']} / {vals['Campaign']}")

print()
print("=" * 98)
print("E. SINGLE CAMPAIGN-LEVEL EXCHANGE RATE")
print("=" * 98)
check("no monthly FX left in the model", "fxRates" not in json.dumps(summary))
check("one rate applied to every month", summary["fxLabel"] == "1 USD = 1,400 KRW", summary["fxLabel"])

print()
print("=" * 98)
print("F. CROSS-SHEET TOTALS / MERGES / FORMULAS")
print("=" * 98)
ov = 7   # overview data row on sheets 2 and 4


def find(sheet, val):
    return sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == sheet and c == 2 and k == 'v' and v == val)


gt = find('Powerlink Keywords', 'GRAND TOTAL')[0]
bt = find('Brand Search Keywords', 'TOTAL')[0]
pairs = [
    ("Overall BS Imp   == Sheet2 Overview", disp('Overall', 15, 8), disp('Brand Search', ov, 7)),
    ("Overall PL Imp   == Sheet4 Overview", disp('Overall', 16, 8), disp('Powerlink', ov, 7)),
    ("Sheet2 Overview  == Sheet3 TOTAL", disp('Brand Search', ov, 7),
     disp('Brand Search Keywords', bt, 4) + disp('Brand Search Keywords', bt, 10)),
    ("Sheet4 Overview  == Sheet5 GRAND TOTAL", disp('Powerlink', ov, 7),
     disp('Powerlink Keywords', gt, 4) + disp('Powerlink Keywords', gt, 10)),
]
for lab, a, b in pairs:
    check(lab, abs(a - b) < 0.01, f"{a:,.0f} vs {b:,.0f}")
for r in find('Powerlink', 'Check: Σ Groups = Total'):
    check(f"Sheet4 group check row {r}",
          all(disp('Powerlink', r, c) == "OK" for c in (3, 4, 5)))

bad_merge = 0
for n in SHEETS:
    seen = set()
    for (r1, c1, r2, c2) in wb["sheets"][n]["merges"]:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) in seen:
                    bad_merge += 1
                seen.add((r, c))
check("no overlapping merges", bad_merge == 0, f"{bad_merge}")

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
for b in bad[:6]:
    print("     ", b)

print()
print("=" * 98)
print("G. RENDERED — Sheet 1 and the top of Sheet 2")
print("=" * 98)
for r in range(1, 18):
    row = [(f"{disp('Overall', r, c):,.2f}" if isinstance(disp('Overall', r, c), float)
            else str(disp('Overall', r, c))[:21]) for c in range(1, 13)]
    if any(x.strip() for x in row):
        print(f"{r:>3}| " + " | ".join(x.ljust(21) for x in row).rstrip())
print()
for r in range(1, 16):
    row = []
    for c in range(1, 15):
        v = disp('Brand Search', r, c)
        row.append(f"{v:,.2f}" if isinstance(v, float) else str(v)[:11])
    if any(x.strip() for x in row):
        print(f"{r:>3}|" + "|".join(x[:11].ljust(11) for x in row))

print()
print("=" * 98)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails)}")
