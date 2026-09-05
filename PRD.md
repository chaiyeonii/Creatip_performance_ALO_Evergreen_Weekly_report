# PRD — Weekly Report Generator (네이버 검색광고)

| 항목 | 내용 |
|---|---|
| 제품명 | Weekly Report Generator |
| 목적 | 네이버 검색광고 Raw Data(CSV/XLSX)를 업로드하면 클라이언트 제출용 5-Sheet Excel 리포트를 자동 생성 |
| 적용 범위 | **특정 브랜드 전용이 아님.** Client / Campaign Name을 입력받아 어떤 광고주에게도 재사용 |
| 형태 | 단일 HTML 파일 (`index.html`) — 더블클릭으로 브라우저 실행, 서버·설치 불필요 |
| 라이브러리 | SheetJS(xlsx, 파싱) + ExcelJS(서식·수식 포함 xlsx 출력), CDN 로드 |
| 데이터 저장 | 브라우저 `localStorage` (서버 전송 없음) |
| 산출물 | `[Client]_[Campaign]_Weekly_Report_YYYYMMDD.xlsx` |

---

## 1. User Inputs

툴 UI는 아래 **4단계 순서**를 그대로 따른다. 모든 입력은 `localStorage`에 저장되어 다음 주차에 재사용된다.

### 단계 1 — Raw Data 업로드

네이버 검색광고 **일별 / 키워드** 리포트 2개를 올리면, `캠페인유형` 컬럼 기준으로
`Brand Search Daily` · `Brand Search Keyword` · `Powerlink Daily` · `Powerlink Keyword`
4종 데이터가 자동 분리된다. (§2 참조)

### 단계 2 — 캠페인 정보

| # | 입력 항목 | 형식 | 설명 |
|---|---|---|---|
| U1 | **Client** | text | **필수.** 모든 시트 제목과 Sheet 1 `Client` 값에 사용 (예: `ALO`, `FIGS`, `OWALA`) |
| U1b | **Brand Color** | dropdown | 12색 중 선택 (Black · Navy · Blue · Sky Blue · Green · Mint · Yellow · Orange · Red · Pink · Purple · Gray). 워크북 전체의 Main Key Color가 된다 |
| U2 | **Campaign Name** | text | **필수.** 시트 제목과 Sheet 1 `Campaign` 값에 사용 (예: `Evergreen`, `JISOO`, `Always-on`). Client명이 아니다 |
| U3 | **Advertising Budget** | Currency 드롭다운 + 금액 | **캠페인 전체 기간의 총 예산 1개.** 월별 입력 방식은 폐지. Sheet 1 정보표의 `Advertising Budget` 값 |
| U4 | **Agency Fee (%)** | % (number) | 퍼센트로 입력. Excel에는 `Total Spent × Rate` **수식**이 들어가고 계산된 **금액**이 표시된다 |

### 단계 3 — 캠페인 설정

| # | 입력 항목 | 형식 | 설명 |
|---|---|---|---|
| U5 | Campaign Start / End | date picker | 전체 Campaign Period. **리포트의 유일한 기간 기준**이며, Daily Breakdown의 날짜 행도 이 구간 전체를 생성한다 |
| U7 | **Brand Search Budget** | Currency 드롭다운 + 금액 | Sheet 1 Media Summary와 Sheet 2 Overview의 Budget |
| U8 | **Brand Search 정액료 · PC** | Raw Data 통화 (number) | 정액제 상품의 PC 금액. 통화 드롭다운 없이 Raw Data 통화 고정. **Overview의 PC Budget으로도 쓰인다** |
| U9 | **Brand Search 정액료 · MO** | Raw Data 통화 (number) | 〃 Mobile |
| U10 | **Powerlink Budget** | Currency 드롭다운 + 금액 | Brand Search Budget과 동일한 입력 방식. Sheet 1 Media Summary와 Sheet 4 Overview의 Budget |
| U11 | **Powerlink Campaign** | dropdown | 업로드된 Raw Data의 실제 캠페인 값에서 **자동 생성**. 선택한 캠페인의 데이터만 Powerlink 리포트에 포함 |

### 단계 4 — 환율

| # | 입력 항목 | 형식 | 설명 |
|---|---|---|---|
| U12 | **From — Country / Currency** | dropdown | Raw Data 광고비의 통화 (17개국) |
| U13 | **To — Country / Currency** | dropdown | 리포트 출력 통화. Excel의 통화 서식이 이 값을 따라간다 |
| U14 | **Exchange Rate** | number | **캠페인 전체에 단일 환율 1개.** 자동 조회 없음. `1 <To> = rate <From>` 방향으로 입력 |

### 그 밖의 설정 (단계 5~7)

| # | 입력 항목 | 설명 |
|---|---|---|
| U15 | Ad Group Mapping | Raw 광고그룹 → 4개 표준값. 자동 추론 + 수동 수정 |
| U16 | Keyword Mapping (KO→EN) | `keyword_mapping.csv`(315행) 내장. 편집·CSV 교체 가능 |

**입력 규칙**
- 환율은 **절대 자동 검색·추정하지 않는다.** 사용자가 직접 입력한다.
- Budget 통화 드롭다운은 **From / To 통화만** 제공한다. 단일 환율로 변환 가능한 조합만 허용하기 위함이다.
- Brand Search 정액료(PC/MO)만 Raw Data 통화(From)로 고정되며, 라벨에 통화 코드가 표시된다.
- Advertising Budget · Brand Search Budget · Powerlink Budget은 모두 `[Currency 드롭다운] [금액]` 형태로 통일한다.
- 필수 항목이 하나라도 비면 **생성 버튼이 비활성화**되고 어떤 값이 비었는지 표시된다.
- Client / Campaign Name을 입력하면 생성될 **5개 시트 제목이 실시간 미리보기**로 표시된다.

---

## 2. Raw Data Inputs

### 2.1 업로드 구성

업로드 영역은 **2개**. 네이버 검색광고에서 받은 파일을 그대로 드롭한다.

| 영역 | 파일 예시 | 포함 매체 |
|---|---|---|
| ① 일별 리포트 | `일별,2226795.csv` | 브랜드검색 + 파워링크 (`캠페인유형` 컬럼으로 자동 분리) |
| ② 키워드 리포트 | `키워드,2226795.csv` | 〃 |
| (선택) 키워드 매핑 | `keyword_mapping.csv` | 툴에 내장된 기본 매핑을 교체할 때만 업로드 |

> 하나의 파일에 두 매체가 함께 들어있으므로, **Brand Search / Powerlink 분리는 `캠페인유형` 컬럼 값으로 시스템이 자동 수행**한다. (요구사항의 4종 Raw Data는 이 2개 파일에서 파생된다)

### 2.2 파일 포맷 사양 (샘플 검증 완료)

