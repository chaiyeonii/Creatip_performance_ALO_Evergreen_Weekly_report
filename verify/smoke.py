"""Direction-of-conversion tests + a UI smoke test (renders every panel against the DOM stub)."""
import io, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
from py_mini_racer import MiniRacer

D = r"C:\Users\user\my_work\Creatip\performance\ALO\Evergreen_Weekly_Report"
SC = os.path.dirname(os.path.abspath(__file__))

html = io.open(os.path.join(D, "index.html"), encoding="utf-8").read()
app = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)[0]
harness = io.open(os.path.join(SC, "harness.js"), encoding="utf-8").read()
daily = io.open(os.path.join(D, "일별,2226795.csv"), encoding="utf-8-sig").read()
kw = io.open(os.path.join(D, "키워드,2226795.csv"), encoding="utf-8-sig").read()

ctx = MiniRacer()
ctx.eval(harness)
ctx.eval(app)
ctx.eval("var DAILY_CSV = " + json.dumps(daily))
ctx.eval("var KW_CSV = " + json.dumps(kw))

fails = []


def check(label, ok, detail=""):
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        fails.append(label)


print("=" * 92)
print("A. EXCHANGE RATE DIRECTION — rate is entered as '1 To = rate From'")
print("=" * 92)
cases = [
    # from,   to,    rate, amount, in-currency, expected out, label
    ("KR", "US", 1400, 1400000, "KRW", 1000.0,  "1 USD = 1,400 KRW"),
    ("JP", "US", 150,   150000, "JPY", 1000.0,  "1 USD = 150 JPY"),
    ("US", "KR", 0.000714, None, None, None,    "1 KRW = 0.0007 USD"),
    ("KR", "KR", None,  500000, "KRW", 500000.0, "KRW (no conversion)"),
]
for frm, to, rate, amt, cur, want, want_label in cases:
    ctx.eval(f"""
      S.fx = {{ fromCountry:'{frm}', fromCurrency:currencyOf('{frm}'),
                toCountry:'{to}',   toCurrency:currencyOf('{to}'),
                rate:{ 'null' if rate is None else rate } }};
    """)
    label = ctx.eval("fxLabel()")
    check(f"{frm}->{to} label", label == want_label, f"{label!r}")
    if amt is not None:
        got = ctx.eval(f"convertAmount({amt}, '{cur}')")
        check(f"{frm}->{to} convert {amt:,} {cur}", abs(got - want) < 0.01, f"{got:,.2f} (want {want:,.2f})")
    rc = ctx.eval("reportCurrency()")
    check(f"{frm}->{to} report currency", rc == ctx.eval(f"currencyOf('{to}')"), rc)

print()
print("=" * 92)
print("B. MONEY NUMBER FORMAT follows the report currency")
print("=" * 92)
for to, want0 in [("US", '"$"#,##0'), ("KR", '"\u20a9"#,##0'), ("JP", '"\u00a5"#,##0')]:
    ctx.eval(f"S.fx.toCountry='{to}'; S.fx.toCurrency=currencyOf('{to}'); applyMoneyFormats();")
    got = ctx.eval("NF_USD0")
    check(f"To={to} money format", got == want0, repr(got))

print()
print("=" * 92)
print("C. UI SMOKE TEST — every panel renders without a runtime error")
print("=" * 92)
ctx.eval("""
  var dRes = ingest(splitCsv(DAILY_CSV),'daily','d.csv');
  var kRes = ingest(splitCsv(KW_CSV),'keyword','k.csv');
  S = blankState();
  S.rawDaily=dRes.rows; S.rawKeyword=kRes.rows;
  S.campaign={client:'OWALA',name:'JISOO',brandColor:'Red',start:'2026-07-07',end:'2026-08-06',
              through:'2026-08-06',plCampaign:'Evergreen_PPC'};
  S.advBudget={currency:'USD',amount:46000};
  S.budgetBS={currency:'KRW',amount:43230000};
  S.budgetPL={currency:'KRW',amount:21169400}; S.bsFixedFee={pc:5280000,mo:37950000};
  S.agencyFeeRate=8;
  S.fx={fromCountry:'KR',fromCurrency:'KRW',toCountry:'US',toCurrency:'USD',rate:1400};
  autoMapAdGroups();
""")
panels = ["renderFx", "renderCampaignInfo", "renderSetup", "renderTitlePreview",
          "renderAdGroups", "renderKeywordMap", "renderStatus", "refreshValidation", "renderAll"]
for fn in panels:
    try:
        ctx.eval(f"{fn}()")
        check(fn, True)
    except Exception as e:
        check(fn, False, str(e).split("\n")[0][:110])

errs = json.loads(ctx.eval("JSON.stringify(validate().errs)"))
check("validate() clean with a full form", not errs, str(errs))

ctx.eval("S.campaign.client=''; S.advBudget.amount=null; S.fx.rate=null;")
errs2 = json.loads(ctx.eval("JSON.stringify(validate().errs)"))
need = ["Client", "Advertising Budget", "Exchange Rate"]
check("validate() flags every missing field",
      all(any(n in e for e in errs2) for n in need), " / ".join(errs2))

print()
print("=" * 92)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED -> ' + '; '.join(fails)}")
sys.exit(1 if fails else 0)
