/* Harness: stubs the browser + ExcelJS so the real index.html logic can run in V8. */

var __captured = {};
var window = { addEventListener: function () {} };
var document = {
  getElementById: function () {
    return {
      innerHTML: '', textContent: '', value: '', className: '', dataset: {},
      classList: { toggle: function () {}, add: function () {}, remove: function () {} },
      addEventListener: function () {}, querySelectorAll: function () { return []; },
      querySelector: function () { return null; }, click: function () {},
      files: [], parentElement: null, disabled: false
    };
  },
  createElement: function () { return { click: function () {}, style: {} }; }
};
var localStorage = {
  _d: {},
  getItem: function (k) { return this._d[k] === undefined ? null : this._d[k]; },
  setItem: function (k, v) { this._d[k] = v; },
  removeItem: function (k) { delete this._d[k]; }
};
function Blob(parts) { this.size = (parts && parts[0] && parts[0].length) || 0; }
var URL = { createObjectURL: function () { return 'blob:x'; }, revokeObjectURL: function () {} };
function FileReader() {}
var XLSX = { read: function () { throw new Error('xlsx not stubbed'); }, utils: {} };
function confirm() { return true; }
function setTimeout(f) { return 0; }

/* ---- ExcelJS recorder ---- */
var ExcelJS = {
  Workbook: function () {
    var wb = this;
    wb.sheetNames = [];
    wb.sheets = {};
    wb.addWorksheet = function (name) {
      var ws = {
        name: name, _cells: {}, _merges: [], _rows: {}, _cols: {}, views: null,
        getCell: function (r, c) {
          var k = r + ',' + c;
          if (!ws._cells[k]) ws._cells[k] = { row: r, col: c, value: null, numFmt: null, font: null, fill: null, border: null, alignment: null };
          return ws._cells[k];
        },
        mergeCells: function (r1, c1, r2, c2) { ws._merges.push([r1, c1, r2, c2]); },
        getRow: function (r) { if (!ws._rows[r]) ws._rows[r] = {}; return ws._rows[r]; },
        getColumn: function (c) { if (!ws._cols[c]) ws._cols[c] = {}; return ws._cols[c]; }
      };
      wb.sheetNames.push(name);
      wb.sheets[name] = ws;
      return ws;
    };
  }
};

function dumpWorkbook(wb) {
  var out = { order: wb.sheetNames, sheets: {} };
  for (var i = 0; i < wb.sheetNames.length; i++) {
    var n = wb.sheetNames[i], ws = wb.sheets[n], cells = [];
    for (var k in ws._cells) {
      var c = ws._cells[k];
      if (c.value === null && !c.numFmt) continue;
      var v = c.value, kind = 'v';
      if (v && typeof v === 'object' && v.formula !== undefined) { v = v.formula; kind = 'f'; }
      cells.push([c.row, c.col, kind, v, c.numFmt]);
    }
    var cols={}; for(var c in ws._cols) if(ws._cols[c].width) cols[c]=ws._cols[c].width;
    out.sheets[n] = { cells: cells, merges: ws._merges, views: ws.views, cols: cols };
  }
  return out;
}