- 인코딩: UTF-8 with BOM
- **1행 = 제목 행** (예: `"일별(2026.07.07.~2026.08.06.),2226795"`) → **무조건 스킵**
- **2행 = 헤더 행**
- 3행부터 데이터

### 2.3 내부 표준 컬럼

업로드된 파일은 아래 **내부 표준 스키마**로 변환된다. 실제 컬럼명이 달라도 매핑을 통해 흡수한다.

| 표준 컬럼 | 일별 리포트 | 키워드 리포트 | 비고 |
|---|---|---|---|
| `media` | `캠페인유형` | `캠페인유형` | 필수 |
| `campaign` | `캠페인` | `캠페인` | 필수 |
| `adGroup` | `광고그룹` | `광고그룹` | **필수** (Powerlink 그룹 분류에 사용) |
| `device` | `PC/모바일 매체` | `PC/모바일 매체` | 필수 |
| `date` | `일별` | — | 일별만 필수 |
| `keyword` | — | `키워드` | 키워드만 필수 |
| `impression` | `노출수` | `노출수` | 필수 |
| `click` | `클릭수` | `클릭수` | 필수 |
| `cost` | `총비용` | `총비용` | 일별만 사용 (KRW, VAT 제외) |
| (미사용) | `클릭률(%)`, `평균 CPC` | `클릭률(%)`, `평균 CPC`, `총비용` | **전부 무시하고 재계산** |

### 2.4 컬럼 매핑 & 정규화

- 컬럼은 **헤더명 기준 매핑**하되, 공백·괄호 차이를 허용하는 별칭 사전을 둔다.
- 별칭으로도 인식되지 않는 필수 컬럼이 있으면 → **컬럼 매핑 UI**를 띄워 사용자가 직접 지정하게 한다 (드롭다운으로 표준 컬럼 선택).
- 필수 컬럼 누락 시 → 어떤 컬럼이 없는지 명시한 에러를 표시하고 중단한다.
- 날짜: `YYYY.MM.DD.` / `YYYY-MM-DD` / `YYYY/MM/DD` → 내부 `YYYY-MM-DD`로 통일.
- 디바이스: `PC` → `PC`, `모바일`/`Mobile`/`MO` → `MO`. 그 외 값은 **미분류**로 집계에서 제외하고 경고를 표시.
- 숫자: 천단위 콤마·공백 제거 후 숫자 변환. 빈값은 0.

### 2.5 Ad Group 정규화 (Powerlink 전용)

Powerlink의 광고그룹은 아래 **4개 표준값**으로 정규화한다.

`Branded` / `Shoes` / `Competitors` / `Generic`

**자동 추론 규칙** — Raw 광고그룹명에서 디바이스 접두사(`PC_`, `MO_`)를 제거한 뒤 키워드 매칭:

| 포함 문자열 (대소문자 무시) | 표준값 |
|---|---|
| `Branded`, `Brand` | Branded |
| `Shoes`, `Shoe` | Shoes |
| `Competitor`, `Comp` | Competitors |
| `General`, `Generic` | Generic |

**샘플 데이터 검증 결과** — Evergreen_PPC의 광고그룹은 정확히 8개이며 전부 자동 추론된다.

| Raw 광고그룹 | 표준값 | Device | 키워드 수 | Imp | Click |
|---|---|---|---|---|---|
| `PC_Branded` | Branded | PC | 156 | 22,714 | 1,205 |
| `MO_Branded` | Branded | MO | 166 | 175,884 | 10,126 |
| `PC_Shoes` | Shoes | PC | 26 | 16,287 | 224 |
| `MO_Shoes` | Shoes | MO | 30 | 60,567 | 929 |
| `PC_Competitors` | Competitors | PC | 11 | 116,706 | 762 |
| `MO_Competitors` | Competitors | MO | 10 | 597,026 | 1,826 |
| `PC_General` | **Generic** | PC | 76 | 37,042 | 1,060 |
| `MO_General` | **Generic** | MO | 76 | 168,215 | 4,086 |

> Raw는 `General`, 리포트 표기는 `Generic`이다. 매핑으로 흡수한다.

**수동 매핑 UI**
- 업로드 후 감지된 Raw 광고그룹 목록과 추론된 표준값을 표로 보여주고, 드롭다운으로 수정 가능하게 한다.
- 추론 실패한 그룹은 `[미분류]`로 표시하고 **사용자가 지정할 때까지 생성을 차단**한다.
- 지정된 매핑은 `localStorage`에 저장되어 다음 주차에 자동 적용된다.
- **분류 기준은 Raw Data의 Ad Group이며**, `keyword_mapping.csv`의 Category는 참조하지 않는다. (샘플 검증 결과 두 값은 100% 일치했으나, 불일치 시 Ad Group이 우선)

---

## 3. Calculation Logic

### 3.1 처리 파이프라인

1. 파일 파싱 (1행 스킵, 2행 헤더)
2. 컬럼 매핑 → 날짜/디바이스/숫자 정규화
3. `캠페인유형`으로 Brand Search / Powerlink 분리, Powerlink는 `캠페인 = Evergreen_PPC` 필터
4. Powerlink 광고그룹 → 4개 표준값 정규화
5. Brand Search Spent 주입 (U5 정액료를 일별 배분)
6. (일자 × 디바이스) 집계 → Daily Breakdown
7. (일자 × 그룹 × 디바이스) 집계 → Daily Breakdown by Keyword Group
8. (그룹 × 디바이스 × 키워드) 집계 → Keyword Breakdown
9. 현지통화 → USD 변환 (캠페인 단일 환율)
10. 파생 지표 계산 (CTR / CPC / CPM)
11. Sheet 2~5 생성 → Sheet 1(Overall)은 하위 시트 셀을 수식으로 참조

### 3.2 환율 적용

- **캠페인 전체에 동일한 환율 1개**를 적용한다. 월별 환율은 사용하지 않는다.
- 환율은 `1 <To> = rate <From>` 방향으로 입력받는다. 따라서 변환식은 다음과 같다.
  ```
  값(To) = 값(From) / rate
  ```
  예: From `Korea / KRW`, To `United States / USD`, `1 USD = 1,400 KRW` → `USD = KRW / 1,400`
- From과 To가 같은 통화이면 변환 없이 그대로 사용한다 (Sheet 1 표기: `<Currency> (no conversion)`).
- 환율 미입력 시 → 생성 차단.
- Budget·정액료도 같은 환율로 변환한다. Budget 통화 드롭다운은 From/To 두 가지만 제공한다.
- **Excel의 통화 서식은 To 통화를 따른다.** (USD → `"$"#,##0`, KRW → `"₩"#,##0`, JPY → `"¥"#,##0` …)

### 3.3 Brand Search Spent 배분

