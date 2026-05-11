# Seoul RTD Collector

서울 실시간 도시데이터(Seoul Real-Time Data)를 자동으로 수집하여 저장하는 파이프라인입니다.
EV 충전소 최적 입지 연구를 위한 데이터 수집 목적으로 구축되었습니다.

---

## 개요

서울시 열린데이터광장의 **서울 실시간 도시데이터 API**를 활용하여
서울 주요 121개 장소(POI)에 대한 실시간 데이터를 15분마다 자동 수집합니다.

수집 데이터는 `data/` 폴더에 타임스탬프 단위 JSON 파일로 저장됩니다.

---

## 수집 데이터 항목

| 분야 | 주요 항목 |
|---|---|
| 실시간 인구 | 혼잡도, 인구 최솟값·최댓값, 연령대별 비율, 예측 인구 |
| 도로·교통 | 평균 도로 속도, 소통 지수(원활/서행/정체), 사고·통제 현황 |
| 대중교통 | 지하철·버스 승하차 인원 (5분·10분·30분·누적) |
| 상권·카드 | 실시간 결제 건수·금액, 연령대별 소비 비율 |
| EV 충전소 | 충전기 상태(사용가능/충전중/고장), 출력(kW), 충전 타입 |
| 주차장 | 총 용량, 현재 가용 면수 |
| 날씨·환경 | 기온, 습도, 강수량, PM2.5, PM10, 자외선 지수 |
| 문화행사 | 행사명, 장소, 기간 |
| 따릉이 | 대여소별 가용 자전거 수 |

---

## 수집 대상 POI (121개소)

서울시 주요 방문지역 121곳 (POI001 ~ POI121)

| 구분 | 개수 |
|---|---|
| 고궁·문화유산 | 5 |
| 관광특구 | 7 |
| 공원 | 33 |
| 발달상권 | 28 |
| 인구밀집지역 (역세권 등) | 48 |

---

## 파이프라인 구조

```
서울 실시간 도시데이터 API (5분 갱신)
        ↓
GitHub Actions (15분마다 자동 실행)
        ↓
data/seoul_rtd_YYYYMMDD_HHMM.json
```

---

## 파일 구조

```
.
├── .github/
│   └── workflows/
│       └── collect_seoul_rtd.yml   # GitHub Actions 스케줄러
├── scripts/
│   └── collect.py                  # 수집 스크립트
├── data/
│   └── seoul_rtd_YYYYMMDD_HHMM.json  # 수집 결과 (자동 생성)
└── README.md
```

---

## 저장 형식

```json
[
  {
    "poi_code": "POI001",
    "collected_at": "2026-05-11 15:00:00",
    "status": "ok",
    "data": {
      "CITYDATA": {
        "AREA_NM": "강남 MICE 관광특구",
        "LIVE_PPLTN_STTS": { ... },
        "ROAD_TRAFFIC_STTS": { ... },
        "CHARGER_STTS": { ... },
        "WEATHER_STTS": { ... }
      }
    }
  }
]
```

- `status: "ok"` — 정상 수집
- `status: "error"` — API 오류 (CITYDATA: null)

---

## 실행 방법

### 자동 실행
GitHub Actions가 15분마다 자동으로 실행합니다.
Actions 탭 → Seoul RTD Collector → Run workflow로 수동 실행도 가능합니다.

### 로컬 실행

```bash
pip install requests
SEOUL_API_KEY=발급받은키 python scripts/collect.py
```

---

## API 키 발급

1. [서울 열린데이터광장](https://data.seoul.go.kr) 로그인
2. Open API → 인증키 신청
3. 서비스명: `서울 실시간 도시데이터` 검색 후 신청
4. 발급된 키를 GitHub Secrets에 `SEOUL_API_KEY`로 등록

---

## 데이터 활용 예시

```python
import json
import glob
import pandas as pd
from pandas import json_normalize

latest = sorted(glob.glob("data/seoul_rtd_*.json"))[-1]
with open(latest, encoding="utf-8") as f:
    results = json.load(f)

rows = []
for item in results:
    cd = item["data"]["CITYDATA"]
    if cd is None:
        rows.append({"poi_code": item["poi_code"], "collected_at": item["collected_at"]})
        continue
    row = json_normalize(cd, sep="_")
    row["poi_code"]     = item["poi_code"]
    row["collected_at"] = item["collected_at"]
    rows.append(row)

df = pd.concat(rows, ignore_index=True)
```

---

## 데이터 출처

- **서울 실시간 도시데이터**: 서울특별시 (https://data.seoul.go.kr/SeoulRtd/)
- 데이터 제공: KT·SKT(실시간 인구), 신한카드(상권), Tmoney(대중교통), 한국환경공단(EV충전소), 기상청(날씨)
- 이용 허락: 공공데이터 이용허락 표준라이선스 (출처 표시 조건)

---

## 연구 목적

본 데이터는 연구에 활용됩니다.
