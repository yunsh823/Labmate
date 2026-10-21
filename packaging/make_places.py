"""Regenerate labmate/data/kma_places.json from KMA's grid/lat-lon spreadsheet.

The spreadsheet ships inside the "오픈API활용가이드" zip on the data.go.kr page for
기상청_단기예보 조회서비스 (data 15084084). Run when KMA publishes a new version:

    python packaging/make_places.py <path to 격자_위경도.xlsx>
"""

import json
import sys
from pathlib import Path

import openpyxl

OUT = Path(__file__).resolve().parent.parent / "labmate" / "data" / "kma_places.json"


def main(xlsx: str) -> None:
    ws = openpyxl.load_workbook(xlsx, read_only=True).worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    col = {name: i for i, name in enumerate(header) if name}
    places = []
    for r in rows:
        if not r[col["1단계"]]:
            continue
        places.append([
            str(r[col["행정구역코드"]]),
            r[col["1단계"]], r[col["2단계"]] or "", r[col["3단계"]] or "",
            int(r[col["격자 X"]]), int(r[col["격자 Y"]]),
            round(float(r[col["위도(초/100)"]]), 6), round(float(r[col["경도(초/100)"]]), 6),
        ])
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "source": f"기상청 단기예보 조회서비스 오픈API 활용가이드 격자_위경도 ({Path(xlsx).name}, sheet {ws.title})",
        "fields": ["code", "level1", "level2", "level3", "nx", "ny", "lat", "lon"],
        "places": places,
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(places)} places -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])