브랜드검색은 정액제이므로 Raw Data의 `총비용`이 전 행 0원이다. U5의 **리포팅 기간 전체 정액료**를 다음 규칙으로 배분한다.

- **PC/MO 분배는 안분하지 않는다.** 사용자가 입력한 PC 금액·MO 금액을 그대로 각 디바이스에 귀속시킨다.
- **일별 배분**: 각 디바이스의 정액료를 **해당 디바이스에 데이터가 존재하는 일수로 균등 배분**한다.
  `일별 Spent(PC) = PC 정액료 / PC 데이터 존재 일수`
- 균등 배분의 반올림 잔액은 **마지막 일자에 몰아서 보정**하여 합계가 정액료와 정확히 일치하게 한다.
- Daily Breakdown의 `_Total` Spent = PC + MO (다른 열과 동일 규칙).
- Overview Spend는 배분값의 `SUM()`이므로 자동으로 정액료 합계와 일치한다.
- 리포팅 기간이 갱신되어 데이터 일수가 늘어나면 **일별 단가는 재계산된다.** 정액료 총액을 새 일수로 다시 나눈다.

### 3.4 파생 지표 (전 구간 공통)

```
CTR = Total Click / Total Impression
CPC = Total Spend / Total Click
CPM = Total Spend / Total Impression × 1000
```

- **일별/그룹별/키워드별 지표의 단순 평균은 절대 사용하지 않는다.** 항상 합계 기준으로 재계산한다.
- Raw Data의 `클릭률(%)`, `평균 CPC` 값은 **읽지 않는다.**
- 분모가 0이면 결과는 0. Excel에서는 `IFERROR(...,0)`으로 감싼다.
- 모든 `_Total` = `_PC + _MO` (행 단위), CTR은 Total 값 기준으로 재계산.

### 3.5 집계 기준 기간

- 기간 기준은 **Campaign Start ~ Campaign End 뿐**이다. `Data Through Date` 개념은 사용하지 않는다.
- Sheet 1 Overall, Sheet 2·4 Overview: 캠페인 기간 내 **Raw Data가 존재하는 구간**의 누적
- Sheet 2·4 Daily Breakdown: **Campaign Start부터 Campaign End까지 모든 날짜**를 오름차순으로 생성
- Sheet 3·5 Keywords: Reporting Period 전체 기간 합산, 동일 키워드 다중 행은 먼저 합산

**Missing Data와 Zero Performance 구분** — 두 상태는 반드시 다르게 표기한다.

| 상태 | 표기 |
|---|---|
| 해당 날짜·디바이스의 Raw Data 행이 **없음** | **빈 셀** (값·수식 없음. 테두리와 서식만 유지) |
| Raw Data 행은 있으나 성과가 **0** | `0` / `0.00%` 등 실제 값 |

- 한 날짜에서 PC만 없고 MO는 있으면 → PC 4칸은 빈 셀, MO는 값, Total은 **MO만 합산**한다.
- 양쪽 디바이스가 모두 없으면 → Total을 포함해 그 행의 모든 지표 셀이 빈 셀이다.
- **TOTAL 행은 빈 셀을 0으로 세지 않는다.** `SUM()`이 빈 셀을 자동으로 무시하므로 Raw Data가 존재하는 구간만 집계된다.

### 3.6 Keyword 시트 생성 규칙

**집계 키**
- Brand Search: `(Device, Keyword)`
- Powerlink: `(Ad Group, Device, Keyword)`

**포함 조건**
- **Imp > 0 또는 Click > 0 인 키워드만 노출.** 둘 다 0인 행은 제외한다. (상위 N개 제한 없이 전량 노출)

**정렬**
- Brand Search: 각 디바이스 블록 내에서 **Impression DESC**
- Powerlink: `Branded → Shoes → Competitors → Generic` 순으로 그룹 배치 후, **각 그룹 내부에서 Impression DESC**
- PC와 MO는 완전히 독립적으로 정렬한다.

**Keyword (EN) 매핑**
- `keyword_mapping.csv` (Category, Keyword KO, Keyword EN — 315행) 를 조회한다.
- 조회 키 정규화: **공백 제거 + 소문자 변환**. (`알로 지수` → `알로지수`, `ALO가디건` → `alo가디건` 매칭)
- 동일 KO 키가 여러 Category에 중복될 경우 **먼저 등장한 행을 사용**한다. EN 값이 서로 다르면 화면에 충돌 경고를 표시한다.
- 매핑에 없는 키워드 → `[UNMAPPED]`로 표기하고, 툴 화면에 미매핑 키워드 목록(Imp 내림차순)을 노출하여 추가 등록을 유도한다.
- Category 컬럼은 매핑 저장소에만 보관하며 **Excel에는 출력하지 않는다.**

**샘플 데이터 검증 결과 (2026.07.07~08.06)**

| 매체 | 고유 키워드 | Imp·Click > 0 | PC / MO | 미매핑 | 그룹 중복 |
|---|---|---|---|---|---|
| Powerlink (Evergreen_PPC) | 551 | 551 | 269 / 282 | **0** | **0** |
| Brand Search | 93 | 93 | 35 / 58 | **0** | — |

> 동일 키워드가 두 개 이상의 Ad Group에 걸친 사례는 0건이므로, 그룹 간 데이터 혼입 위험은 없다.

---

## 4. Sheet Structure

### 4.0 공통 규칙 — Report Naming & Layout Offset

**특정 브랜드명·캠페인명을 코드에 고정하지 않는다.** 모든 제목과 Campaign Information 값은 사용자가 입력한 Client / Campaign Name을 참조해 동적으로 생성한다.

**Report Title 규칙** — 각 시트 `B2`에 배치:

| Sheet | Title |
|---|---|
| 1. Overall | `[Client]_[Campaign Name] AD Summary` |
| 2. Brand Search | `[Client]_[Campaign Name] Brand Search Report` |
| 3. Brand Search Keywords | `[Client]_[Campaign Name] Brand Search Keyword Report` |
| 4. Powerlink | `[Client]_[Campaign Name] Powerlink Report` |
| 5. Powerlink Keywords | `[Client]_[Campaign Name] Powerlink Keyword Report` |

예시 — Client `ALO` / Campaign `Evergreen` → `ALO_Evergreen AD Summary`
Client `FIGS` / Campaign `Always-on` → `FIGS_Always-on AD Summary`

**Header 뒤 공백 행 규칙** — 전 시트 공통:

