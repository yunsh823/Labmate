"""Daily paper alerts.

Two sources:
- Semantic Scholar recommendations from the user's seed papers (closest to
  Google Scholar's "related research" alerts).
- OpenAlex works from the last few days whose title/abstract match a keyword,
  optionally limited to chosen journals.

Results are merged, de-duplicated against everything already shown, optionally
stripped of preprints, and capped so a day's list stays readable.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

S2_RECOMMEND = "https://api.semanticscholar.org/recommendations/v1/papers"
OPENALEX = "https://api.openalex.org"
USER_AGENT = "Labmate desktop app (paper alerts)"
WINDOW_DAYS = 7
DAILY_CAP = 15
PREPRINT_VENUES = ("arxiv", "biorxiv", "medrxiv", "research square", "ssrn", "essoar", "ess open archive",
                   "eartharxiv", "preprints.org", "authorea", "egusphere")


class PaperError(Exception):
    """code: 'rate_limited' | 'network' | 'not_found'."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _get_json(url: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": USER_AGENT, **({"Content-Type": "application/json"} if data else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise PaperError({429: "rate_limited", 404: "not_found"}.get(e.code, "network")) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise PaperError("network") from None


# --- normalizing both sources into one shape ----------------------------------

def paper_key(doi: str | None, title: str) -> str:
    if doi:
        return doi.lower()
    return "t:" + re.sub(r"[^0-9a-z가-힣]+", "", title.lower())[:200]


def _is_preprint_venue(venue: str) -> bool:
    v = venue.lower()
    return any(p in v for p in PREPRINT_VENUES)


def from_semantic_scholar(p: dict) -> dict | None:
    title = (p.get("title") or "").strip()
    if not title or not p.get("publicationDate"):
        return None
    ids = p.get("externalIds") or {}
    doi = ids.get("DOI")
    venue = p.get("venue") or (p.get("journal") or {}).get("name") or ""
    authors = [a.get("name", "") for a in p.get("authors") or []]
    return {
        "key": paper_key(doi, title), "doi": doi, "title": title,
        "first_author": authors[0] if authors else "", "author_count": len(authors),
        "venue": venue, "pub_date": p["publicationDate"],
        "url": f"https://doi.org/{doi}" if doi else (p.get("url") or ""),
        "preprint": int((not doi and "ArXiv" in ids) or _is_preprint_venue(venue)),
        "reason_kind": "seed", "reason_value": "",
    }


def from_openalex(w: dict, reason_kind: str, reason_value: str) -> dict | None:
    title = (w.get("title") or w.get("display_name") or "").strip()
    if not title or not w.get("publication_date"):
        return None
    doi = (w.get("doi") or "").removeprefix("https://doi.org/") or None
    loc = w.get("primary_location") or {}
    source = loc.get("source") or {}
    authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships") or []]
    venue = source.get("display_name") or ""
    return {
        "key": paper_key(doi, title), "doi": doi, "title": title,
        "first_author": authors[0] if authors else "", "author_count": len(authors),
        "venue": venue, "pub_date": w["publication_date"],
        "url": f"https://doi.org/{doi}" if doi else (loc.get("landing_page_url") or w.get("id") or ""),
        "preprint": int(w.get("type") == "preprint" or source.get("type") == "repository" or _is_preprint_venue(venue)),
        "reason_kind": reason_kind, "reason_value": reason_value,
    }


# --- sources ------------------------------------------------------------------

def recommend(seed_dois: list[str], since: date) -> list[dict]:
    if not seed_dois:
        return []
    query = urllib.parse.urlencode({
        "fields": "title,authors,venue,journal,publicationDate,externalIds,url", "limit": 100})
    data = _get_json(f"{S2_RECOMMEND}?{query}", {"positivePaperIds": [f"DOI:{d}" for d in seed_dois]})
    papers = (from_semantic_scholar(p) for p in data.get("recommendedPapers", []))
    return [p for p in papers if p and p["pub_date"] >= since.isoformat()]


def search_openalex(keywords: list[str], journals: list[dict], since: date) -> list[dict]:
    """One query per keyword (within the chosen journals, if any); journals alone if no keywords."""
    # Papers only (no datasets, theses, ...); preprints are dropped later if the user excludes them.
    base = [f"from_publication_date:{since.isoformat()}", "type:article|review|letter|preprint"]
    if journals:
        base.append("primary_location.source.id:" + "|".join(j["id"] for j in journals))
    # Quoted: "atmospheric blocking" as a phrase, not either word anywhere in the abstract.
    clean = {kw: kw.replace(",", " ").replace('"', " ") for kw in keywords}
    queries = [(f'title_and_abstract.search:"{clean[kw]}"', "keyword", kw) for kw in keywords]
    if not keywords and journals:
        queries = [(None, "journal", ", ".join(j["name"] for j in journals))]
    out = []
    for extra, kind, value in queries:
        filters = ",".join(base + ([extra] if extra else []))
        query = urllib.parse.urlencode({"filter": filters, "sort": "publication_date:desc", "per-page": 25})
        data = _get_json(f"{OPENALEX}/works?{query}")
        out += [p for p in (from_openalex(w, kind, value) for w in data.get("results", [])) if p]
    return out


def lookup_title(doi: str) -> str:
    """Title for a seed DOI, so Settings can show what was added."""
    data = _get_json(f"{OPENALEX}/works/doi:{urllib.parse.quote(doi)}")
    return (data.get("title") or data.get("display_name") or "").strip()


def search_journals(query: str) -> list[dict]:
    q = urllib.parse.urlencode({"search": query, "filter": "type:journal", "per-page": 8})
    data = _get_json(f"{OPENALEX}/sources?{q}")
    return [{"id": s["id"].rsplit("/", 1)[-1], "name": s["display_name"]} for s in data.get("results", [])]


def normalize_doi(text: str) -> str | None:
    m = re.search(r"10\.\d{4,9}/\S+", text.strip())
    return m.group(0).rstrip(".,;)") if m else None


# --- choosing the day's list -----------------------------------------------------

def select(candidates: list[dict], known: set[str], include_preprints: bool, cap: int = DAILY_CAP) -> list[dict]:
    """Drop what was shown before, duplicates, and (optionally) preprints; then take turns
    between sources so one busy keyword can't crowd out the seed recommendations."""
    seen = set(known)
    groups: dict[tuple[str, str], list[dict]] = {}
    for p in sorted(candidates, key=lambda p: p["pub_date"], reverse=True):
        title_key = paper_key(None, p["title"])
        if p["key"] in seen or title_key in seen or (p["preprint"] and not include_preprints):
            continue
        seen.update((p["key"], title_key))
        groups.setdefault((p["reason_kind"], p["reason_value"]), []).append(p)
    picked, queues = [], list(groups.values())
    while queues and len(picked) < cap:
        for q in list(queues):
            if len(picked) >= cap:
                break
            picked.append(q.pop(0))
            if not q:
                queues.remove(q)
    return picked


def fetch(seed_dois: list[str], keywords: list[str], journals: list[dict], known: set[str],
          include_preprints: bool, today: date | None = None) -> tuple[list[dict], str | None]:
    """(papers to add, error code or None). One source failing doesn't sink the other."""
    since = (today or date.today()) - timedelta(days=WINDOW_DAYS)
    candidates, error = [], None
    for source in (lambda: recommend(seed_dois, since), lambda: search_openalex(keywords, journals, since)):
        try:
            candidates += source()
        except PaperError as e:
            error = e.code
    return select(candidates, known, include_preprints), error
