from datetime import date

import pytest

from labmate import papers
from labmate.db import Store

TODAY = date(2026, 10, 20)


def s2(title, doi=None, date_="2026-10-18", venue="Journal of Climate", arxiv=None, authors=("Kim", "Lee")):
    ids = {k: v for k, v in (("DOI", doi), ("ArXiv", arxiv)) if v}
    return {"title": title, "externalIds": ids, "venue": venue, "publicationDate": date_,
            "authors": [{"name": a} for a in authors], "url": "https://www.semanticscholar.org/p/1"}


def oa(title, doi=None, date_="2026-10-17", venue="Geophysical Research Letters", type_="article", source_type="journal"):
    return {"title": title, "doi": f"https://doi.org/{doi}" if doi else None, "publication_date": date_,
            "type": type_, "primary_location": {"source": {"display_name": venue, "type": source_type}},
            "authorships": [{"author": {"display_name": "Park"}}]}


def test_normalizes_both_sources():
    a = papers.from_semantic_scholar(s2("Blocking and heat", doi="10.1/ABC"))
    assert a["key"] == "10.1/abc" and a["url"] == "https://doi.org/10.1/ABC"
    assert (a["first_author"], a["author_count"], a["preprint"]) == ("Kim", 2, 0)
    b = papers.from_openalex(oa("ERA5 heatwaves", doi="10.2/x"), "keyword", "heatwave")
    assert b["reason_kind"] == "keyword" and b["reason_value"] == "heatwave" and b["venue"] == "Geophysical Research Letters"
    assert papers.from_semantic_scholar(s2("No date", date_=None)) is None


def test_preprint_detection():
    assert papers.from_semantic_scholar(s2("arXiv only", arxiv="2610.1", venue="arXiv.org"))["preprint"] == 1
    assert papers.from_openalex(oa("RS", type_="preprint", venue="Research Square"), "keyword", "x")["preprint"] == 1
    assert papers.from_openalex(oa("Repo", source_type="repository", venue="Zenodo"), "keyword", "x")["preprint"] == 1
    assert papers.from_openalex(oa("Journal paper"), "keyword", "x")["preprint"] == 0


def cand(title, kind="keyword", value="k", doi=None, preprint=0, date_="2026-10-18"):
    return {"key": papers.paper_key(doi, title), "doi": doi, "title": title, "first_author": "", "author_count": 0,
            "venue": "", "pub_date": date_, "url": "", "preprint": preprint, "reason_kind": kind, "reason_value": value}


def test_select_drops_known_duplicates_and_preprints():
    c = [cand("Old one", doi="10.1/old"), cand("Same Title", doi="10.1/a"), cand("same title!"),  # title duplicate
         cand("Preprint", preprint=1), cand("Fresh", doi="10.1/b")]
    got = [p["title"] for p in papers.select(c, known={"10.1/old"}, include_preprints=False)]
    assert got == ["Same Title", "Fresh"]
    with_pre = [p["title"] for p in papers.select(c, known={"10.1/old"}, include_preprints=True)]
    assert "Preprint" in with_pre


def test_select_takes_turns_between_sources_and_caps():
    busy = [cand(f"kw {i}", value="busy") for i in range(30)]
    seeds = [cand(f"seed {i}", kind="seed", value="") for i in range(3)]
    got = papers.select(busy + seeds, set(), include_preprints=True, cap=10)
    assert len(got) == 10
    assert sum(p["reason_kind"] == "seed" for p in got) == 3  # not crowded out by the busy keyword


def test_one_source_failing_keeps_the_other(monkeypatch):
    def boom(*a):
        raise papers.PaperError("rate_limited")
    monkeypatch.setattr(papers, "recommend", boom)
    monkeypatch.setattr(papers, "search_openalex", lambda *a: [cand("From OpenAlex", doi="10.9/z")])
    got, error = papers.fetch(["10.1/seed"], ["heatwave"], [], set(), False, TODAY)
    assert [p["title"] for p in got] == ["From OpenAlex"] and error == "rate_limited"


def test_openalex_queries_per_keyword_within_journals(monkeypatch):
    urls = []
    monkeypatch.setattr(papers, "_get_json", lambda url, body=None: urls.append(url) or {"results": []})
    papers.search_openalex(["blocking", "heat, wave"], [{"id": "S1", "name": "J Clim"}], TODAY)
    assert len(urls) == 2
    assert all("primary_location.source.id%3AS1" in u and "from_publication_date%3A2026-10-20" in u for u in urls)
    assert "title_and_abstract.search%3A%22heat++wave%22" in urls[1]  # phrase; comma would break the filter syntax
    assert all("type%3Aarticle%7Creview%7Cletter%7Cpreprint" in u for u in urls)  # papers only


def test_normalize_doi():
    assert papers.normalize_doi("https://doi.org/10.1175/JCLI-D-17-0034.1") == "10.1175/JCLI-D-17-0034.1"
    assert papers.normalize_doi("doi: 10.1029/2020GL089999.") == "10.1029/2020GL089999"
    assert papers.normalize_doi("not a doi") is None


def test_store_add_list_and_status(tmp_path):
    store = Store(tmp_path / "t.db")
    p = cand("Paper", doi="10.1/p")
    assert store.add_papers([p, p]) == 1  # second insert ignored
    assert store.count_new_papers() == 1 and store.paper_keys() == {"10.1/p"}
    store.mark_papers_seen()
    assert store.count_new_papers() == 0
    store.set_paper_status("10.1/p", "hidden")
    assert store.list_papers() == []