- **Report Title 다음에는 빈 행 1개**를 넣는다.
- **Section Header 바로 아래에는 빈 행을 넣지 않고 표 헤더가 바로 이어진다.** 대상: `Media Summary`(Sheet 1), `Overview`·`Daily Breakdown`(Sheet 2·4), Sheet 4의 Keyword Group 밴드(Branded/Shoes/Competitors/Generic), Sheet 5의 Ad Group 밴드.
- 빈 행은 **서로 다른 Section Block 사이**를 구분하는 용도로만 쓴다. 예: `Overview` → 표 → **빈 행** → `Daily Breakdown` → 표.
- 예외적으로 `Daily Breakdown by Keyword Group`과 Keyword 시트 부제는 그 아래에 또 다른 밴드가 오므로 빈 행을 유지한다.
- 표의 컬럼 헤더 아래에도 빈 행을 넣지 않는다. 컬럼 헤더 바로 아래에 TOTAL 행 또는 데이터가 이어진다.

**Layout Offset 규칙** — 전 시트 공통:

- **A열 = 완전 공백** (너비 2.4), **1행 = 완전 공백** (높이 9)
- 모든 Content Block은 **B2부터** 시작한다. 제목만 옮기는 것이 아니라 표·헤더·데이터 전체가 한 칸씩 이동한다.
- 제목은 필요 시 우측 여러 열에 걸쳐 병합할 수 있으나 **시작 위치는 항상 B2**.

**시트별 행 배치** (`R0 = 2`, `C0 = B`):

| 시트 | 행 배치 |
|---|---|
| 1 Overall | 2 제목 · 3 공백 · **4~10 기본 정보 7행** · 11 공백 · 12 `Media Summary` · 13 헤더 · 14~16 데이터 |
| 2 · 4 | 2 제목 · 3 공백 · 4 `Overview` · 5 헤더 · 6 PC · 7 MO · 8 Subtotal · 9 공백 · 10 `Daily Breakdown` · 11~12 2단 헤더 · 13 TOTAL · 14~ 일별 |
| 3 · 5 | 2 제목 · 3 공백 · 4 부제 · 5 공백 · 6~7 2단 헤더 · 8~ 데이터 |

Keyword 시트의 열 구성은 `B~F` (PC 5열) · **`G` (Spacer, 완전 공백)** · `H~L` (MO 5열) 이다.

### Sheet 1 — Overall (Summary Report)

정형화된 Excel Report Table 형태. 카드·대시보드형 레이아웃은 사용하지 않는다.

**영역 ① 기본 정보** — `Campaign Information` 섹션 헤더는 **두지 않는다.** 제목(B2) 아래 공백 행 하나를 두고 곧바로 정보표가 시작된다 (4~10행, 7개 항목).

| 항목 | 값 | 산출 |
|---|---|---|
| Client | *(사용자 입력값)* | User Input — 하드코딩 금지 |
| Campaign | *(사용자 입력값)* | User Input. **Client명이 아니라 Campaign Name** |
| Period | `2026.08.08 - 2026.09.06` | Campaign Period, `YYYY.MM.DD - YYYY.MM.DD` |
| Total Spent | USD | Media Summary Total 행의 Spent를 **수식 참조** (Brand Search + Powerlink 실제 Spend) |
| Advertising Budget | 리포트 통화 | **캠페인 전체 총 예산 1개** (단계 2에서 입력, 필요 시 환율로 변환) |
| Agency Fee | USD | **`= Total Spent 셀 × Agency Fee Rate`** 수식. 퍼센트가 아니라 계산된 금액을 표기 |
| Exchange Rate | `1 USD = 1,400 KRW` | `1 <To> = rate <From>` 형식. From=To이면 `<Currency> (no conversion)` |

- 라벨 셀과 값 셀 **모두 가로·세로 중앙 정렬**.
- 값 셀은 `C:E` 병합.

**영역 ② Media Summary** — 12행에 섹션 헤더, 13행 공백, 14행부터 표.

| Campaign | Period | Media | Ad | Budget | Spent | Impression | Click | CTR | CPC | CPM |
|---|---|---|---|---|---|---|---|---|---|---|

- 행 구성: `Brand Search` → `Powerlink` → `Total`
- **반복되는 Campaign / Period / Media 값은 두 매체 행에 걸쳐 세로 병합** (Media = `Naver`)
- Budget/Spent/Impression/Click은 Sheet 2·4의 Overview 셀을 **수식 참조**
- CTR/CPC/CPM은 각 행의 합계 기준 **재계산**
- Total 행: `Campaign~Ad` 4개 열을 가로 병합, 남색 배경 + 흰색 볼드

> **Budget 두 갈래에 대한 주의** — 영역 ①의 Advertising Budget은 *캠페인 총액* 1개 입력이고, 영역 ②의 Budget 열은 *매체별* 입력값(Brand Search / Powerlink)이다. 서로 다른 입력이므로 툴이 두 합계를 비교해 **차이가 있으면 경고**한다.

### Sheet 2 — Brand Search

**영역 ① Overview** — Device별 성과 요약. `PC → MO → Subtotal` 3행.

| Media | Ad | Device | Budget | Spent | Impression | Click | CTR | CPC | CPM |
|---|---|---|---|---|---|---|---|---|---|
| Naver SA | Brand Search | PC | | | | | | | |
| 〃 | 〃 | MO | | | | | | | |
| 〃 | 〃 | **Subtotal** | | | | | | | |

- `Media` / `Ad` 값은 3행에 걸쳐 **세로 병합**
- Spent·Impression·Click은 Daily Breakdown TOTAL 행의 해당 디바이스 블록을 **수식 참조**
- CTR·CPC·CPM은 각 행의 값 기준 **재계산**. Subtotal은 PC/MO 평균이 아니라 합계 기준으로 다시 계산한다
  - `CTR = Subtotal Click / Subtotal Impression`
  - `CPC = Subtotal Spent / Subtotal Click`
  - `CPM = Subtotal Spent / Subtotal Impression × 1,000`
- **Budget** — `PC Budget = 정액료 · PC`, `MO Budget = 정액료 · MO`, `Subtotal Budget = PC + MO` (수식). 환율로 리포트 통화 변환
- Subtotal 행은 볼드 + 배경색 + 상단 굵은 테두리로 강조
- Sheet 1 Media Summary는 이 **Subtotal 행**을 참조한다

> **Budget 불일치 처리** — 사용자가 입력한 `Brand Search Budget`과 `정액료 PC + MO`의 합이 다르면 값을 임의로 고치지 않고, 생성 전에 툴 화면에 **불일치 경고**를 표시한다. Overview는 정액료 기준을 사용한다.

**영역 ② Daily Breakdown** (2단 헤더)

| Date | Brand Search_Total | | | | Brand Search_PC | | | | Brand Search_MO | | | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | Spent | Impression | Click | CTR | Spent | Impression | Click | CTR | Spent | Impression | Click | CTR |

