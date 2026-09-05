"""Run the real index.html JS in V8 (py-mini-racer) with browser/ExcelJS stubs,
then dump the produced workbook cells to JSON for verification."""
import io, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
from py_mini_racer import MiniRacer

D = r"C:\Users\user\my_work\Creatip\performance\ALO\Evergreen_Weekly_Report"
SCRATCH = os.path.dirname(os.path.abspath(__file__))

html = io.open(os.path.join(D, "index.html"), encoding="utf-8").read()
scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
assert len(scripts) == 1, f"expected 1 inline script, found {len(scripts)}"
app_js = scripts[0]
print(f"inline script: {len(app_js):,} chars")

harness = io.open(os.path.join(SCRATCH, "harness.js"), encoding="utf-8").read()
daily_csv = io.open(os.path.join(D, "일별,2226795.csv"), encoding="utf-8-sig").read()
kw_csv    = io.open(os.path.join(D, "키워드,2226795.csv"), encoding="utf-8-sig").read()

ctx = MiniRacer()
ctx.eval(harness)
try:
    ctx.eval(app_js)
except Exception as e:
    print("!! SYNTAX/RUNTIME ERROR while loading app script:")
    print(e)
    sys.exit(1)
print("app script loaded OK (no syntax errors)")

ctx.eval("var DAILY_CSV = " + json.dumps(daily_csv))
ctx.eval("var KW_CSV = "    + json.dumps(kw_csv))

setup = r"""
var LOG = [];
function step(name, fn){ try { var r = fn(); LOG.push(['ok', name]); return r; }
                         catch(e){ LOG.push(['ERR', name + ' :: ' + e.message]); throw e; } }

var dRes = step('ingest daily',   function(){ return ingest(splitCsv(DAILY_CSV), 'daily',   'daily.csv'); });
var kRes = step('ingest keyword', function(){ return ingest(splitCsv(KW_CSV),    'keyword', 'kw.csv'); });

S.rawDaily   = dRes.rows;
S.rawKeyword = kRes.rows;
S.campaign = { client:'FIGS', name:'Always-on',
               start:'2026-07-07', end:'2026-08-20',   // deliberately past the raw data
               plCampaign:'Evergreen_PPC' };
S.advBudget  = { currency:'USD', amount:46000 };
S.budgetBS   = { currency:'KRW', amount:43230000 };
S.budgetPL   = { currency:'KRW', amount:21169400 };
S.bsFixedFee = { pc:5280000, mo:37950000 };
S.agencyFeeRate = 8;
S.fx = { fromCountry:'KR', fromCurrency:'KRW', toCountry:'US', toCurrency:'USD', rate:1400 };

step('autoMapAdGroups', function(){ autoMapAdGroups(); });
var M = step('buildModel', function(){ return buildModel(); });

var SUMMARY = {
  log: LOG,
  dailyRows: dRes.rows.length, kwRows: kRes.rows.length,
  badDevice: dRes.badDevice.concat(kRes.badDevice),
  adGroupMap: S.adGroupMap,
  detectedMonths: detectedMonths(),
  detectedAdGroups: detectedAdGroups(),
  bsDailyDays: M.bsDaily.length, plDailyDays: M.plDaily.length,
  bsKw: M.bsKeywords.length, plKw: M.plKeywords.length,
  unmappedGroups: M.unmappedGroups,
  unmappedKw: M.unmappedKw.size,
  missingFx: M.missingFx,
  budgetBS: M.budgetBS, budgetPL: M.budgetPL,
  budgetTotal: M.budgetTotal, agencyRate: M.agencyRate,
  fxLabel: fxLabel(), period: fmtPeriod(), reportCurrency: reportCurrency(),
  bsBudget: M.bsBudget, plBudget: M.plBudget,
  bsBlank: M.bsDaily.filter(function(d){return !d.PC && !d.MO;}).map(function(d){return d.date;}),
  bsPartial: M.bsDaily.filter(function(d){return (!d.PC)!==(!d.MO);}).map(function(d){return d.date;}),
  validationErrors: validate().errs,
  titles: reportTitles(),
  prefix: reportPrefix(),
  groupDays: (function(){ var o={}; for(var i=0;i<GROUPS.length;i++) o[GROUPS[i]] = M.plGroup[GROUPS[i]].length; return o; })(),
  bsSpendUsd: M.bsDaily.reduce(function(a,d){ return a+d.totalSpent; },0),
  plSpendUsd: M.plDaily.reduce(function(a,d){ return a+d.totalSpent; },0),
  bsImp: M.bsDaily.reduce(function(a,d){ return a+d.totalImp; },0),
  plImp: M.plDaily.reduce(function(a,d){ return a+d.totalImp; },0),
  bsClick: M.bsDaily.reduce(function(a,d){ return a+d.totalClick; },0),
  plClick: M.plDaily.reduce(function(a,d){ return a+d.totalClick; },0)
};
var WB_DUMP = null;
buildWorkbook(M).then(function(wb){ WB_DUMP = dumpWorkbook(wb); })
                .catch(function(e){ WB_DUMP = { error: e.message + ' | ' + (e.stack||'') }; });
JSON.stringify(SUMMARY);
"""
PRE  = "var SETUP_ERR=null;\ntry{\n"
POST = ("\n}catch(e){ SETUP_ERR={__err:e.message,__stack:String(e.stack).slice(0,400)}; }\n"
        "JSON.stringify(SETUP_ERR||SUMMARY);")
