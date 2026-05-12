import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("SEOUL_API_KEY", "")
POI_CODES = [f"POI{str(i).zfill(3)}" for i in range(1, 122)]
KST = timezone(timedelta(hours=9))

os.makedirs("data", exist_ok=True)


def xml_to_dict(element):
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


async def collect_poi_async(session, poi_code, max_retry=3):
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/{poi_code}"
    collected_at = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    last_error = "알 수 없는 오류"

    for attempt in range(1, max_retry + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as res:
                content = await res.read()
                root = ET.fromstring(content)
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
            last_error = str(e)
            print(f"  ⚠️  {poi_code} 시도 {attempt}/{max_retry} 실패: {e}")
            if attempt < max_retry:
                await asyncio.sleep(3)

    return {
        "poi_code":     poi_code,
        "collected_at": collected_at,
        "status":       "error",
        "error":        last_error,
        "data":         {"CITYDATA": None}
    }


async def collect_all():
    async with aiohttp.ClientSession() as session:
        tasks = [collect_poi_async(session, poi) for poi in POI_CODES]
        results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        status = "✅" if result["status"] == "ok" else "❌"
        area_nm = ""
        try:
            area_nm = result["data"]["CITYDATA"]["AREA_NM"]
        except:
            pass
        print(f"[{i:3d}/121] {status} {result['poi_code']}  {area_nm}")

    return list(results)


# ── 전체 수집 ──────────────────────────────────────────
results = asyncio.run(collect_all())

print(f"\n완료: {sum(1 for r in results if r['status'] == 'ok')}개 성공")

# ── JSON 저장 ──────────────────────────────────────────
timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M")
filename = f"data/seoul_rtd_{timestamp}.json"

with open(filename, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"저장 완료: {filename}")
