import io, json, os

SCRATCH = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(SCRATCH, "eval_wb.py"), encoding="utf-8").read()
core = src.split("# ---------------- report ----------------")[0]
ns = {"__name__": "core", "__file__": os.path.join(SCRATCH, "eval_wb.py")}
exec(compile(core, "eval_wb_core", "exec"), ns)
grid, disp, raw_val, wb = ns["grid"], ns["disp"], ns["raw_val"], ns["wb"]
S = json.loads(io.open(os.path.join(SCRATCH, "summary.json"), encoding="utf-8").read())

SHEETS = wb["order"]
fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


def rowcells(sheet, r):
    # only cells that actually carry a value or formula; a cell that has just a
    # number format and a border renders as empty in Excel
    return {c: v for (s, rr, c), (k, v) in grid.items()
            if s == sheet and rr == r and v is not None and v != ''}


def findrow(sheet, col, val):
    return sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == sheet and c == col and k == 'v' and v == val)


print("=" * 100)
print("A. DATA THROUGH DATE — removed everywhere")
print("=" * 100)
hits = [(s, r, c, v) for (s, r, c), (k, v) in grid.items()
        if isinstance(v, str) and "Through" in v]
check("no 'Data Through Date' cell in any sheet", not hits, str(hits[:3]))
check("model exposes no 'through'", "through" not in S, "")

print()
print("=" * 100)
print("B. DAILY BREAKDOWN — full campaign period, missing vs zero")
print("=" * 100)
DB_HDR = 11          # 2 title,3 blank,4 band,5 blank,6 hdr,7-9 overview,10 blank,11 band,12 blank,13-14 hdr
TOTAL_ROW = 13
FIRST = 14
for sheet in ("Brand Search", "Powerlink"):
    dates = []
    r = FIRST
    while True:
        v = disp(sheet, r, 2)
        if not isinstance(v, str) or not v[:4].isdigit():
            break
        dates.append((r, v))
        r += 1
    check(f"{sheet:<13} rows cover the campaign period", len(dates) == S["bsDailyDays"],
          f"{len(dates)} rows, {dates[0][1]} .. {dates[-1][1]}")

blanks = set(S["bsBlank"])
sheet = "Brand Search"
bad_blank, bad_zero = [], []
for r, d in [(rr, dd) for rr, dd in
             [(x, disp(sheet, x, 2)) for x in range(FIRST, FIRST + S["bsDailyDays"])]]:
    cells = rowcells(sheet, r)
    metric_cols = [c for c in cells if c >= 3]
    if d in blanks:
        if metric_cols:
            bad_blank.append((d, metric_cols))
    else:
        if not metric_cols:
            bad_zero.append(d)
check("days with no raw data: metric cells carry no value", not bad_blank, str(bad_blank[:3]))
check("days with raw data are populated", not bad_zero, str(bad_zero[:3]))

# the one day where PC is missing but MO is present
part = S["bsPartial"][0]
pr = next(r for r in range(FIRST, FIRST + S["bsDailyDays"]) if disp(sheet, r, 2) == part)
cells = rowcells(sheet, pr)
pc_cols = [c for c in (7, 8, 9, 10) if c in cells]
mo_cols = [c for c in (11, 12, 13, 14) if c in cells]
check(f"{part}: missing PC side carries no value", not pc_cols, f"PC cols present {pc_cols}")
check(f"{part}: present MO side filled", len(mo_cols) == 4, f"MO cols {mo_cols}")
check(f"{part}: Total equals MO alone",
      abs(disp(sheet, pr, 4) - disp(sheet, pr, 12)) < 0.01,
      f"{disp(sheet,pr,4):,.0f} vs {disp(sheet,pr,12):,.0f}")

print()
print("=" * 100)
print("C. METRIC ORDER — Spent | Impression | Click | CTR")
print("=" * 100)
want = ['Spent', 'Impression', 'Click', 'CTR']
for sheet in ("Brand Search", "Powerlink"):
    got = [disp(sheet, DB_HDR + 1, c) for c in range(3, 15)]
    check(f"{sheet:<13} sub-header", got == want * 3, str(got[:4]))
    grp = [disp(sheet, DB_HDR, c) for c in (3, 7, 11)]
    check(f"{sheet:<13} group header", all('_Total' in grp[0] and '_PC' in grp[1] and '_MO' in grp[2] for _ in [0]),
          str(grp))
