from labmate import places


def names(query, limit=5000):
    return [r["name"] for r in places.search(query, limit)[0]]


def test_broad_query_lists_everything_in_the_city():
    got = names("대구")
    city = [n for n in got if n.startswith("대구")]
    assert "대구 동구 신천3동" in city and any(n.startswith("대구 북구 ") for n in city) and len(city) > 100
    # 강진군 대구면 also contains "대구" but ranks after every Daegu city entry
    others = [n for n in got if not n.startswith("대구")]
    assert others and got[:len(city)] == city


def test_adding_a_district_narrows_to_it():
    got = names("대구 동구")
    assert "대구 동구 신천3동" in got
    assert all(n.startswith("대구 동구") for n in got)


def test_partial_words_at_each_level():
    assert "대구 동구 신천3동" in names("대구 동 신천")
    assert "대구 동구 신천3동" in names("신천3")
    assert names("대구 동구 신천3동") == ["대구 동구 신천3동"]


def test_province_short_forms_and_merged_city():
    assert any(n.startswith("경북 포항시") for n in names("경북 포항"))
    assert any(n.startswith("충남") for n in names("충남"))
    gwangju = names("광주")
    assert any(n.startswith("전남광주") for n in gwangju)  # 2026 merger still found by the old name


def test_words_must_follow_the_hierarchy_order():
    assert names("동구 대구") == []  # district before city does not match


def test_result_limit_reports_total():
    results, total = places.search("서울", limit=10)
    assert len(results) == 10 and total > 400


def test_get_returns_official_grid():
    rid = places.search("대구 동구 신천3동")[0][0]["id"]
    assert places.get(rid) == ("대구 동구 신천3동", 89, 91)
