import io, json, os
SCRATCH = os.path.dirname(os.path.abspath(__file__))
wb = json.loads(io.open(os.path.join(SCRATCH, "wb_dump.json"), encoding="utf-8").read())

print("=" * 92)
print("MERGE OVERLAP CHECK  (overlapping merges make ExcelJS throw on save)")
print("=" * 92)
bad = 0
for name in wb["order"]:
    seen = {}
    for (r1, c1, r2, c2) in wb["sheets"][name]["merges"]:
        if r1 == r2 and c1 == c2:
            print(f"  {name}: degenerate 1x1 merge at ({r1},{c1})"); bad += 1
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) in seen:
                    print(f"  {name}: OVERLAP at ({r},{c}) between {seen[(r,c)]} and {(r1,c1,r2,c2)}"); bad += 1
                seen[(r, c)] = (r1, c1, r2, c2)
    # a value written to a merge slave is silently lost by Excel
    cells = {(r, c): (k, v) for r, c, k, v, nf in wb["sheets"][name]["cells"]}
    for (r1, c1, r2, c2) in wb["sheets"][name]["merges"]:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if (r, c) == (r1, c1):
                    continue
                e = cells.get((r, c))
                if e and e[1] not in (None, ''):
                    print(f"  {name}: value on merge slave ({r},{c}) = {e[1]!r} -> would be lost"); bad += 1
print(f"  result: {'PASS - no problems' if bad == 0 else str(bad) + ' problem(s)'}")


def dump(name, r0, r1, cmax=13, w=13):
    s = wb["sheets"][name]
    cells = {}
    for r, c, k, v, nf in s["cells"]:
        cells[(r, c)] = ("=" + str(v)) if k == "f" else v
    merges = {(m[0], m[1]): m for m in s["merges"]}
    print(f"\n--- {name}  rows {r0}..{r1} ---")
    for r in range(r0, r1 + 1):
        out = []
        for c in range(1, cmax + 1):
            v = cells.get((r, c), "")
            if isinstance(v, float):
                v = f"{v:,.2f}"
            v = str(v)
            out.append(v[: w - 1].ljust(w - 1))
        mark = " <merge>" if any(m[0] == r for m in s["merges"]) else ""
        print(f"{r:>4}|" + "|".join(out) + mark)


dump("Brand Search", 1, 12)
dump("Brand Search", 39, 41)
dump("Powerlink", 41, 50)
dump("Powerlink", 186, 189)
dump("Powerlink Keywords", 1, 10, cmax=10, w=17)
dump("Powerlink Keywords", 160, 172, cmax=10, w=17)
dump("Overall", 1, 18, cmax=4, w=22)