# "Cost" is a legitimate column on the keyword sheets; it must not appear in a
# Daily Breakdown, where the metric is called Spent.
check("no 'Cost' label in any Daily Breakdown",
      not [1 for (s, r, c), (k, v) in grid.items()
           if v == 'Cost' and s in ('Brand Search', 'Powerlink')])

print()
print("=" * 100)
print("D. FREEZE PANES — none")
print("=" * 100)
for n in SHEETS:
    v = wb["sheets"][n]["views"] or [{}]
    # views now exist to switch gridlines off; what must be absent is a frozen pane
    check(f"{n:<24} no freeze", not any(x.get("state") == "frozen" for x in v), str(v))

print()
print("=" * 100)
print("E. OVERVIEW — Media | Ad | Device(PC/MO/Subtotal) + budgets")
print("=" * 100)
OV_HDR, R_PC, R_MO, R_SUB = 5, 6, 7, 8
hdr = [disp("Brand Search", OV_HDR, c) for c in range(2, 12)]
check("header", hdr == ['Media', 'Ad', 'Device', 'Budget', 'Spent', 'Impression', 'Click', 'CTR', 'CPC', 'CPM'],
      str(hdr))
for sheet, ad in (("Brand Search", "Brand Search"), ("Powerlink", "Powerlink")):
    check(f"{sheet:<13} Media / Ad merged", disp(sheet, R_PC, 2) == 'Naver SA' and disp(sheet, R_PC, 3) == ad)
    devs = [disp(sheet, r, 4) for r in (R_PC, R_MO, R_SUB)]
    check(f"{sheet:<13} device rows", devs == ['PC', 'MO', 'Subtotal'], str(devs))
    sub_i, pc_i, mo_i = disp(sheet, R_SUB, 7), disp(sheet, R_PC, 7), disp(sheet, R_MO, 7)
    check(f"{sheet:<13} Subtotal Imp = PC + MO", abs(sub_i - (pc_i + mo_i)) < 0.01,
          f"{sub_i:,.0f} vs {pc_i:,.0f}+{mo_i:,.0f}")
    ctr = disp(sheet, R_SUB, 9)
    check(f"{sheet:<13} Subtotal CTR recalculated", abs(ctr - disp(sheet, R_SUB, 8) / sub_i) < 1e-9,
          f"{ctr*100:.2f}%")

b = S["bsBudget"]
check("BS PC Budget = 정액료 PC", abs(disp("Brand Search", R_PC, 5) - b["pc"]) < 0.01,
      f"{disp('Brand Search',R_PC,5):,.2f} vs {b['pc']:,.2f}")
check("BS MO Budget = 정액료 MO", abs(disp("Brand Search", R_MO, 5) - b["mo"]) < 0.01)
check("BS Subtotal Budget = PC + MO", abs(disp("Brand Search", R_SUB, 5) - (b["pc"] + b["mo"])) < 0.01)
check("PL Subtotal Budget = Powerlink Budget",
      abs(disp("Powerlink", R_SUB, 5) - S["plBudget"]["total"]) < 0.01)

print()
print("=" * 100)
print("F. TOTAL ROW — sums only the days that have raw data")
print("=" * 100)
for sheet, key in (("Brand Search", "bs"), ("Powerlink", "pl")):
    tot_spent = disp(sheet, TOTAL_ROW, 3)
    tot_imp = disp(sheet, TOTAL_ROW, 4)
    check(f"{sheet:<13} TOTAL Spent", abs(tot_spent - S[key + "SpendUsd"]) < 0.01,
          f"{tot_spent:,.2f} vs {S[key+'SpendUsd']:,.2f}")
    check(f"{sheet:<13} TOTAL Impression", abs(tot_imp - S[key + "Imp"]) < 0.01,
          f"{tot_imp:,.0f} vs {S[key+'Imp']:,.0f}")

