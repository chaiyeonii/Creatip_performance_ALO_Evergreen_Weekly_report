# Reference implementation mirroring index.html buildModel(), to produce ground-truth numbers.
import csv, collections, io, os, math

D = r"C:\Users\user\my_work\Creatip\performance\ALO\Evergreen_Weekly_Report"

FX = {"2026-07": 1385.0, "2026-08": 1372.0}
FEE_PC, FEE_MO = 5_280_000, 37_950_000
BUDGET_BS, BUDGET_PL = 50_000_000, 30_000_000
PL_CAMPAIGN = "Evergreen_PPC"
START = "2026-07-07"


def rd(name):
    return list(csv.reader(io.open(os.path.join(D, name), encoding="utf-8-sig")))[2:]


def dev(v):
    return "PC" if v == "PC" else ("MO" if v in ("모바일", "Mobile", "MO") else "")


def dt(v):
    return v.strip().rstrip(".").replace(".", "-")


def media(v):
    return "BS" if "브랜드검색" in v or "신제품검색" in v else ("PL" if "파워링크" in v else "")


def group(ag):
    s = ag.split("_", 1)[-1].lower()
    if "compet" in s: return "Competitors"
    if "shoe"   in s: return "Shoes"
    if "brand"  in s: return "Branded"
    if "general" in s or "generic" in s: return "Generic"
    return ""


daily = rd("일별,2226795.csv")
kws   = rd("키워드,2226795.csv")

# ---------- Brand Search daily ----------
bs = collections.defaultdict(lambda: [0, 0, 0])   # (date,dev) -> imp, click, costKRW
for r in daily:
    if media(r[1]) != "BS": continue
    d = dev(r[3])
    if not d: continue
    a = bs[(dt(r[4]), d)]
    a[0] += int(r[5]); a[1] += int(r[6])

for device, fee in (("PC", FEE_PC), ("MO", FEE_MO)):
    days = sorted(k[0] for k in bs if k[1] == device)
    per = fee // len(days)
    for i, d in enumerate(days):
        bs[(d, device)][2] = fee - per * (len(days) - 1) if i == len(days) - 1 else per

# ---------- Powerlink daily ----------
pl  = collections.defaultdict(lambda: [0, 0, 0])
plg = collections.defaultdict(lambda: [0, 0, 0])
for r in daily:
    if media(r[1]) != "PL" or r[0] != PL_CAMPAIGN: continue
    d = dev(r[3])
    if not d: continue
    key = (dt(r[4]), d)
    a = pl[key];  a[0] += int(r[5]); a[1] += int(r[6]); a[2] += int(r[9])
    b = plg[(dt(r[4]), group(r[2]), d)]; b[0] += int(r[5]); b[1] += int(r[6]); b[2] += int(r[9])


def usd(krw, date):
    return krw / FX[date[:7]]


def totals(agg, filt=lambda k: True):
    imp = clk = 0; cost = 0.0
    for k, v in agg.items():
        if not filt(k): continue
        imp += v[0]; clk += v[1]; cost += usd(v[2], k[0])
    return imp, clk, cost


def line(lbl, imp, clk, cost, budget_krw=None):
    ctr = clk / imp if imp else 0
    cpc = cost / clk if clk else 0
    cpm = cost / imp * 1000 if imp else 0
    b = ""
    if budget_krw is not None:
        bu = budget_krw / FX[START[:7]]
        b = f"  Budget=${bu:,.0f}  SpendRate={cost/bu*100:6.2f}%"
    print(f"{lbl:<26} Imp={imp:>10,}  Click={clk:>8,}  Spend=${cost:>11,.2f}  "
          f"CTR={ctr*100:6.2f}%  CPC=${cpc:6.2f}  CPM=${cpm:7.2f}{b}")