raw = ctx.eval(PRE + setup + POST)
summary = json.loads(raw)
if "__err" in summary:
    print("!! setup failed:", summary["__err"]); print(summary["__stack"]); sys.exit(1)
print("\n--- JS execution log ---")
for kind, name in summary["log"]:
    print(f"  [{kind}] {name}")

dump_json = ctx.eval("JSON.stringify(WB_DUMP)")
if dump_json in (None, "null"):
    dump_json = ctx.eval("JSON.stringify(WB_DUMP)")   # give microtasks another turn
assert dump_json and dump_json != "null", "buildWorkbook promise did not settle"

io.open(os.path.join(SCRATCH, "summary.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=1))
io.open(os.path.join(SCRATCH, "wb_dump.json"), "w", encoding="utf-8").write(dump_json)

wb = json.loads(dump_json)
if "error" in wb:
    print("\n!! buildWorkbook FAILED:", wb["error"])
    sys.exit(1)

print("\n--- model summary (from real JS) ---")
for k in ["dailyRows","kwRows","badDevice","detectedMonths","detectedAdGroups","adGroupMap",
          "bsDailyDays","plDailyDays","groupDays","bsKw","plKw","unmappedGroups","unmappedKw",
          "missingFx","validationErrors"]:
    print(f"  {k:18} = {summary[k]}")
print(f"  {'BS':18} imp={summary['bsImp']:,} click={summary['bsClick']:,} spend=${summary['bsSpendUsd']:,.2f}")
print(f"  {'PL':18} imp={summary['plImp']:,} click={summary['plClick']:,} spend=${summary['plSpendUsd']:,.2f}")
b, pl = summary['bsBudget'], summary['plBudget']
print(f"  {'BS Budget':18} PC={b['pc']:,.2f}  MO={b['mo']:,.2f}  total={b['total']:,.2f}")
print(f"  {'PL Budget':18} total={pl['total']:,.2f}")
print(f"  {'blank days (BS)':18} {len(summary['bsBlank'])}  {summary['bsBlank'][:2]} .. {summary['bsBlank'][-2:]}")
print(f"  {'one-device days':18} {len(summary['bsPartial'])}  {summary['bsPartial']}")

print("\n--- workbook sheets ---")
for n in wb["order"]:
    s = wb["sheets"][n]
    rows = max((c[0] for c in s["cells"]), default=0)
    cols = max((c[1] for c in s["cells"]), default=0)
    f = sum(1 for c in s["cells"] if c[2] == "f")
    print(f"  {n:24} cells={len(s['cells']):>6}  formulas={f:>6}  extent={rows}r x {cols}c  merges={len(s['merges'])}  views={s['views']}")
