# verify — 브라우저 없이 툴을 검증하는 스크립트

`index.html`의 인라인 JS를 **실제로 실행**해서 생성되는 Excel의 셀 좌표·수식·수치를 검사한다.
이 PC에는 Node.js가 없으므로 Python에 얹은 V8(py-mini-racer)로 돌린다.

## 준비

```bash
pip install py-mini-racer
```

`일별*.csv` / `키워드*.csv` 원본을 상위 폴더(리포지토리 루트)에 두어야 한다.
클라이언트 데이터라 `.gitignore`로 제외되어 있으므로 네이버 검색광고에서 다시 받아 놓을 것.

## 실행 순서

```bash
cd verify

python expected.py       # 1. 정답지 — Python 독립 구현으로 기대 수치를 먼저 계산
python run_js.py         # 2. index.html의 JS를 V8에서 실행 → wb_dump.json / summary.json 생성
python verify5.py        # 3. 주 검증기 — 결측 vs 0, 전 기간 날짜, 지표 순서, Overview PC/MO/Subtotal,
                         #    틀 고정 없음, 열 너비, 교차합계, 수식 전량
python verify2.py        # (구버전 레이아웃용 리포트 — 참고용)
python smoke.py          # 4. 환율 방향(From/To)·통화 서식·UI 패널 렌더 스모크 테스트
python check_layout.py   # 5. 병합 셀 충돌 검사 + 레이아웃 시각 덤프
```

Windows에서 한글 출력이 깨지면 `PYTHONIOENCODING=utf-8`을 앞에 붙인다.

## 각 파일 역할

| 파일 | 역할 |
|---|---|
| `expected.py` | `index.html`과 **독립적으로** 같은 집계를 Python으로 재구현. 대조군(정답지) |
| `harness.js` | `window`·`document`·`localStorage`·`Blob` 스텁 + ExcelJS를 **호출 기록기**로 대체 |
| `run_js.py` | HTML에서 인라인 `<script>` 추출 → 스텁 위에서 실행 → 워크북 셀 전체를 JSON으로 덤프 |
| `eval_wb.py` | Excel 수식 평가기 (`SUM`/`IFERROR`/`IF`/`ROUND`, 시트 간 참조, 범위). `verify2.py`가 재사용 |
| `verify5.py` | **주 검증기** — Data Through 제거, 캠페인 전 기간 날짜, 결측일 빈 셀, 지표 순서, Overview 디바이스 분할, 틀 고정 없음, 열 너비 |
| `verify4.py` | 이전 라운드 — A열·1행 공백, 헤더 뒤 공백 행, B2 제목 규칙, Sheet 1 레이아웃·값(Agency Fee·Budget·환율), 교차합계, 수식 전량 |
| `verify3.py` | 이전 라운드 검증기 (참고용) |
| `verify2.py` | 시트별 값 덤프 (구버전 레이아웃 기준, 참고용) |
| `smoke.py` | 환율 방향 변환(`1 To = rate From`), To 통화별 Excel 서식, 모든 render 함수 무오류 실행, validate() 동작 |
| `check_layout.py` | 병합 셀 겹침(ExcelJS 저장 시 예외 원인) 검사, Spacer 열 오염 검사, 레이아웃 덤프 |

## 반드시 통과해야 하는 것

- 수식 전량 평가 시 **실패 0건** (`#DIV/0!` 방지 확인)
- **Σ 4개 광고그룹 = Powerlink 전체** (Imp / Click / Cost)
- **Keyword 시트 합계 = Overview 합계** (Brand Search·Powerlink 각각)
- **Overall = 하위 시트 참조값** (Total Spent / Budget / Imp)
- 병합 셀 충돌 **0건**
- Keyword 시트 Spacer 열(G)에 데이터 영역 내용물 **0개**
- Raw Data 없는 날짜의 지표 셀에 **값·수식이 없을 것** (성과 0과 구분)
- 전 시트 **틀 고정 없음**, 모든 사용 열에 너비 지정
- 모든 시트에서 **A열·1행 완전 공백**, 제목은 **B2**
- 제목·섹션 헤더 **다음 행이 반드시 공백**
- Sheet 1: `Agency Fee = Total Spent × Rate`, `Advertising Budget = Σ 월별 Budget`
- 시트 제목이 `[Client]_[Campaign] …` 규칙과 일치

`expected.py`의 환율·정액료·예산 상수와 `run_js.py`의 Client/Campaign 값은 테스트용이다.
`run_js.py`는 일부러 ALO가 아닌 값(`FIGS` / `Always-on`)을 넣어 브랜드 하드코딩이 남아 있지 않은지 함께 검증한다.
