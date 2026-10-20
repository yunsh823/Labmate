"""Neighbourhood search over KMA's forecast locations (시·도 → 시·군·구 → 읍·면·동).

Typing broad-to-narrow narrows the list: "대구" lists everything in Daegu,
"대구 동구" only Dong-gu, "대구 동구 신천" the matching dong. Each word may be
partial, and provinces match their usual short forms ("경북", "충남").
"""

import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data" / "kma_places.json"

# Short display names; also searchable.
SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천",
    "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남", "전북특별자치도": "전북",
    "경상북도": "경북", "경상남도": "경남", "제주특별자치도": "제주", "전남광주통합특별시": "전남광주",
    "전라남도": "전남", "전라북도": "전북", "광주광역시": "광주", "강원도": "강원",
}


@lru_cache(maxsize=1)
def _places() -> list[tuple[str, tuple[str, ...], int, int]]:
    """(display name, searchable levels, nx, ny) in KMA's code order (a tree walk)."""
    out = []
    for code, l1, l2, l3, nx, ny, _lat, _lon in json.loads(DATA.read_text(encoding="utf-8"))["places"]:
        short = SHORT.get(l1, l1)
        levels = tuple(x for x in (f"{l1} {short}", l2, l3) if x)
        name = " ".join(x for x in (short, l2, l3) if x)
        out.append((name, levels, nx, ny))
    return out


def _match(tokens: list[str], levels: tuple[str, ...]) -> tuple[int, int] | None:
    """Words must hit levels in order (each word a later level).

    Returns a sort key, or None: words matching broader levels rank first, so "대구"
    lists Daegu city before 강진군 대구면; then whole-word prefixes before mid-word hits.
    """
    level, depth, prefix_hits = 0, 0, 0
    for t in tokens:
        while level < len(levels) and t not in levels[level]:
            level += 1
        if level == len(levels):
            return None
        depth += level
        prefix_hits += any(part.startswith(t) for part in levels[level].split())
        level += 1
    return depth, -prefix_hits


def search(query: str, limit: int = 80) -> tuple[list[dict], int]:
    tokens = query.split()
    if not tokens:
        return [], 0
    hits = []
    for i, (name, levels, nx, ny) in enumerate(_places()):
        key = _match(tokens, levels)
        if key is not None:
            hits.append((key, i, name))
    hits.sort()
    return [{"id": i, "name": name} for _, i, name in hits[:limit]], len(hits)


def get(place_id: int) -> tuple[str, int, int]:
    name, _levels, nx, ny = _places()[place_id]
    return name, nx, ny