- **지표 순서는 `Spent → Impression → Click → CTR`.** `Cost`라는 표현은 사용하지 않는다
- 1행: `Date` / `_Total` / `_PC` / `_MO` (각 4열 병합)
- 2행: 지표명 반복
- **3행 = TOTAL 행** — 헤더 바로 아래. Raw Data가 존재하는 구간만 집계하며 CTR은 `Total Click / Total Impression`으로 재계산
- 4행부터 **Campaign Start ~ End 전체 날짜** (오름차순). Raw Data가 없는 날짜는 §3.5 규칙대로 빈 셀
- Total 열은 존재하는 디바이스만 더하는 수식, CTR은 `=IFERROR(Click/Impression,0)`
- Spent는 캠페인 단일 환율로 리포트 통화 변환

**Device Group 시각적 구분** — 빈 열을 삽입하지 않고 테두리·헤더 색으로 분리한다.

| 요소 | 규칙 |
|---|---|
| 세로 구분선 | `Date`, `Total`, `PC`, `MO` 각 블록의 좌우 경계에 **medium 두께 세로선** |
| 헤더 색 | Total `#1F3864` / PC `#2E5395` / MO `#4472C4` |
| 서브헤더 색 | 같은 계열 한 단계 밝은 톤 (`#35548C` / `#4A6FAE` / `#6A8FD4`) |
| 그룹 헤더 | 각 4열 병합, 독립된 Header Block으로 구성 |

**틀 고정** — **사용하지 않는다.** Date 열 고정도, 헤더 행 고정도 적용하지 않는다 (전 시트 공통).

**열 너비** — 실제로 기록된 콘텐츠 길이를 추적해 자동 산정한다. 한글은 폭 1.75자로 계산하며, 최소 8 / 최대 26(Keyword 시트는 30)으로 클램프해 잘림도 과도한 확장도 막는다. Spacer 열과 A열은 최소값에서 제외한다.

### Sheet 3 — Brand Search Keywords

**컬럼 구성** — PC와 MO 각각 **7개 데이터 열**, 가운데 Spacer 열 1개.

| B~H: Brand Search_PC | I | J~P: Brand Search_MO |
|---|---|---|
| Keyword (EN) · Keyword (KO) · Spent · Imp · Click · CTR · CPC | (빈 열) | Keyword (EN) · Keyword (KO) · Spent · Imp · Click · CTR · CPC |

- **Spacer 열(I)**: 데이터·테두리·배경 전부 없음. 너비 2.2
- PC 헤더는 `B:H` 병합, MO 헤더는 `J:P` 병합 → 두 개의 독립된 표로 인식

**행 구성** — TOTAL이 키워드 목록 **위**에 온다.

| 행 | 내용 |
|---|---|
| 6 | Device Group Header (`Brand Search_PC` / `Brand Search_MO`) |
| 7 | Column Header |
| 8 | **TOTAL Row** |
| 9~ | 키워드 데이터 (Impression DESC) |

- TOTAL 행은 표 마지막에 두지 않는다. PC·MO 모두 동일하다.
- PC와 MO는 완전히 독립 집계·정렬. 행 수가 다르면 짧은 쪽은 빈 셀로 남기고 억지로 맞추지 않는다.

**TOTAL 계산** — Reporting Period 전체, 해당 Device 기준.

```
Spent = SUM(Keyword Spent)
Imp   = SUM(Keyword Impression)
Click = SUM(Keyword Click)
CTR   = Total Click / Total Impression
CPC   = Total Spent / Total Click
```

키워드별 비율의 평균은 사용하지 않는다. 분모가 0이면 `IFERROR(...,0)`으로 0 처리.

**Spent / CPC** — 리포트 통화 기준. 캠페인 단일 환율로 변환하며 통화 서식은 워크북 전체와 동일하다.

> **용어 통일** — 최종 Excel에 노출되는 광고비 라벨은 전부 `Spent`다. `Cost`는 사용하지 않는다 (Raw Data의 원본 컬럼명이 `총비용`인 것과 무관). 사용 지표명은 `Budget · Spent · Impression/Imp · Click · CTR · CPC · CPM`.

> **Brand Search의 키워드 Spent** — 브랜드검색은 정액제라 Raw Data의 키워드별 총비용이 전 행 0원이다. 그래서 **각 디바이스의 정액료를 그 디바이스 키워드의 노출 비중으로 배분**한다. 그 결과 Sheet 3의 TOTAL Cost가 Sheet 2 Overview의 Subtotal Spent와 정확히 일치한다.

### Sheet 4 — Powerlink (3개 영역)

**영역 ① Overview** — Sheet 2와 동일한 `PC / MO / Subtotal` 구조 (Ad = `Powerlink`).
단 Powerlink는 디바이스별 Budget 입력이 없으므로 **PC·MO Budget은 비우고 Subtotal Budget에만 Powerlink Budget**을 넣는다.

**영역 ② Daily Breakdown** — 전체 Powerlink 성과

| Date | Powerlink_Total (Spent/Impression/Click/CTR) | Powerlink_PC (동일) | Powerlink_MO (동일) |
|---|---|---|---|

- Sheet 2의 Daily Breakdown과 동일 규칙 — 지표 순서 `Spent / Impression / Click / CTR`, 캠페인 전 기간 날짜, 결측일 빈 셀, TOTAL 행 위치
- Overview는 이 표의 합계 행을 참조

**영역 ③ Daily Breakdown by Keyword Group**

영역 ② 아래에 **4개 그룹 테이블을 세로로 순서대로 배치**한다.

```
[그룹명 밴드] Branded
| Date | Branded_Total (Spent/Impression/Click/CTR) | Branded_PC (동일) | Branded_MO (동일) |
   ... 일별 데이터 ... + 합계 행
[빈 행]
[그룹명 밴드] Shoes
| Date | Shoes_Total (...) | Shoes_PC (...) | Shoes_MO (...) |
   ...
[빈 행]
[그룹명 밴드] Competitors
   ...
[빈 행]
[그룹명 밴드] Generic
   ...
```

- **순서 고정: Branded → Shoes → Competitors → Generic** (데이터가 없는 그룹도 헤더만 출력하고 "No data" 표기)
- 그룹명 밴드: 좌측 정렬 볼드 + 그룹별 구분 배경색, 테이블 전체 폭 병합
- 각 그룹 테이블은 영역 ②와 **동일한 2단 헤더 구조 · 동일 열 순서**를 사용하여 세로 비교가 가능하도록 한다
- `{Group}_Total` = `{Group}_PC + {Group}_MO` (수식)
- CTR은 각 날짜·각 그룹별로 `=IFERROR(Click/Imp,0)` 재계산
- 각 그룹 하단 합계 행. **4개 그룹 합계의 합 = 영역 ② 합계**여야 하며, 툴이 생성 시 검증하고 불일치 시 경고
- 가로로 늘어놓지 않고 세로로 쌓는 이유: 4그룹 × 12열 = 48열이 되어 가독성·인쇄가 무너지기 때문

---

