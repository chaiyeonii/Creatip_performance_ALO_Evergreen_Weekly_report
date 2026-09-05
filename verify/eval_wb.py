"""Evaluate the formulas in the dumped workbook to confirm the Excel output is numerically correct."""
import io, json, os, re, sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
wb = json.loads(io.open(os.path.join(SCRATCH, "wb_dump.json"), encoding="utf-8").read())

grid = {}   # (sheet, row, col) -> ('v'|'f', value)
for name, s in wb["sheets"].items():
    for r, c, kind, val, nf in s["cells"]:
        grid[(name, r, c)] = (kind, val)


def col_num(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n


TOK = re.compile(r"""
    (?P<sheet>'[^']+'!|[A-Za-z_][A-Za-z0-9_]*!)
  | (?P<func>[A-Z]+(?=\())
  | (?P<ref>\$?[A-Z]{1,3}\$?\d+)
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<str>"[^"]*")
  | (?P<op>[-+*/(),:=<>])
""", re.X)

_stack = set()


class Ev:
    def __init__(self, sheet, text):
        self.sheet = sheet
        self.toks = []
        i = 0
        while i < len(text):
            if text[i] == ' ':
                i += 1; continue
            m = TOK.match(text, i)
            if not m:
                raise ValueError(f"cannot tokenize at {text[i:][:20]!r} in {text!r}")
            self.toks.append((m.lastgroup, m.group()))
            i = m.end()
        self.p = 0

    def peek(self): return self.toks[self.p] if self.p < len(self.toks) else (None, None)
    def take(self):
        t = self.peek(); self.p += 1; return t

    def parse(self):
        v = self.expr()
        assert self.p == len(self.toks), f"trailing tokens {self.toks[self.p:]}"
        return v

    def expr(self):
        v = self.add()
        k, t = self.peek()
        if k == 'op' and t == '=':
            self.take()
            return v == self.add()
        return v

    def add(self):
        v = self.mul()
        while True:
            k, t = self.peek()
            if k == 'op' and t in '+-':
                self.take()
                r = self.mul()
                v = v + r if t == '+' else v - r
            else:
                return v

    def mul(self):
        v = self.unary()
        while True:
            k, t = self.peek()
            if k == 'op' and t in '*/':
                self.take()
                r = self.unary()
                if t == '*':
                    v = v * r
                else:
                    if r == 0:
                        raise ZeroDivisionError()
                    v = v / r
            else:
                return v

    def unary(self):
        k, t = self.peek()
        if k == 'op' and t == '-':
            self.take(); return -self.unary()
        return self.atom()

    def atom(self):
        k, t = self.take()
        if k == 'num':
            return float(t)
        if k == 'str':
            return t[1:-1]
        if k == 'op' and t == '(':
            v = self.expr()
            assert self.take()[1] == ')'
            return v
        if k == 'func':
            return self.call(t)
        if k == 'sheet':
            sheet = t[:-1].strip("'")
            k2, t2 = self.take()
            assert k2 == 'ref', f"expected ref after sheet, got {t2}"
            return cell_val(sheet, t2)
        if k == 'ref':
            k2, t2 = self.peek()
            if k2 == 'op' and t2 == ':':   # range outside SUM - not expected
                raise ValueError("bare range")
            return cell_val(self.sheet, t)
        raise ValueError(f"unexpected token {k}:{t}")

    def args(self):
        assert self.take()[1] == '('
        out = []
        if self.peek()[1] == ')':
            self.take(); return out
        while True:
            out.append(self.arg_raw())
            k, t = self.take()
            if t == ')': return out
            assert t == ',', f"expected , got {t}"

    def arg_raw(self):
        """Capture one argument, keeping ranges intact."""
        start = self.p
        depth = 0
        while self.p < len(self.toks):
            k, t = self.toks[self.p]
            if k == 'op' and t == '(': depth += 1
            elif k == 'op' and t == ')':
                if depth == 0: break
                depth -= 1
            elif k == 'op' and t == ',' and depth == 0: break
            self.p += 1
        return self.toks[start:self.p]

    def call(self, fn):
        raw = self.args()
        if fn == 'SUM':
            total = 0.0
            for a in raw:
                if len(a) == 3 and a[1][1] == ':':
                    total += sum_range(self.sheet, a[0][1], a[2][1])
                else:
                    total += sub_eval(self.sheet, a)
            return total
        if fn == 'IFERROR':
            try:
                return sub_eval(self.sheet, raw[0])
            except (ZeroDivisionError, ValueError, TypeError):
                return sub_eval(self.sheet, raw[1])
        if fn == 'IF':
            cond = sub_eval(self.sheet, raw[0])
            return sub_eval(self.sheet, raw[1] if cond else raw[2])
        if fn == 'ROUND':
            v = sub_eval(self.sheet, raw[0]); d = int(sub_eval(self.sheet, raw[1]))
            return round(v, d)
        raise ValueError(f"unsupported function {fn}")


def sub_eval(sheet, toks):
    e = Ev.__new__(Ev)
    e.sheet, e.toks, e.p = sheet, toks, 0
    return e.parse()


def sum_range(sheet, a, b):
    ma = re.match(r"\$?([A-Z]+)\$?(\d+)", a); mb = re.match(r"\$?([A-Z]+)\$?(\d+)", b)
    c1, r1 = col_num(ma.group(1)), int(ma.group(2))
    c2, r2 = col_num(mb.group(1)), int(mb.group(2))
    tot = 0.0
    for r in range(min(r1, r2), max(r1, r2) + 1):
        for c in range(min(c1, c2), max(c1, c2) + 1):
            v = raw_val(sheet, r, c)
            if isinstance(v, (int, float)): tot += v
    return tot


def raw_val(sheet, r, c):
    e = grid.get((sheet, r, c))
    if e is None: return 0.0
    kind, val = e
    if kind == 'v':
        return val if isinstance(val, (int, float)) else 0.0
    key = (sheet, r, c)
    if key in _stack: raise ValueError("circular")
    _stack.add(key)
    try:
        return Ev(sheet, val).parse()
    finally:
        _stack.discard(key)


def cell_val(sheet, ref):
    m = re.match(r"\$?([A-Z]+)\$?(\d+)", ref)
    return raw_val(sheet, int(m.group(2)), col_num(m.group(1)))


def disp(sheet, r, c):
    e = grid.get((sheet, r, c))
    if e is None: return ""
    kind, val = e
    if kind == 'v': return val
    try:
        return raw_val(sheet, r, c)
    except Exception as ex:
        return f"<ERR {ex}>"


# ---------------- report ----------------
def money(v): return f"${v:,.2f}" if isinstance(v, float) else v
def n(v):     return f"{v:,.0f}" if isinstance(v, float) else v

print("=" * 96)
print("SHEET 2 / 4  — Overview row (row 5)")
print("=" * 96)
hdr = ['Media', 'Period', 'Through', 'Budget', 'Spend', 'Imp', 'Click', 'CTR', 'CPC', 'CPM']
for sh in ['Brand Search', 'Powerlink']:
    vals = [disp(sh, 5, c) for c in range(1, 11)]
    print(f"  {sh}")
    for h, v in zip(hdr, vals):
        if isinstance(v, float):
            v = f"{v*100:.2f}%" if h == 'CTR' else (f"${v:,.2f}" if h in ('Budget', 'Spend', 'CPC', 'CPM') else f"{v:,.0f}")
        print(f"     {h:<8} {v}")

print("\n" + "=" * 96)
print("SHEET 1 — Overall")
print("=" * 96)
labels = {}
for (s, r, c), (k, v) in grid.items():
    if s == 'Overall' and c == 1 and k == 'v' and isinstance(v, str):
        labels[r] = v
for r in sorted(labels):
    if r < 9: continue
    lab = labels[r]
    row = [disp('Overall', r, c) for c in (2, 3, 4)]
    def f(v):
        if not isinstance(v, float): return str(v)
        if 'Rate' in lab or lab == 'CTR': return f"{v*100:.2f}%"
        if 'USD' in lab: return f"${v:,.2f}"
        return f"{v:,.0f}"
    print(f"  {lab:<16} BS={f(row[0]):>14}  PL={f(row[1]):>14}  TOTAL={f(row[2]):>14}")

print("\n" + "=" * 96)
print("SHEET 4 — Daily Breakdown by Keyword Group (group total rows) + integrity check")
print("=" * 96)
band = {}
for (s, r, c), (k, v) in grid.items():
    if s == 'Powerlink' and c == 1 and k == 'v' and v in ('Branded', 'Shoes', 'Competitors', 'Generic'):
        band[v] = r
tot_rows = sorted(r for (s, r, c), (k, v) in grid.items()
                  if s == 'Powerlink' and c == 1 and k == 'v' and v == 'Total')
print(f"  'Total' rows found on Powerlink: {tot_rows}")
for g in ('Branded', 'Shoes', 'Competitors', 'Generic'):
    br = band[g]
    tr = next(r for r in tot_rows if r > br)
    print(f"  {g:<12} band@{br:>3} total@{tr:>3}  "
          f"Imp={disp('Powerlink',tr,2):>12,.0f}  Click={disp('Powerlink',tr,3):>9,.0f}  "
          f"Cost={money(disp('Powerlink',tr,4)):>12}  CTR={disp('Powerlink',tr,5)*100:5.2f}%")
chk = [r for (s, r, c), (k, v) in grid.items()
       if s == 'Powerlink' and c == 1 and k == 'v' and isinstance(v, str) and v.startswith('Check')]
for r in chk:
    print(f"  CHECK row {r}: Imp={disp('Powerlink',r,2)}  Click={disp('Powerlink',r,3)}  Cost={disp('Powerlink',r,4)}")

print("\n" + "=" * 96)
print("SHEET 3 / 5 — keyword totals")
print("=" * 96)
for sh, lab in [('Brand Search Keywords', 'Total'), ('Powerlink Keywords', 'Grand Total')]:
    rows = [r for (s, r, c), (k, v) in grid.items() if s == sh and c == 1 and k == 'v' and v == lab]
    for r in rows:
        pc_i, pc_c = disp(sh, r, 3), disp(sh, r, 4)
        mo_i, mo_c = disp(sh, r, 8), disp(sh, r, 9)
        print(f"  {sh:<24} row {r:>3}  PC Imp={pc_i:>10,.0f} Click={pc_c:>9,.0f} | "
              f"MO Imp={mo_i:>10,.0f} Click={mo_c:>9,.0f} | SUM Imp={pc_i+mo_i:>10,.0f} Click={pc_c+mo_c:>9,.0f}")
    subs = [(r, grid[(sh, r, 1)][1]) for (s, r, c), (k, v) in grid.items()
            if s == sh and c == 1 and k == 'v' and isinstance(v, str) and v.endswith('Subtotal')]
    for r, v in sorted(subs):
        print(f"      {v:<22} PC Imp={disp(sh,r,3):>9,.0f} Click={disp(sh,r,4):>8,.0f} | "
              f"MO Imp={disp(sh,r,8):>9,.0f} Click={disp(sh,r,9):>8,.0f}")

# ---- scan every formula for evaluation errors ----
print("\n" + "=" * 96)
print("FORMULA SCAN")
print("=" * 96)
bad = []
total_f = 0
for name, s in wb["sheets"].items():
    for r, c, kind, val, nf in s["cells"]:
        if kind != 'f': continue
        total_f += 1
        try:
            raw_val(name, r, c)
        except Exception as ex:
            bad.append((name, r, c, val, repr(ex)))
print(f"  evaluated {total_f:,} formulas — {len(bad)} failed")
for b in bad[:15]:
    print("   ", b)
