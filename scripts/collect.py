import requests
import xml.etree.ElementTree as ET
import json
import time
import os
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("SEOUL_API_KEY", "")
POI_CODES = [f"POI{str(i).zfill(3)}" for i in range(1, 122)]
KST = timezone(timedelta(hours=9))

os.makedirs("data", exist_ok=True)


def xml_to_dict(element):
    """XML 노드를 재귀적으로 dict로 변환"""
    result = {}

    children = list(element)
    if children:
        child_dict = {}
        for child in children:
            child_data = xml_to_dict(child)
            tag = child.tag

            if tag in child_dict:
                if not isinstance(child_dict[tag], list):
                    child_dict[tag] = [child_dict[tag]]
                child_dict[tag].append(child_data)
            else:
                child_dict[tag] = child_data
        result = child_dict

    if element.text and element.text.strip():
        if result:
            result["_text"] = element.text.strip()
        else:
            return element.text.strip()

    return result if result else None


def collect_poi(poi_code):
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/{poi_code}"
    collected_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    try:
        res = requests.get(url, timeout=15)
        root = ET.fromstring(res.content)
        data = xml_to_dict(root)

        if not data or "CITYDATA" not in data:
            raise ValueError("CITYDATA 없음")

        return {
            "poi_code":     poi_code,
            "collected_at": collected_at,
            "status":       "ok",
            "data":         data
        }

    except Exception as e:
        return {
            "poi_code":     poi_code,
            "collected_at": collected_at,
            "status":       "error",
            "error":        str(e),
            "data":         {"CITYDATA": None}
        }


# ── 전체 수집 ──────────────────────────────────────────
results = []

for i, poi in enumerate(POI_CODES, 1):
    result = collect_poi(poi)
    results.append(result)

    status = "✅" if result["status"] == "ok" else "❌"
    area_nm = ""
    try:
        area_nm = result["data"]["CITYDATA"]["AREA_NM"]
    except:
        pass
    print(f"[{i:3d}/121] {status} {poi}  {area_nm}")

    time.sleep(0.3)

print(f"\n완료: {sum(1 for r in results if r['status'] == 'ok')}개 성공")

# ── JSON 저장 (data/ 폴더에 타임스탬프 단위) ──────────
timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M")
filename = f"data/seoul_rtd_{timestamp}.json"

with open(filename, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"저장 완료: {filename}")