### Sheet 5 — Powerlink Keywords (Ad Group별 구분)

컬럼 구성과 Spacer 규칙은 Sheet 3과 동일하다 (`Keyword (EN) · Keyword (KO) · Spent · Imp · Click · CTR · CPC`, PC `B:H` / Spacer `I` / MO `J:P`).

**행 구성**

| 행 | 내용 |
|---|---|
| 6 | Device Group Header (`Powerlink_PC` / `Powerlink_MO`) |
| 7 | 빈 행 |
| 8~ | Ad Group 블록 반복 |

**Ad Group 블록** — `Branded → Shoes → Competitors → Generic` 순서 고정. 각 블록은 다음 순서를 정확히 따른다.

1. Ad Group Header (그룹별 배경색, `B:H` / `J:P` 각각 병합)
2. Keyword Column Header
3. **TOTAL Row** (`{Group} TOTAL`)
4. Keyword 데이터 (Impression DESC)
5. 빈 행 1개
6. 다음 Ad Group

- Column Header는 **각 Ad Group 블록마다 반복**한다.
- TOTAL은 블록 하단이 아니라 **Column Header 바로 아래**에 온다.
- 데이터가 없는 그룹은 헤더 + `No data` 행을 출력하고 순서를 유지한다.
- 하단 전체 합계(GRAND TOTAL) 행은 두지 않는다. 검증은 4개 그룹 TOTAL의 합으로 수행한다.

**그룹별 TOTAL 계산** — 해당 `Group + Device` 키워드만 대상으로 한다.

```
Spent = SUM(Group Keyword Spent)
Imp   = SUM(Group Keyword Impression)
Click = SUM(Group Keyword Click)
CTR   = Group Total Click / Group Total Impression
CPC   = Group Total Spent / Group Total Click
```

- PC와 MO는 각각 독립적으로 집계·정렬하며, 한쪽 그룹의 키워드가 적어도 행 수를 맞추지 않는다.
- Powerlink의 키워드 Spent는 Raw Data의 키워드별 총비용을 환율 변환해 사용한다.

> **참고** — 네이버 반올림 때문에 키워드 파일 총비용(23,923,009 KRW)과 일별 파일 총비용(23,923,003 KRW)에 6원 차이가 있다. Spent는 일별을 정본으로 쓰므로 Sheet 5의 Spent 합계는 Sheet 4와 소수점 이하에서 미세하게 다를 수 있다.

---

## 4.9 Excel Design System

### Gridlines

전 시트에서 **워크시트 눈금선을 표시하지 않는다** (`showGridLines: false`). 일반 스프레드시트가 아니라 정돈된 클라이언트 리포트로 보이게 하기 위함이다.

### Border

| 용도 | 색 |
|---|---|
| 일반 셀·표 내부 구분선 | `#D9DDE4` (연회색, thin) |
| Section·TOTAL·Device Block 경계 | `#AEB6C2` (조금 진한 회색, medium) |

- 검정색이나 두꺼운 테두리는 사용하지 않는다.
- **테두리에는 브랜드 컬러를 쓰지 않는다.** 구조는 회색이 잡고, 색은 헤더가 담당한다.

### Brand Color System

사용자가 고른 **Main Key Color 하나**에서 나머지 톤을 전부 파생시킨다. Secondary는 자동 생성되며 사용자가 따로 고르지 않는다.

| 역할 | 산출 방식 | 사용처 |
|---|---|---|
| **Main** | 선택한 브랜드 컬러 그대로 | Report Title, Section Header, Main Table Header, Media Summary Total |
| PC tint | 명도 +0.12 (상한 0.72), 채도 ×0.92 | Daily Breakdown `_PC` 헤더, Keyword `_PC` 헤더 |
| MO tint | 명도 +0.22 (상한 0.80), 채도 ×0.80 | 〃 `_MO` |
| Sub tints | 각 블록에서 명도 +0.16~0.36, 채도 ×0.52~0.70 | 2단 헤더의 지표명 행, Keyword 컬럼 헤더 |
| **Secondary (band)** | 명도 0.92, 채도 ×0.32 | Section Header 배경, Sheet 1 정보표 라벨 |
| Total tint | 명도 0.88, 채도 ×0.26 | TOTAL / Subtotal 행 배경 |
| Group tints | 명도 0.935 / 0.905 / 0.875 / 0.845, 채도 ×0.30 | Keyword Group 밴드 4종 |

- 데이터 셀은 흰색을 유지한다. 색은 헤더와 강조 영역에만 제한적으로 쓴다.
- 브랜드 컬러가 회색(채도 0)이면 모든 파생 톤이 자연스럽게 그레이 스케일이 된다.

### 텍스트 가독성

- 각 배경색에 대해 **흰색과 `#1A1A1A` 중 대비가 높은 쪽을 자동 선택**한다 (WCAG 상대휘도 기준).
- 파생 톤이 어느 글자색으로도 4.5:1을 넘기지 못하는 중간 명도 구간에 들어가면, **대비 4.5:1을 만족할 때까지 명도를 올린다**(`safeTone`). Main 컬러 자체는 브랜드 값이므로 변형하지 않는다.
- 12개 브랜드 컬러 전부에 대해 파생 톤의 최저 대비가 4.5:1 이상임을 검증 스크립트가 확인한다.

### 디자인 목표

눈금선 없음 · 연회색 테두리 · 흰 배경 중심 · 브랜드 컬러는 주요 헤더에만 · Secondary는 연하고 차분하게 · 과도한 색 사용 금지 · 숫자 가독성 최우선.

---

## 5. Excel Output Rules