print("=" * 132)
print(f"FX: {FX}   BS fee: PC {FEE_PC:,} / MO {FEE_MO:,}   Budget: BS {BUDGET_BS:,} / PL {BUDGET_PL:,} KRW")
print("=" * 132)

bi, bc, bs_cost = totals(bs)
pi, pc_, pl_cost = totals(pl)
line("Brand Search", bi, bc, bs_cost, BUDGET_BS)
line("Powerlink",    pi, pc_, pl_cost, BUDGET_PL)
line("TOTAL",        bi + pi, bc + pc_, bs_cost + pl_cost, BUDGET_BS + BUDGET_PL)

print("\n-- Brand Search by device (fixed-fee split) --")
for d in ("PC", "MO"):
    i, c, s = totals(bs, lambda k, d=d: k[1] == d)
    days = len({k[0] for k in bs if k[1] == d})
    print(f"  {d}: {days}일  Imp={i:>9,}  Click={c:>8,}  Spend=${s:>10,.2f}  (fee {FEE_PC if d=='PC' else FEE_MO:,} KRW)")

print("\n-- Powerlink by keyword group --")
gsum = [0, 0, 0.0]
for g in ("Branded", "Shoes", "Competitors", "Generic"):
    i, c, s = totals(plg, lambda k, g=g: k[1] == g)
    gsum[0] += i; gsum[1] += c; gsum[2] += s
    line("  " + g, i, c, s)
print(f"  {'Σ groups':<24} Imp={gsum[0]:>10,}  Click={gsum[1]:>8,}  Spend=${gsum[2]:>11,.2f}")
print(f"  match vs Powerlink total: imp={gsum[0]==pi}  click={gsum[1]==pc_}  spend={abs(gsum[2]-pl_cost)<0.005}")

# ---------- keywords ----------
print("\n-- Keyword counts (Imp>0 or Click>0) --")
kmap = {}
for row in list(csv.reader(io.open(os.path.join(D, "keyword_mapping.csv"), encoding="utf-8-sig")))[1:]:
    if row: kmap.setdefault(row[1].replace(" ", "").lower(), row[2])

for label, pred, withg in (("Brand Search", lambda r: media(r[0]) == "BS", False),
                           ("Powerlink",    lambda r: media(r[0]) == "PL" and r[1] == PL_CAMPAIGN, True)):
    agg = collections.defaultdict(lambda: [0, 0])
    for r in kws:
        if not pred(r): continue
        d = dev(r[4])
        if not d: continue
        k = (group(r[2]) if withg else "", d, r[3])
        a = agg[k]; a[0] += int(r[5]); a[1] += int(r[6])
    act = {k: v for k, v in agg.items() if v[0] > 0 or v[1] > 0}
    unm = [k[2] for k in act if k[2].replace(" ", "").lower() not in kmap]
    ti = sum(v[0] for v in act.values()); tc = sum(v[1] for v in act.values())
    print(f"  {label:<13} rows={len(act):>4}  PC={sum(1 for k in act if k[1]=='PC'):>4}  "
          f"MO={sum(1 for k in act if k[1]=='MO'):>4}  Imp={ti:>10,}  Click={tc:>8,}  unmapped={len(unm)}")
    if withg:
        for g in ("Branded", "Shoes", "Competitors", "Generic"):
            sub = {k: v for k, v in act.items() if k[0] == g}
            print(f"      {g:<12} PC={sum(1 for k in sub if k[1]=='PC'):>4}  MO={sum(1 for k in sub if k[1]=='MO'):>4}  "
                  f"Imp={sum(v[0] for v in sub.values()):>9,}  Click={sum(v[1] for v in sub.values()):>7,}")
    ref = (bi, bc) if label == "Brand Search" else (pi, pc_)
    print(f"      vs daily total: imp {'MATCH' if ti==ref[0] else f'DIFF {ti-ref[0]}'}, "
          f"click {'MATCH' if tc==ref[1] else f'DIFF {tc-ref[1]}'}")
