import io, json, os, importlib.util, sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ev", os.path.join(SCRATCH, "eval_wb_core.py"))

# reuse the evaluator from eval_wb.py by importing its top half
src = io.open(os.path.join(SCRATCH, "eval_wb.py"), encoding="utf-8").read()
core = src.split("# ---------------- report ----------------")[0]
ns = {"__name__": "core", "__file__": os.path.join(SCRATCH, "eval_wb.py")}
exec(compile(core, "eval_wb_core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]


def cells_of(sheet, col, pred):
    return sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == sheet and c == col and k == 'v' and isinstance(v, str) and pred(v))


print("=" * 100)
print("SHEET 1 — Overall")
print("=" * 100)
for r in range(1, 17):
    row = []
    for c in range(1, 12):
        v = disp('Overall', r, c)
        if isinstance(v, float):
            v = f"{v:,.2f}"
        row.append(str(v)[:20])
    if any(row):
        print(f"{r:>3}| " + " | ".join(x.ljust(20) for x in row).rstrip())

print("\n" + "=" * 100)
print("SHEET 2 — Brand Search  (header + TOTAL row + first dates)")
print("=" * 100)
for r in list(range(1, 13)) + [40, 41]:
    row = []
    for c in range(1, 14):
        v = disp('Brand Search', r, c)
        if isinstance(v, float):
            v = f"{v:,.2f}"
        row.append(str(v)[:12])
    if any(row):
        print(f"{r:>3}|" + "|".join(x.ljust(12) for x in row))

print("\n" + "=" * 100)
print("SHEET 3 — Brand Search Keywords  (spacer column check)")
print("=" * 100)
for r in list(range(1, 9)) + [63, 64]:
    row = []
    for c in range(1, 12):
        v = disp('Brand Search Keywords', r, c)
        if isinstance(v, float):
            v = f"{v:,.2f}"
        row.append(str(v)[:16])
    if any(row):
        print(f"{r:>3}|" + "|".join(x.ljust(16) for x in row))

spacer_used = [(s, r) for (s, r, c), (k, v) in grid.items()
               if c == 6 and s.endswith('Keywords') and (v not in (None, '') or k == 'f')]
merges_over_spacer = []
for name in ('Brand Search Keywords', 'Powerlink Keywords'):
    for (r1, c1, r2, c2) in wb["sheets"][name]["merges"]:
        if c1 <= 6 <= c2 and r1 > 3:
            merges_over_spacer.append((name, r1, c1, c2))
print(f"\n  spacer column (col 6) content cells: {len(spacer_used)} -> {spacer_used[:5]}")
print(f"  merges crossing spacer below row 3: {len(merges_over_spacer)} -> {merges_over_spacer[:5]}")

print("\n" + "=" * 100)
print("SHEET 4 — group TOTAL rows + integrity check")
print("=" * 100)
bands = {v: r for (s, r, c), (k, v) in grid.items()
         if s == 'Powerlink' and c == 1 and k == 'v' and v in ('Branded', 'Shoes', 'Competitors', 'Generic')}
tots = cells_of('Powerlink', 1, lambda v: v == 'TOTAL')
print(f"  TOTAL rows on Powerlink: {tots}")
for g in ('Branded', 'Shoes', 'Competitors', 'Generic'):
    br = bands[g]
    tr = next(r for r in tots if r > br)
    print(f"  {g:<12} band@{br:>3} TOTAL@{tr:>3}  Imp={disp('Powerlink',tr,2):>12,.0f}  "
          f"Click={disp('Powerlink',tr,3):>9,.0f}  Cost=${disp('Powerlink',tr,4):>11,.2f}  "
          f"CTR={disp('Powerlink',tr,5)*100:5.2f}%")
for r in cells_of('Powerlink', 1, lambda v: v.startswith('Check')):
    print(f"  CHECK row {r}: Imp={disp('Powerlink',r,2)} Click={disp('Powerlink',r,3)} Cost={disp('Powerlink',r,4)}")

print("\n" + "=" * 100)
print("SHEET 5 — subtotals & grand total")
print("=" * 100)
for r in cells_of('Powerlink Keywords', 1, lambda v: 'Subtotal' in v or v == 'GRAND TOTAL'):
    lab = grid[('Powerlink Keywords', r, 1)][1]
    pi, pc = disp('Powerlink Keywords', r, 3), disp('Powerlink Keywords', r, 4)
    mi, mc = disp('Powerlink Keywords', r, 9), disp('Powerlink Keywords', r, 10)
    print(f"  row {r:>3} {lab:<20} PC Imp={pi:>10,.0f} Click={pc:>8,.0f} | "
          f"MO Imp={mi:>10,.0f} Click={mc:>8,.0f} | Σ Imp={pi+mi:>10,.0f} Click={pc+mc:>8,.0f}")
r = cells_of('Brand Search Keywords', 1, lambda v: v == 'TOTAL')[0]
pi, pc = disp('Brand Search Keywords', r, 3), disp('Brand Search Keywords', r, 4)
mi, mc = disp('Brand Search Keywords', r, 9), disp('Brand Search Keywords', r, 10)
print(f"  BSK row {r:>3} TOTAL              PC Imp={pi:>10,.0f} Click={pc:>8,.0f} | "
      f"MO Imp={mi:>10,.0f} Click={mc:>8,.0f} | Σ Imp={pi+mi:>10,.0f} Click={pc+mc:>8,.0f}")

print("\n" + "=" * 100)
print("CROSS-SHEET CONSISTENCY")
print("=" * 100)
checks = [
    ("Overall Total Spent  == Media Summary Total",  disp('Overall', 7, 2),  disp('Overall', 16, 6)),
    ("Overall Adv Budget   == Media Summary Total",  disp('Overall', 8, 2),  disp('Overall', 16, 5)),
    ("Overall BS Imp       == Sheet2 Overview Imp",  disp('Overall', 14, 7), disp('Brand Search', 5, 6)),
    ("Overall PL Imp       == Sheet4 Overview Imp",  disp('Overall', 15, 7), disp('Powerlink', 5, 6)),
    ("Sheet4 Overview Imp  == Sheet5 GrandTotal",    disp('Powerlink', 5, 6),
     disp('Powerlink Keywords', cells_of('Powerlink Keywords', 1, lambda v: v == 'GRAND TOTAL')[0], 3)
     + disp('Powerlink Keywords', cells_of('Powerlink Keywords', 1, lambda v: v == 'GRAND TOTAL')[0], 9)),
    ("Sheet2 Overview Imp  == Sheet3 TOTAL",         disp('Brand Search', 5, 6), pi + mi),
]
for lab, a, b in checks:
    ok = abs(a - b) < 0.01
    print(f"  [{'OK ' if ok else 'FAIL'}] {lab:<44} {a:>14,.2f}  vs {b:>14,.2f}")

print("\n" + "=" * 100)
bad, total_f = [], 0
for name, s in wb["sheets"].items():
    for r, c, kind, val, nf in s["cells"]:
        if kind != 'f':
            continue
        total_f += 1
        try:
            raw_val(name, r, c)
        except Exception as ex:
            bad.append((name, r, c, val, repr(ex)))
print(f"FORMULA SCAN: evaluated {total_f:,} formulas — {len(bad)} failed")
for b in bad[:10]:
    print("   ", b)