| 항목 | 규칙 |
|---|---|
| Sheet 구성 | Overall / Brand Search / Brand Search Keywords / Powerlink / Powerlink Keywords (순서 고정) |
| 수식 | Total·CTR·CPC·CPM·Overview 집계·Overall은 전부 **실제 Excel 수식**. 원자료(Spent/Impression/Click)만 값으로 기록 |
| 오류 방지 | 모든 나눗셈은 `IFERROR(식, 0)`으로 래핑 → `#DIV/0!` 발생 금지 |
| 통화 형식 | **To 통화 기준.** Budget/Spend는 `#,##0`, CPC/CPM은 `#,##0.00` 에 통화 기호를 붙인다 |
| Percentage | `0.00%` (셀에는 소수로 저장하고 서식으로 % 표시. 값에 100을 곱하지 않음) |
| 정수 | `#,##0` (Imp / Click) |
| Gridlines | 전 시트 숨김 |
| 헤더 서식 | **Brand Main Color 배경 + 자동 대비 텍스트**, 2단 헤더 가운데 병합, 전 시트 동일 규칙 |
| Border | 일반 `#D9DDE4` thin, 강조 `#AEB6C2` medium. 검정·브랜드 컬러 미사용 |
| Device Group 구분 | 빈 열 삽입 없이 **medium 세로 테두리 + 블록별 헤더 색**으로 Total/PC/MO 분리 (Daily Breakdown) |
| Layout Offset | **A열·1행 공백**, 모든 Content는 B2부터. 전 시트 동일 |
| Header 뒤 공백 행 | Report Title·모든 Section Header 다음에 **빈 행 1개**. 표 컬럼 헤더는 예외 |
| Sheet 1 정보표 정렬 | 라벨·값 셀 모두 **가로·세로 중앙 정렬** |
| Report Title | 각 시트 B2에 `[Client]_[Campaign Name] …` 동적 생성. 브랜드명 하드코딩 금지 |
| Keyword Spacer 열 | Keyword 시트는 PC(B~H, 7열) · **Spacer 1열 I(완전 공백, 너비 2.2)** · MO(J~P, 7열) 구성 |
| TOTAL 행 위치 | **Daily Breakdown·Keyword 시트 모두 컬럼 헤더 바로 아래.** 표 하단에 두지 않는다 |
| 지표 순서 | Daily Breakdown은 `Spent / Impression / Click / CTR`, Keyword 시트는 `Spent / Imp / Click / CTR / CPC`. `Cost` 표현 미사용 |
| 결측 데이터 | Raw Data가 없는 날짜는 **빈 셀**, 성과 0은 `0`. TOTAL 행은 빈 셀을 집계하지 않음 |
| 그룹명 밴드 | 브랜드 색에서 파생한 4단계 연한 톤 + 볼드 + 좌측 정렬, 전체 폭 병합 |
| 소계/합계 행 | 상단 굵은 테두리 + 볼드 + 연회색 배경 |
| 영역 구분 | 각 영역 사이 공백 행 + 영역 제목 밴드 (`Overview` / `Daily Breakdown` / `Daily Breakdown by Keyword Group`) |
| Freeze Panes | **사용하지 않는다.** 전 시트에서 틀 고정 없음 |
| 열 너비 | 기록된 콘텐츠 길이 기준 자동 산정(한글 1.75자). 최소 8 / 최대 26(Keyword 시트 30). A열 2.4, Spacer 열 2.2 고정 |
| 정렬 | 숫자 우측, 텍스트 좌측, 헤더 가운데 |
| 검증 | 생성 시 ⓐ 그룹 합계 = 전체 합계 ⓑ Keyword 합계 = Overview Imp/Click 를 대조하고 불일치 시 경고 표시 |
| 파일명 | `[Client]_[Campaign]_Weekly_Report_{DataThroughDate}.xlsx` (입력값에서 파일명 안전 문자로 치환) |

---

## 6. localStorage Requirements

단일 루트 키 `client_report_generator_v1` 아래에 JSON으로 저장한다. 구버전 키 `alo_evergreen_report_v1`이 남아 있으면 최초 로드 시 그대로 읽어 이어받는다.

| 키 | 내용 | 삭제 시점 |
|---|---|---|
| `campaign` | Client, **Brand Color**, Campaign Name, Campaign Start/End, Powerlink Campaign | 사용자가 설정 초기화 시 |
| `fx` | `{ fromCountry, fromCurrency, toCountry, toCurrency, rate }` — 캠페인 단일 환율 | 사용자가 수정·삭제 시 |
| `advBudget` | `{ currency:'USD', amount:46000 }` — 캠페인 총 Advertising Budget | 〃 |
| `budgetBS` | `{ currency:'KRW', amount:43230000 }` — Brand Search Budget | 〃 |
| `budgetPL` | `{ currency:'KRW', amount:21169400 }` — Powerlink Budget | 〃 |
| `agencyFeeRate` | Agency Fee 퍼센트 (예: `8`) | 〃 |
| `bsFixedFee` | `{ pc: 5280000, mo: 37950000 }` — 브랜드검색 기간 전체 정액료(KRW) | 〃 |
| `keywordMap` | `[{ category, ko, en }]` — KO→EN 매핑 (기본 315행) | 사용자가 삭제/교체 시 |
| `adGroupMap` | `{ "PC_Branded": "Branded", "MO_General": "Generic", ... }` | 사용자가 삭제/교체 시 |
| `columnMap` | 자동 인식 실패 시 사용자가 지정한 컬럼 매핑 | 〃 |
| `rawDaily` | 정규화된 일별 데이터 | 사용자가 삭제 또는 재업로드 시 |
| `rawKeyword` | 정규화된 키워드 데이터 | 〃 |
| `meta` | 마지막 업로드 파일명·업로드 시각 | 〃 |

**요구사항**
- 원본 CSV 텍스트가 아닌 **정규화된 JSON**을 저장하여 용량을 절감한다.
- 5MB 초과 시 경고 + 오래된 데이터 정리 안내.
- 화면에 저장 상태(업로드 파일, 기간, 등록된 환율/정액료/예산, 감지된 광고그룹, 미매핑 키워드 수)를 항상 표시한다.
- "데이터 삭제" / "전체 초기화" 버튼 제공 (확인 모달 필수).
- 데이터는 브라우저 밖으로 전송되지 않는다 (외부 API 호출 없음).

---

## 7. Open Questions

### 해결 완료

