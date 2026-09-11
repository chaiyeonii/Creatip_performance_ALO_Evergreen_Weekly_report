# PRD — Weekly Report Generator (네이버 검색광고)

| 항목 | 내용 |
|---|---|
| 제품명 | Weekly Report Generator |
| 목적 | 네이버 검색광고 Raw Data를 업로드하면 클라이언트 제출용 5-Sheet Excel 리포트를 자동 생성 |
| 적용 범위 | **특정 브랜드 전용이 아닌 범용 툴.** Client · Campaign Name · Brand Color를 입력받아 어떤 광고주에게도 재사용 |
| 형태 | 단일 HTML 파일 `index.html` — 브라우저에서 실행, 서버·설치 불필요 |
| 라이브러리 | SheetJS 0.18.5 (파싱) · ExcelJS 4.4.0 (서식·수식 포함 xlsx 출력), cdnjs 로드 |
| 데이터 저장 | 브라우저 `localStorage` — 외부 서버 전송 없음 |
| 산출물 | `[Client]_[Campaign]_Weekly_Report_[CampaignEnd YYYYMMDD].xlsx` |
| 문서 기준일 | 2026-09-11 · 구현 커밋 `0d74c71` 기준 |

---

## 목차

1. [Tool 입력 흐름](#1-tool-입력-흐름)
2. [Raw Data](#2-raw-data)
3. [계산 로직](#3-계산-로직)
4. [시트 공통 규칙](#4-시트-공통-규칙)
5. [시트별 구조](#5-시트별-구조)
6. [Excel 디자인 시스템](#6-excel-디자인-시스템)
7. [Excel 출력 규칙 요약](#7-excel-출력-규칙-요약)
8. [localStorage](#8-localstorage)
9. [설계 결정 기록](#9-설계-결정-기록)
10. [미해결 사항](#10-미해결-사항)
11. [부록](#11-부록)

---

## 1. Tool 입력 흐름

화면은 아래 순서를 그대로 따른다. 모든 입력은 `localStorage`에 저장되어 새로고침·다음 주차에도 유지된다.

### 1단계 — Raw Data 업로드

| 슬롯 | 파일 예시 |
|---|---|
| ① 일별 리포트 | `일별,2226795.csv` |
| ② 키워드 리포트 | `키워드,2226795.csv` |

두 파일 모두 브랜드검색과 파워링크가 섞여 있다. `캠페인유형` 컬럼으로 **Brand Search Daily · Brand Search Keyword · Powerlink Daily · Powerlink Keyword** 4종 데이터가 자동 분리된다. CSV·XLSX 모두 지원.

### 2단계 — 캠페인 정보

| 항목 | 형식 | 필수 | 설명 |
|---|---|:-:|---|
| Client | text | ● | 모든 시트 제목과 Sheet 1 `Client` 값 (예: `ALO`, `FIGS`, `OWALA`) |
| Brand Color | dropdown | | 12색 중 선택. 워크북 전체의 Main Key Color (§6) |
| Campaign Name | text | ● | 모든 시트 제목과 Sheet 1 `Campaign` 값 (예: `Evergreen`, `JISOO`, `Always-on`) |
| Advertising Budget | `[통화▼] [금액]` | ● | **캠페인 전체 기간의 총 예산 1개.** Sheet 1 정보표 값 |
| Agency Fee (%) | number | ● | 퍼센트 입력. Excel에는 `Total Spent × Rate` 수식으로 계산된 **금액**이 들어간다 |

Client와 Campaign Name을 입력하면 생성될 5개 시트 제목이 화면에 **실시간 미리보기**로 표시된다.

### 3단계 — 캠페인 설정

| 구분 | 항목 | 형식 | 필수 | 설명 |
|---|---|---|:-:|---|
| 기간 | Campaign Start / End | date picker | ● | **리포트의 유일한 기간 기준** |
| Brand Search | Budget | `[통화▼] [금액]` | ● | Sheet 1 Media Summary 대조용 · 정액료 합과 비교 경고 |
| | 정액료 · PC | number (Raw Data 통화 고정) | ●¹ | Overview PC Budget, 일별·키워드 Spent 배분의 원천 |
| | 정액료 · MO | number (Raw Data 통화 고정) | ●¹ | 〃 Mobile |
| Powerlink | Budget | `[통화▼] [금액]` | ● | Sheet 1 Media Summary · Sheet 4 Overview Budget |
| | Powerlink Campaign | dropdown | | 업로드된 Raw Data의 실제 캠페인 값으로 **자동 생성**. 선택한 캠페인만 Powerlink 리포트에 포함 |

¹ PC·MO 중 최소 하나.

### 4단계 — 환율

| 항목 | 형식 | 설명 |
|---|---|---|
| From — Country / Currency | dropdown | Raw Data 광고비의 통화 |
| To — Country / Currency | dropdown | **리포트 통화.** Excel 통화 서식이 이 값을 따른다 |
| Exchange Rate | number | **캠페인 전체에 단일 환율 1개.** `1 <To> = rate <From>` 방향으로 입력. From = To이면 입력 불필요 |

지원 국가 17개: Korea/KRW · Japan/JPY · United States/USD · China/CNY · Taiwan/TWD · Hong Kong/HKD · Singapore/SGD · Thailand/THB · Vietnam/VND · Indonesia/IDR · Malaysia/MYR · Philippines/PHP · India/INR · Australia/AUD · Canada/CAD · United Kingdom/GBP · Eurozone/EUR

### 5~7단계 — 매핑과 현황

| 단계 | 내용 |
|---|---|
| 5. Ad Group 매핑 | Raw 광고그룹 → `Branded / Shoes / Competitors / Generic`. 자동 추론 + 드롭다운 수정 |
| 6. Keyword 매핑 | KO→EN 매핑 315행 내장. 목록 보기 · CSV 교체 · 내려받기 · 기본값 복원 |
| 7. 데이터 현황 | 행 수, Raw Data 기간, Campaign Period, 적용 환율, 저장 용량, 업로드 시각 · 데이터 삭제 / 전체 초기화 |

### 입력 규칙

- **환율·예산 등 금액은 절대 자동 조회·추정하지 않는다.** 사용자가 직접 입력한다.
- Budget 통화 드롭다운은 **From / To 두 통화만** 제공한다 — 단일 환율로 변환 가능한 조합만 허용.
- 필수 항목이 비거나 Ad Group이 미분류이면 **생성 버튼이 비활성화**되고 비어 있는 항목이 목록으로 표시된다.
- 금액 불일치는 생성을 막지 않고 **경고로 표시**한다 (값을 임의로 고치지 않는다).
  - Brand Search Budget ≠ 정액료 PC + MO
  - Advertising Budget ≠ Brand Search Budget + Powerlink Budget

---

## 2. Raw Data

### 2.1 파일 포맷

- 인코딩 UTF-8 with BOM (EUC-KR도 자동 판별)
- **1행 = 제목 행** (예: `"일별(2026.07.07.~2026.08.06.),2226795"`) → 스킵
- **2행 = 헤더**, 3행부터 데이터
- 헤더가 1행에 있는 파일도 자동 인식

### 2.2 내부 표준 컬럼

| 표준 | 일별 리포트 | 키워드 리포트 | 비고 |
|---|---|---|---|
| `media` | 캠페인유형 | 캠페인유형 | `브랜드검색/신제품검색` → BS, `파워링크` → PL |
| `campaign` | 캠페인 | 캠페인 | Powerlink 캠페인 필터 |
| `adGroup` | 광고그룹 | 광고그룹 | Powerlink 그룹 분류 |
| `device` | PC/모바일 매체 | PC/모바일 매체 | `PC` → PC, `모바일`/`Mobile`/`MO` → MO |
| `date` | 일별 | — | |
| `keyword` | — | 키워드 | |
| `imp` | 노출수 | 노출수 | |
| `click` | 클릭수 | 클릭수 | |
| `cost` | 총비용 | 총비용 | VAT 제외 금액 그대로 사용 |
| (미사용) | 클릭률(%), 평균 CPC | 클릭률(%), 평균 CPC | **읽지 않고 전부 재계산** |

### 2.3 정규화

- 헤더는 공백·괄호·대소문자 차이를 허용하는 **별칭 사전**으로 매핑한다.
- 필수 컬럼을 찾지 못하면 누락 컬럼명과 인식된 헤더를 보여주고 중단한다.
- 날짜 `YYYY.MM.DD.` · `YYYY-MM-DD` · `YYYY/MM/DD` · `YYYYMMDD` → `YYYY-MM-DD`.
- 인식되지 않는 디바이스 값은 집계에서 제외하고 경고한다.
- 숫자는 콤마·공백 제거 후 변환, 빈값은 0.

### 2.4 Ad Group 정규화 (Powerlink)

디바이스 접두사(`PC_`, `MO_`)를 제거한 뒤 포함 문자열로 추론한다.

| 포함 문자열 (대소문자 무시) | 표준값 |
|---|---|
| `compet`, `comp` | Competitors |
| `shoe` | Shoes |
| `brand` | Branded |
| `general`, `generic` | Generic |

- 추론 실패 그룹은 `미분류`로 표시되고 **지정할 때까지 생성이 차단**된다.
- 분류 기준은 Raw Data의 광고그룹이다. 키워드 매핑의 Category는 참조하지 않는다.
- 네이버 Raw의 `General`은 리포트에서 `Generic`으로 표기된다.

---

## 3. 계산 로직

### 3.1 파이프라인

1. 파싱 → 컬럼 매핑 → 날짜·디바이스·숫자 정규화
2. `캠페인유형`으로 Brand Search / Powerlink 분리, Powerlink는 **선택한 캠페인만** 필터
3. Campaign Start ~ End 범위로 필터
4. Powerlink 광고그룹 → 4개 표준값
5. Brand Search 정액료를 일별·키워드별로 배분
6. 집계 — (날짜 × 디바이스), (날짜 × 그룹 × 디바이스), (그룹 × 디바이스 × 키워드)
7. From → To 통화 변환 (캠페인 단일 환율)
8. Sheet 2~5 생성 → Sheet 1은 하위 시트 셀을 **수식으로 참조**

### 3.2 환율

```
값(To) = 값(From) / rate        ← rate는 "1 To = rate From"
```

- 예: From KRW, To USD, `1 USD = 1,400 KRW` → `USD = KRW / 1,400`
- **캠페인 전 기간에 동일한 환율 1개**를 적용한다. 월별 환율은 사용하지 않는다.
- From = To이면 변환하지 않는다.
- Spent · Budget · 정액료 모두 같은 환율로 변환한다.

### 3.3 Brand Search Spent 배분

브랜드검색은 **정액제 상품이라 Raw Data의 `총비용`이 일별·키워드 모두 전 행 0원**이다. 사용자가 입력한 정액료로 Spent를 만든다.

| 대상 | 규칙 |
|---|---|
| PC / MO | 안분하지 않는다. 입력한 PC 금액·MO 금액을 각 디바이스에 그대로 귀속 |
| 일별 | 디바이스별 정액료를 **그 디바이스에 데이터가 존재하는 일수로 균등 배분**. 반올림 잔액은 마지막 날에 보정해 합계가 정액료와 정확히 일치 |
| 키워드 | 디바이스별 정액료를 **그 디바이스 키워드들의 노출 비중으로 배분** |

결과적으로 Sheet 2 Overview Subtotal Spent = Sheet 3 TOTAL Spent = 정액료 PC + MO (환율 변환 후).

Powerlink는 Raw Data의 총비용을 그대로 쓴다.

### 3.4 파생 지표

```
CTR = Click / Impression
CPC = Spent / Click
CPM = Spent / Impression × 1,000
```

- **모든 합계 행·Subtotal·TOTAL은 합계값으로 다시 계산한다.** 일별·키워드별 비율의 평균은 쓰지 않는다.
- 모든 나눗셈은 `IFERROR(…, 0)` — 분모 0이면 0.

### 3.5 기간과 결측 데이터

- 기간 기준은 **Campaign Start ~ Campaign End 뿐**이다.
- Daily Breakdown은 **캠페인 기간의 모든 날짜**를 행으로 만든다.
- Raw Data가 없는 날과 성과가 0인 날을 **반드시 구분**한다.

| 상태 | 표기 |
|---|---|
| 그 날짜·디바이스의 Raw Data 행이 **없음** | **빈 셀** (값·수식 없음, 테두리와 서식은 유지) |
| Raw Data 행은 있으나 성과가 **0** | `0`, `0.00%` 등 실제 값 |

- 한 날짜에 PC만 없으면 → PC 4칸은 빈 셀, Total은 **MO만** 합산.
- 양쪽 다 없으면 → Total 포함 그 행의 지표 셀이 전부 빈 셀.
- TOTAL 행의 `SUM()`은 빈 셀을 무시하므로 **Raw Data가 있는 구간만** 집계된다.

### 3.6 키워드 집계

| | Brand Search | Powerlink |
|---|---|---|
| 집계 키 | (디바이스, 키워드) | (광고그룹, 디바이스, 키워드) |
| 포함 조건 | Imp > 0 또는 Click > 0 | 〃 |
| 정렬 | 디바이스별 Impression DESC | 그룹 순서 고정 → 그룹 내 Impression DESC |
| PC / MO | 완전히 독립 집계·정렬, 행 수를 맞추지 않음 | 〃 |

**Keyword (EN) 매핑**
- 조회 키는 공백 제거 + 소문자 (`알로 지수` → `알로지수`).
- 같은 KO가 여러 번 나오면 먼저 나온 행을 쓰고, EN이 서로 다르면 충돌 경고.
- 매핑에 없으면 `[UNMAPPED]`로 표기하고, 생성 후 화면에 미매핑 목록을 노출.
- Category 컬럼은 Excel에 출력하지 않는다.

---

## 4. 시트 공통 규칙

### 4.1 시트 구성과 제목

| # | 시트명 | B2 제목 |
|---|---|---|
| 1 | Overall | `[Client]_[Campaign] AD Summary` |
| 2 | Brand Search | `[Client]_[Campaign] Brand Search Report` |
| 3 | Brand Search Keywords | `[Client]_[Campaign] Brand Search Keyword Report` |
| 4 | Powerlink | `[Client]_[Campaign] Powerlink Report` |
| 5 | Powerlink Keywords | `[Client]_[Campaign] Powerlink Keyword Report` |

예: Client `ALO` · Campaign `Evergreen` → `ALO_Evergreen AD Summary`

**브랜드명·캠페인명은 코드에 하드코딩하지 않는다.** 제목·정보표·파일명 모두 입력값에서 생성한다.

### 4.2 여백

- **A열과 1행은 전 시트에서 완전 공백** (A열 너비 2.4, 1행 높이 9). 모든 콘텐츠는 **B2**부터 시작한다.
- **Report Title 다음에는 빈 행 1개.**
- **Section Header 바로 아래에는 빈 행 없이 표가 붙는다.** 빈 행은 서로 다른 Section Block 사이에만 쓴다.

```
Overview          ← Section Header
Media | Ad | …    ← 표가 바로 이어짐
…
(빈 행)            ← Section 사이 구분
Daily Breakdown
Date | …
```

- 예외: `Daily Breakdown by Keyword Group` 밴드와 Keyword 시트 부제 밴드는 아래에 또 다른 밴드가 오므로 빈 행을 둔다.
- 표의 컬럼 헤더 아래에는 빈 행을 넣지 않는다.

### 4.3 용어

광고비 라벨은 전 시트에서 **`Spent`**로 통일한다. `Cost`는 사용하지 않는다.
사용 지표명: `Budget · Spent · Impression / Imp · Click · CTR · CPC · CPM`

### 4.4 기타

- **틀 고정 없음** — 전 시트에서 행·열 모두 고정하지 않는다.
- **열 너비 자동** — 실제로 기록된 콘텐츠 길이로 산정 (한글 1자 = 1.75). 최소 8 · 최대 26 (Keyword 시트 30). A열과 Spacer 열은 예외.

---

## 5. 시트별 구조

### Sheet 1 — Overall (AD Summary)

| 행 | 내용 |
|---|---|
| 2 | Report Title |
| 3 | 빈 행 |
| 4~10 | 기본 정보표 7행 |
| 11 | 빈 행 |
| 12 | `Media Summary` Section Header |
| 13 | 표 헤더 |
| 14 · 15 · 16 | Brand Search · Powerlink · Total |

**기본 정보표** — 섹션 헤더 없이 제목 아래에 바로 온다. 라벨은 B열, 값은 C:E 병합. **라벨·값 모두 가로·세로 중앙 정렬.**

| 항목 | 값 |
|---|---|
| Client | 입력값 |
| Campaign | 입력값 (Client가 아니라 Campaign Name) |
| Period | `YYYY.MM.DD - YYYY.MM.DD` |
| Total Spent | Media Summary Total 행 Spent **수식 참조** |
| Advertising Budget | 캠페인 총 예산 (리포트 통화로 변환) |
| Agency Fee | **`= Total Spent 셀 × Rate`** 수식 → 금액 표시 |
| Exchange Rate | `1 USD = 1,400 KRW` · From = To이면 `USD (no conversion)` |

**Media Summary**

| Campaign | Period | Media | Ad | Budget | Spent | Impression | Click | CTR | CPC | CPM |
|---|---|---|---|---|---|---|---|---|---|---|

- Campaign · Period · Media(`Naver SA`)는 두 매체 행에 걸쳐 **세로 병합**
- Budget·Spent·Impression·Click은 Sheet 2·4 **Overview Subtotal 행을 수식 참조**
- Total 행: Campaign~Ad 4열 가로 병합, Main Color 배경
- CTR·CPC·CPM은 각 행 합계로 재계산

### Sheet 2 — Brand Search Report

| 행 | 내용 |
|---|---|
| 2 | Report Title |
| 3 | 빈 행 |
| 4 | `Overview` |
| 5 | Overview 헤더 |
| 6 · 7 · 8 | PC · MO · **Subtotal** |
| 9 | 빈 행 |
| 10 | `Daily Breakdown` |
| 11 · 12 | 2단 헤더 |
| 13 | **TOTAL** |
| 14~ | 캠페인 기간의 모든 날짜 (오름차순) |

**Overview** (B~K)

| Media | Ad | Device | Budget | Spent | Impression | Click | CTR | CPC | CPM |
|---|---|---|---|---|---|---|---|---|---|
| Naver SA | Brand Search | PC | | | | | | | |
| 〃 | 〃 | MO | | | | | | | |
| 〃 | 〃 | **Subtotal** | | | | | | | |

- Media · Ad는 3행 세로 병합
- Spent · Impression · Click은 Daily Breakdown TOTAL 행의 해당 블록을 수식 참조
- **Budget**: PC = 정액료 PC, MO = 정액료 MO, Subtotal = PC + MO (수식)
- Subtotal 행은 Total tint 배경 + 볼드 + 상단 강조선

**Daily Breakdown** (B~N)

| Date | Brand Search_Total | | | | Brand Search_PC | | | | Brand Search_MO | | | |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | Spent | Impression | Click | CTR | Spent | Impression | Click | CTR | Spent | Impression | Click | CTR |
| **TOTAL** | | | | | | | | | | | | |
| 2026-07-07 | | | | | | | | | | | | |

- 열: B Date · C~F Total · G~J PC · K~N MO
- Total 블록 = 그 날 존재하는 디바이스만 더한 수식
- **TOTAL 행은 헤더 바로 아래** — 표 하단에 두지 않는다
- Total / PC / MO는 빈 열 없이 **medium 세로 테두리 + 블록별 헤더 색**으로 구분

### Sheet 3 — Brand Search Keyword Report

| 행 | 내용 |
|---|---|
| 2 | Report Title |
| 3 | 빈 행 |
| 4 | 부제 `Keyword Breakdown by Device · 기간` |
| 5 | 빈 행 |
| 6 | Device Header (`Brand Search_PC` / `Brand Search_MO`) |
| 7 | 컬럼 헤더 |
| 8 | **TOTAL** |
| 9~ | 키워드 (Impression DESC) |

| B~H: Brand Search_PC | I | J~P: Brand Search_MO |
|---|---|---|
| Keyword (EN) · Keyword (KO) · Spent · Imp · Click · CTR · CPC | Spacer | Keyword (EN) · Keyword (KO) · Spent · Imp · Click · CTR · CPC |

- **Spacer 열 I**는 데이터·테두리·배경이 전혀 없는 완전 공백 (너비 2.2)
- PC `B:H`, MO `J:P` 각각 헤더 병합 → 두 개의 독립된 표로 보인다
- TOTAL: Spent·Imp·Click은 `SUM`, CTR = Click / Imp, CPC = Spent / Click

### Sheet 4 — Powerlink Report

영역 ①②는 Sheet 2와 **행 번호까지 동일**하다.

- **Overview** — Ad = `Powerlink`. 디바이스별 예산 입력이 없으므로 **PC·MO Budget은 공란, Subtotal에만 Powerlink Budget.**
- **Daily Breakdown** — Sheet 2와 같은 열 구성·지표 순서·결측 처리·TOTAL 위치.

**영역 ③ Daily Breakdown by Keyword Group**

```
(빈 행)
Daily Breakdown by Keyword Group     ← 섹션 밴드
(빈 행)
Branded                               ← 그룹 밴드
Date | Branded_Total | Branded_PC | Branded_MO    ← 헤더가 바로 이어짐
TOTAL
날짜 …
(빈 행)
Shoes
…
Competitors
…
Generic
…
Check: Σ Groups = Total   OK | OK | OK
```

- **그룹 순서 고정**: Branded → Shoes → Competitors → Generic
- 각 그룹 표는 영역 ②와 **같은 열 구성**이라 세로로 비교할 수 있다
- 데이터가 없는 그룹도 헤더와 `No data`를 출력해 순서를 유지한다
- 마지막 **Check 행**이 4개 그룹 TOTAL의 합 = 영역 ② TOTAL을 Spent·Impression·Click별로 검증해 `OK / MISMATCH`를 표시한다
- 가로로 늘어놓지 않는 이유: 4그룹 × 12열 = 48열이 되어 가독성·인쇄가 무너진다

### Sheet 5 — Powerlink Keyword Report

컬럼 구성과 Spacer 규칙은 Sheet 3과 같다 (PC `B:H` · Spacer `I` · MO `J:P`).

| 행 | 내용 |
|---|---|
| 2 | Report Title |
| 3 | 빈 행 |
| 4 | 부제 `Keyword Breakdown by Ad Group & Device · 기간` |
| 5 | 빈 행 |
| 6 | Device Header (`Powerlink_PC` / `Powerlink_MO`) |
| 7 | 빈 행 |
| 8~ | Ad Group 블록 반복 |

**Ad Group 블록** — Branded → Shoes → Competitors → Generic

1. 그룹 밴드 (`B:H` / `J:P` 각각 병합)
2. 컬럼 헤더 (블록마다 반복)
3. **`{Group} TOTAL`**
4. 키워드 (Impression DESC)
5. 빈 행 1개 → 다음 그룹

- 그룹 TOTAL은 해당 **그룹 + 디바이스** 키워드만 집계한다
- 하단 전체 합계(GRAND TOTAL)는 두지 않는다

---

## 6. Excel 디자인 시스템

### 6.1 기본

| 요소 | 규칙 |
|---|---|
| 눈금선 | **전 시트 숨김** |
| 배경 | 데이터 셀은 흰색. 색은 헤더·강조 영역에만 제한적으로 사용 |
| 테두리 | 일반 `#D9DDE4` thin · 강조(섹션·TOTAL·디바이스 블록 경계) `#AEB6C2` medium |
| 테두리 금지 | 검정·두꺼운 테두리, **브랜드 컬러 테두리** 사용 금지 |

### 6.2 Brand Color

| 이름 | HEX | 이름 | HEX | 이름 | HEX |
|---|---|---|---|---|---|
| Black | `#1A1A1A` | Green | `#2E7D4F` | Red | `#C0392B` |
| **Navy** (기본) | `#1F3864` | Mint | `#2FA89B` | Pink | `#D25A80` |
| Blue | `#2E5395` | Yellow | `#E0A81E` | Purple | `#6B4C9A` |
| Sky Blue | `#3E8FD0` | Orange | `#DD7A26` | Gray | `#5A6472` |

선택지는 배열 하나로 관리되어 색을 추가하기 쉽다.

### 6.3 파생 톤

선택한 Main 하나에서 나머지 톤을 **자동 생성**한다. 사용자는 Secondary를 고르지 않는다.

| 톤 | 산출 (HSL) | 사용처 |
|---|---|---|
| **Main** | 선택값 그대로 | Report Title · Overview/Media Summary 헤더 · Daily Total 블록 헤더 · Media Summary Total 행 · Sheet 3 TOTAL |
| PC tint | 명도 +0.12 (상한 0.72), 채도 ×0.92 | `_PC` 디바이스 헤더 |
| MO tint | 명도 +0.22 (상한 0.80), 채도 ×0.80 | `_MO` 디바이스 헤더 |
| Sub tints | 명도 +0.16 ~ +0.36, 채도 ×0.52 ~ 0.70 | 2단 헤더의 지표명 행 · Keyword 컬럼 헤더 |
| **Secondary** | 명도 0.92, 채도 ×0.32 | Section Header 밴드 · Sheet 1 정보표 라벨 |
| Total tint | 명도 0.88, 채도 ×0.26 | TOTAL · Subtotal · 그룹 TOTAL 행 |
| Group tints | 명도 0.935 / 0.905 / 0.875 / 0.845, 채도 ×0.30 | Keyword Group 밴드 4종 |

회색 계열 브랜드는 모든 톤이 자연스럽게 그레이 스케일이 된다.

### 6.4 텍스트 가독성

- 모든 색 배경마다 **흰색과 `#1A1A1A` 중 대비가 높은 쪽**을 자동 선택한다 (WCAG 상대휘도).
- 파생 톤이 어느 쪽으로도 **4.5:1**을 넘지 못하면 넘을 때까지 명도를 올린다. Main은 브랜드 값이므로 변형하지 않는다.
- 12개 브랜드 컬러 전부에서 최저 대비 4.5:1 이상을 검증 스크립트가 확인한다.

---

## 7. Excel 출력 규칙 요약

| 항목 | 규칙 |
|---|---|
| 시트 순서 | Overall · Brand Search · Brand Search Keywords · Powerlink · Powerlink Keywords |
| 수식 | 원자료(Spent · Impression · Click)만 값. Total · CTR · CPC · CPM · Overview · Overall은 **실제 Excel 수식** |
| 오류 | 모든 나눗셈 `IFERROR(…, 0)` — `#DIV/0!` 없음 |
| 통화 서식 | **To 통화 기호** + Sheet 1의 Budget·Spent·Agency Fee는 `#,##0`, 그 외 금액(CPC·CPM·Sheet 2~5)은 `#,##0.00` (기호 예: `$`, `₩`, `¥`, `€`, `S$`) |
| 백분율 | `0.00%` — 셀에는 소수 저장 |
| 정수 | `#,##0` |
| 정렬 | 헤더·라벨·날짜 가운데 · 숫자 우측 |
| 파일명 | `[Client]_[Campaign]_Weekly_Report_[CampaignEnd].xlsx` — 파일명에 쓸 수 없는 문자는 `_`로 치환 |

---

## 8. localStorage

루트 키 `client_report_generator_v1`. 구버전 키 `alo_evergreen_report_v1`이 있으면 최초 1회 읽어 이어받는다.

| 키 | 내용 |
|---|---|
| `campaign` | client · name · brandColor · start · end · plCampaign |
| `advBudget` | `{ currency, amount }` — 캠페인 총 예산 |
| `budgetBS` | `{ currency, amount }` — Brand Search Budget |
| `budgetPL` | `{ currency, amount }` — Powerlink Budget |
| `bsFixedFee` | `{ pc, mo }` — Raw Data 통화 |
| `agencyFeeRate` | 퍼센트 숫자 |
| `fx` | `{ fromCountry, fromCurrency, toCountry, toCurrency, rate }` |
| `adGroupMap` | Raw 광고그룹 → 표준값 |
| `keywordMap` | `[{ category, ko, en }]` · `keywordMapIsDefault` |
| `rawDaily` / `rawKeyword` | 정규화된 JSON (원본 CSV 텍스트 아님) |
| `meta` | 업로드 파일명 · 업로드 시각 |

- 저장 용량 4.5MB 초과 시 경고
- "업로드 데이터 삭제"(설정 유지) · "전체 초기화" 모두 확인 창 필수
- 데이터는 브라우저 밖으로 전송되지 않는다

---

## 9. 설계 결정 기록

요청 사이에 충돌이 있었거나 구현에서 판단이 필요했던 항목.

| # | 주제 | 결정 | 이유 |
|---|---|---|---|
| D1 | 업로드 슬롯 수 | 4종 데이터를 요구했으나 **슬롯은 2개** | 네이버는 일별·키워드 2개 파일로만 내려받히고 두 매체가 섞여 있음. `캠페인유형`으로 자동 분리 |
| D2 | 환율 | 월별 → **캠페인 단일 환율**로 변경 | 주차별 보고서 간 수치 일관성 |
| D3 | 환율 방향 | From / To를 따로 고르고 `1 To = rate From` | 어떤 통화 조합이든 같은 식으로 계산 |
| D4 | 정액료 통화 | "KRW 고정" 요청을 **Raw Data 통화(From) 고정**으로 구현 | 범용 툴이므로. From이 KRW면 요청대로 보인다 |
| D5 | Brand Search 키워드 Spent | 정액료를 **노출 비중**으로 배분 | Raw 키워드 총비용이 0원. 일별 배분과 같은 기준이며 Sheet 2·3 합계가 정확히 일치 |
| D6 | Powerlink Overview Budget | PC·MO 공란, Subtotal만 | 디바이스별 예산 입력이 없음 |
| D7 | 예산 이중 입력 | 캠페인 총액과 매체별을 모두 받고 **불일치 시 경고만** | 정보표와 Media Summary의 원천이 다름. 값은 임의 수정하지 않음 |
| D8 | Sheet 2 한정 변경 | 지표 순서·틀 고정·Overview 구조를 **Sheet 4에도 적용** | 두 시트가 같은 구조를 공유해야 함 |
| D9 | 빈 행 규칙 충돌 | Section Header 바로 아래는 표, 빈 행은 섹션 사이에만 | 최신 규격이 더 구체적 |
| D10 | Sheet 5 합계 | 그룹 TOTAL을 상단으로 옮기면서 **GRAND TOTAL 제거** | TOTAL을 위로 올리라는 취지. 검증은 그룹 TOTAL의 합으로 |
| D11 | Spent 정본 | Powerlink Spent는 **일별 파일**을 정본으로 | 키워드 파일과 네이버 반올림으로 수 원 차이 |
| D12 | 컬럼 인식 실패 | 수동 매핑 UI 대신 **누락 컬럼을 알려주고 중단** | 네이버 표준 헤더는 별칭 사전으로 모두 인식됨. 수동 매핑 UI는 미구현 |

---

## 10. 미해결 사항

| # | 질문 | 현재 처리 |
|---|---|---|
| Q1 | 기존 ALO Weekly Report 원본 파일 미수령 | 서면 규격대로 구현. 폰트·밀도 등 세부 서식은 원본 대조 필요 |
| Q2 | Brand Search 정액료가 기간 전체 금액이므로, 주차가 늘면 금액도 갱신해야 하는가 | 설정에 항상 노출. 미변경 시 총액 유지, 일별 단가만 재계산 |
| Q3 | 예산 이중 입력을 하나로 통합할 것인가 | 현재는 둘 다 받고 경고 (D7) |
| Q4 | Powerlink도 디바이스별 예산이 필요한가 | 현재는 Subtotal만 (D6) |
| Q5 | Brand Search 키워드 Spent를 클릭 비중으로 배분해야 하는가 | 현재 노출 비중 (D5) |
| Q6 | Agency Fee가 Advertising Budget에 포함되는가 | 별도 항목, 합산하지 않음 |
| Q7 | `에슬레져` / `에슬레져룩` → `Esléger` 표기가 의도된 것인가 | 리스트 그대로 유지. 확인 시 `Athleisure`로 통일 |
| Q8 | Powerlink에서 제외한 캠페인(예: `ALO Wellness Club`)을 별도 시트로 다룰 것인가 | 현재는 드롭다운으로 1개만 선택 |

---

## 11. 부록

### A. 검증

리포지토리 `verify/`에 브라우저 없이 툴을 검증하는 스크립트가 있다. `index.html`의 JS를 V8(py-mini-racer)에서 그대로 실행하고, 생성된 워크북의 셀·수식·서식을 전부 대조한다.

```
python run_js.py     # JS 실행 → 워크북 덤프
python verify7.py    # 디자인 · 섹션 배치 · 용어
python verify6.py    # Keyword 시트
python verify5.py    # 날짜 · 결측 · Overview · 열 너비
python smoke.py      # 환율 방향 · 통화 서식 · UI
```

`0d74c71` 기준 4개 스위트 전부 통과, 수식 2,588개 평가 실패 0, 색상 셀 최저 대비 5.05:1.

### B. 샘플 데이터 검증 (2026.07.07 ~ 08.06)

| 매체 | 고유 키워드 | PC / MO | 미매핑 | 그룹 간 중복 |
|---|---|---|---|---|
| Powerlink (Evergreen_PPC) | 551 | 269 / 282 | 0 | 0 |
| Brand Search | 93 | 35 / 58 | 0 | — |

Powerlink 광고그룹 8개(`PC/MO × Branded/Shoes/Competitors/General`) 전부 자동 추론 성공.

### C. 키워드 번역 보정

제공된 매핑 리스트에서 Generic 14개가 모두 `winter yoga wear`로 잘못 매핑돼 있어 개별 번역으로 보정했다. 리스트를 다시 받으면 같은 오류가 재발할 수 있다.

| KO | EN | KO | EN |
|---|---|---|---|
| 겨울헬스복 | Winter gym wear | 필라테스복세트 | Pilates outfit set |
| 트레이닝세트 | Training set | 겨울트레이닝세트 | Winter training set |
| 요가커버업 | Yoga cover-up | 겨울요가바지 | Winter yoga pants |
| 필라테스옷추천 | Recommended Pilates clothing | 겨울트레이닝복 | Winter training wear |
| 트레이닝복세트 | Training wear set | 츄리닝세트 | Tracksuit set |
| 여성헬스복 | Women's gym wear | 요가상의 | Yoga tops |
| 겨울트레이닝복세트 | Winter training wear set | 연예인요가복 | Celebrity yoga wear |

### D. 변경 이력

| 라운드 | 주요 변경 |
|---|---|
| 1 | 최초 PRD · 5-Sheet 구조 · 월별 환율 |
| 2 | Powerlink Keyword Group · Ad Group 정규화 |
| 3 | Overall Summary Report 형태 · Device Group 구분 · Keyword Spacer |
| 4 | 범용화 (Client / Campaign Name) · B2 시작 레이아웃 |
| 5 | 헤더 뒤 빈 행 · 단일 환율 · Agency Fee % |
| 6 | 입력 순서 개편 · 환율 From / To |
| 7 | Data Through Date 제거 · 전 기간 날짜 · 결측 빈 셀 · Overview PC/MO/Subtotal |
| 8 | Keyword 시트 Spent · CPC · TOTAL 상단 · Powerlink Budget 통화 |
| 9 | Brand Color 시스템 · 눈금선 제거 · 연회색 테두리 · Section 바로 아래 표 · Cost → Spent |