print()
print("=" * 100)
print("G. COLUMN WIDTHS — every used column sized, gutter narrow, spacer narrow")
print("=" * 100)
for n in SHEETS:
    cols = {int(k): v for k, v in wb["sheets"][n]["cols"].items()}
    used = sorted({c for (s, r, c) in grid if s == n and c > 1})
    missing = [c for c in used if c not in cols]
    check(f"{n:<24} all used columns have a width", not missing, str(missing))
    check(f"{n:<24} column A narrow", cols.get(1, 99) <= 3, str(cols.get(1)))
    if n.endswith("Keywords"):
        # keyword blocks are 7 columns wide, so the spacer sits at column I
        check(f"{n:<24} spacer col I narrow", cols.get(9, 99) <= 4, str(cols.get(9)))
    wide = {c: w for c, w in cols.items() if w > 30}
    check(f"{n:<24} no runaway column", not wide, str(wide))

print()
print("=" * 100)
print("H. CROSS-SHEET / MERGES / FORMULAS")
print("=" * 100)
# Keyword TOTAL rows now sit under each column header, not at the bottom.
# Sheet 3 has one TOTAL (row 8); Sheet 5 has one per ad group.
KW_PC, KW_MO = 2, 10          # first column of each device block
BT = 8                        # Sheet 3 TOTAL row
GROUPS4 = ["Branded", "Shoes", "Competitors", "Generic"]
grp_tot = sorted(r for (s_, r, c), (k, v) in grid.items()
                 if s_ == 'Powerlink Keywords' and c == KW_PC and k == 'v'
                 and isinstance(v, str) and v.endswith(' TOTAL'))
bs_kw_imp = disp('Brand Search Keywords', BT, KW_PC + 3) + disp('Brand Search Keywords', BT, KW_MO + 3)
pl_kw_imp = sum(disp('Powerlink Keywords', r, b + 3) for r in grp_tot for b in (KW_PC, KW_MO))
pairs = [
    ("Overall BS Imp  == Sheet2 Subtotal", disp('Overall', 14, 8), disp('Brand Search', R_SUB, 7)),
    ("Overall PL Imp  == Sheet4 Subtotal", disp('Overall', 15, 8), disp('Powerlink', R_SUB, 7)),
    ("Sheet2 Subtotal == Sheet3 TOTAL", disp('Brand Search', R_SUB, 7), bs_kw_imp),
    ("Sheet4 Subtotal == Sheet5 group TOTALs", disp('Powerlink', R_SUB, 7), pl_kw_imp),
    ("Overall Total Spent == Media Summary", disp('Overall', 7, 3), disp('Overall', 16, 7)),
    ("Overall Adv Budget  == input", disp('Overall', 8, 3), S["budgetTotal"]),
]
for lab, a, b2 in pairs:
    check(lab, abs(a - b2) < 0.01, f"{a:,.0f} vs {b2:,.0f}")
for r in findrow('Powerlink', 2, 'Check: Σ Groups = Total'):
    check(f"Sheet4 group check row {r}",
          all(disp('Powerlink', r, c) == "OK" for c in (3, 4, 5)),
          str([disp('Powerlink', r, c) for c in (3, 4, 5)]))

bad_merge = 0
for n in SHEETS:
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
    for r, c, kind, val, nf in [(x[0],x[1],x[2],x[3],x[4]) for x in s["cells"]]:
        if kind != 'f':
            continue
        total_f += 1
        try:
            raw_val(n, r, c)
        except Exception as ex:
            bad.append((n, r, c, val, repr(ex)))
check(f"all {total_f:,} formulas evaluate", not bad, f"{len(bad)} failed")
for x in bad[:6]:
    print("     ", x)

print()
print("=" * 100)
print("I. RENDERED — Sheet 2 top + the boundary between real and missing data")
print("=" * 100)
for r in list(range(1, 18)) + list(range(FIRST + 29, FIRST + 33)):
    row = []
    for c in range(1, 15):
        v = disp('Brand Search', r, c)
        row.append(f"{v:,.2f}" if isinstance(v, float) else str(v)[:12])
    if any(x.strip() for x in row):
        print(f"{r:>3}|" + "|".join(x[:12].ljust(12) for x in row))

print()
print("=" * 100)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails)}")