| # | 항목 | 확정 내용 |
|---|---|---|
| R1 | KO→EN 키워드 매핑 | `keyword_mapping.csv` 315행 확보. 샘플 기준 **미매핑 0건** |
| R2 | 키워드 노출 범위 | **Imp 또는 Click이 0이 아닌 키워드 전량 노출**, Imp DESC |
| R3 | Brand Search 정액료 | **기간 전체 기준 PC 5,280,000 / MO 37,950,000 KRW** |
| R4 | 매체 분류 / 캠페인 필터 | `캠페인유형`으로 분리, Powerlink는 `Evergreen_PPC`만 |
| R5 | VAT | 제외 기준 (Raw Data 총비용 그대로) |
| R6 | 환율 | 월별 입력, 해당 월 데이터에만 적용 |
| R7 | Ad Group 분류 | Raw `광고그룹` 기준, 4개 표준값으로 정규화. 샘플 8개 그룹 전부 자동 추론 성공 |
| R8 | Campaign Period / Budget / 환율 | **툴의 Settings 화면에서 입력** (U1~U4). 미입력 시 생성 차단 |
| R9 | 범용화 | Client / Campaign Name 입력 기반으로 제목·파일명·Campaign Information을 동적 생성. 코드에 브랜드명·캠페인명 하드코딩 없음 (검증 스크립트가 매 실행마다 확인) |
| R10 | Layout Offset | 전 시트 A열·1행 공백, Content는 B2 시작 |
| R11 | Header 뒤 공백 행 | 제목·섹션 헤더 다음 빈 행 1개 (표 컬럼 헤더는 제외) |
| R12 | 환율 | **캠페인 단일 환율** + From/To Country 드롭다운. 월별 환율 폐지 |
| R13 | Advertising Budget | **캠페인 총액 1개** + 통화 드롭다운. 월별 입력 방식 폐지 |
| R15 | Tool Input 순서 | 1 Raw Data → 2 캠페인 정보 → 3 캠페인 설정 → 4 환율 → 5 Ad Group → 6 Keyword → 7 현황 |
| R16 | 환율 방향 | From/To 통화를 각각 선택하고 `1 To = rate From`으로 입력. 리포트 통화 = To |
| R17 | Data Through Date | **완전 제거.** 기간 기준은 Campaign Start/End 뿐 |
| R18 | 결측 vs 0 | Raw Data 없는 날짜는 빈 셀, 성과 0은 `0`. TOTAL 행은 빈 셀 제외 |
| R19 | Overview | `PC / MO / Subtotal` 3행 구조. PC/MO Budget은 정액료, Subtotal은 합계 |
| R20 | 틀 고정 | 전 시트 미사용 |
| R21 | Powerlink Budget | Brand Search Budget과 동일하게 `[Currency][금액]` 입력 |
| R22 | Keyword 시트 컬럼 | `EN · KO · Spent · Imp · Click · CTR · CPC` 7열 |
| R23 | Keyword TOTAL 위치 | 컬럼 헤더 바로 아래 (Sheet 3 1개, Sheet 5 그룹별) |
| R24 | Brand Search 키워드 Spent | 정액료를 노출 비중으로 배분 (Raw가 0원이므로) |
| R25 | Gridlines | 전 시트 숨김 |
| R26 | Border | 연회색 2단계, 브랜드 컬러·검정 미사용 |
| R27 | Section Header 뒤 공백 | 표 바로 위에는 넣지 않고, Section 사이에만 유지 |
| R28 | 용어 | 광고비 라벨은 전부 `Spent` |
| R29 | Brand Color | 12색 드롭다운, Secondary·텍스트 색 자동 산출 |
| R14 | Agency Fee | % 입력 → `Total Spent × Rate` 수식으로 금액 산출 |

### 미해결

| # | 질문 | 현재 가정 |
|---|---|---|
| Q1 | Brand Search 정액료가 "리포팅 기간 전체"이므로, 다음 주차에 기간이 늘어나면 **금액도 갱신해야 하는지** | Settings에 항상 노출하여 매주 확인·수정 가능. 미변경 시 기존 총액 유지하고 일별 단가만 재계산 |
| Q2 | Sheet 4 영역 ③에서 **데이터가 0인 그룹**(예: 특정 주에 Shoes 미집행)의 처리 | 헤더 + "No data" 행 출력 (그룹 순서 유지) |
| Q4 | 매핑 리스트의 `에슬레져` / `에슬레져룩` → `Esléger` / `Esléger Look` 표기가 의도된 것인지 (`애슬레저`=Athleisure의 다른 표기로 보임) | 리스트 그대로 유지. 확인 시 `Athleisure` / `Athleisure Look`으로 통일 |
| Q5 | 일별 합계와 키워드 합계에 **7 KRW 오차** 존재(네이버 반올림) | **일별 리포트를 정본**으로 사용 (Spend는 일별에서만 산출) |
| Q11 | 정액료·Powerlink Budget을 `KRW 고정`으로 요청받았으나 툴은 범용이다 | **Raw Data 통화(From)로 고정**하고 라벨에 통화 코드를 표시. From이 KRW면 요청대로 KRW로 보인다 |
| Q12 | Raw Data 업로드를 4개 슬롯으로 나눌지 | 네이버는 일별/키워드 2개 파일로만 내려받히므로 **2개 슬롯 유지**, 4종 데이터는 `캠페인유형`으로 자동 분리 |
| Q13 | Powerlink Overview의 **PC/MO Budget** 입력이 없다 | PC·MO Budget은 공란, Subtotal에만 Powerlink Budget 표기. 디바이스별 예산이 필요하면 입력란 추가 필요 |
| Q14 | 지표 순서·틀 고정 변경을 Sheet 2에만 적용할지 | Sheet 2·4가 같은 구조를 공유해야 하므로 **양쪽 모두 적용**. Sheet 4의 그룹별 Daily Breakdown도 동일 |
| Q15 | Brand Search 키워드 Spent 배분 기준을 **노출 비중**으로 할지 클릭 비중으로 할지 | 노출 비중. 일별 PC/MO 배분과 동일한 기준 |
| Q16 | Ad Group 밴드 다음에 빈 행을 넣지 않아 '헤더 뒤 공백 행' 일반 규칙과 어긋난다 | 새 규격의 6단계 순서가 더 구체적이므로 그쪽을 따름. Sheet 4의 그룹 밴드는 기존대로 빈 행 유지 |
| Q6 | Powerlink에서 제외한 `ALO Wellness Club` 캠페인의 향후 처리 | 현재 스코프 제외. 캠페인 필터는 Settings에서 변경 가능하도록 설계 |
| Q7 | Excel에 브랜드 로고/컬러 등 **디자인 가이드** 적용 여부 | 기본 남색 헤더 테마 |
| Q8 | **기존 ALO Weekly Report 원본 파일 미수령.** 레이아웃은 서면 규격대로 구현했으나 폰트·색상·열너비 등 세부 서식은 원본 대조 필요 | 첨부 파일 수령 시 재현도 보완 |
| Q9 | Agency Fee가 Advertising Budget에 **포함되는 금액인지 별도인지** | 별도 항목으로 표기, 합산하지 않음 |
| Q10 | **Budget 입력이 두 갈래**(캠페인 총 Advertising Budget / 매체별 Budget)로 나뉜다. 하나로 통합할지 | 둘 다 입력받고 **합계가 다르면 툴에서 경고**. Sheet 1 정보표는 총액, Media Summary는 매체별 값 사용 |

> **참고 — 번역 보정 내역**: 제공된 리스트에서 Generic 14개 키워드(겨울헬스복, 트레이닝세트, 요가커버업, 필라테스옷추천, 트레이닝복세트, 여성헬스복, 겨울트레이닝복세트, 필라테스복세트, 겨울트레이닝세트, 겨울요가바지, 겨울트레이닝복, 츄리닝세트, 요가상의, 연예인요가복)가 모두 `winter yoga wear`로 잘못 매핑되어 있어 개별 번역으로 보정했다. (`Winter gym wear`, `Training set`, `Yoga cover-up`, `Recommended Pilates clothing`, `Training wear set`, `Women's gym wear`, `Winter training wear set`, `Pilates outfit set`, `Winter training set`, `Winter yoga pants`, `Winter training wear`, `Tracksuit set`, `Yoga tops`, `Celebrity yoga wear`)
