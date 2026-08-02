"""Parse TLDR newsletter markdown into one chunk per story.

The newsletters have a rigid, verified structure (see
docs/superpowers/specs/2026-08-01-tldr-search-design.md section 4), so this
is a parser, not a heuristic extractor:

    <headline line>
    [TLDR](/) [Newsletters](/newsletters) [Advertise](...)   <- masthead
    # TLDR <Category> <date>                                 <- H1
    ## <headline repeated>                                   <- H2 #1
    ### <Section name>                                       <- section label
    [### <Story title> (N minute read)](<url>)               <- story boundary
    <body paragraphs>
    ## <tagline>                                              <- H2 #2 = footer
    Subscribe / Join N readers / Privacy|Careers / Timestamp  <- footer junk

Verified across a 200-file sample: every file has exactly two `## `
headings, and exactly one of them follows the first story — that second one
is the footer boundary, so everything after it is dropped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

STORY_RE = re.compile(r"^\[###\s*(?P<title>.*?)\]\((?P<url>\S+?)\)\s*$")
SECTION_RE = re.compile(r"^###\s*(?P<name>.*)$")
H2_RE = re.compile(r"^##\s+")
H1_RE = re.compile(r"^#\s+")
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((?:[^)]*)\)")
READ_TIME_RE = re.compile(r"\s*\((?:\d+\s*minute\s*read|GitHub Repo)[^)]*\)\s*$", re.I)
BULLET_RE = re.compile(r"^[*\-]\s+")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

# Emoji + pictographs + variation selectors + dingbats. Decorative in this
# corpus (30% of bodies carry them) and they tokenize to 2-4 tokens each.
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "\U0000200D"
    "]+"
)

# Params that are pure tracking noise. Anything else on the URL is kept.
TRACKING_PREFIXES = ("utm_", "sfcampaign_", "mc_", "_hs")
TRACKING_KEYS = {"ref", "source", "campaign_id"}

SPONSOR_MARKERS = ("(sponsor)", "(sponsored)")

# Stories that link here are TLDR self-promotion (hiring posts, "advertise
# with us"), not editorial content. They don't carry a (Sponsor) tag, so the
# SPONSOR_MARKERS check alone misses these.
JUNK_HOSTS = (
    "advertise.tldr.tech",
    "jobs.ashbyhq.com",
    "refer.tldr.tech",
    "tldr.tech/privacy",
    "tldr.tech/advertise",
    "/api/latest/",
)

# 168 corpus-wide. Some route through jobs.ashbyhq.com (caught above), others
# through a bare `mailto:` link, which has no host to denylist. Title text is
# the one signal both forms share.
JUNK_TITLE_MARKERS = ("tldr is hiring",)


@dataclass
class Chunk:
    id: str
    category: str
    date: str
    year_month: str
    section: str
    title: str
    url: str
    source_host: str
    raw_markdown: str
    words: int


def _strip_tracking_params(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    keep = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith(TRACKING_PREFIXES) and k.lower() not in TRACKING_KEYS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(keep), parts.fragment))


def _source_host(url: str) -> str:
    try:
        host = urlsplit(url).netloc
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _normalize(text: str) -> str:
    """Rules 5-9 from the spec: flatten links, unescape entities, strip
    emoji, strip bullets, collapse all whitespace to single spaces."""
    text = MD_LINK_RE.sub(r"\1", text)
    text = text.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
    text = EMOJI_RE.sub("", text)
    text = BULLET_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_junk(title: str, url: str, section: str) -> bool:
    hay = f"{title} {section}".lower()
    if any(m in hay for m in SPONSOR_MARKERS) or any(m in hay for m in JUNK_TITLE_MARKERS):
        return True
    return any(h in url for h in JUNK_HOSTS)


def parse_file(path: Path) -> list[Chunk]:
    """Parse one newsletter markdown file into its story chunks."""
    category = path.parent.name
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()

    date_match = DATE_RE.search(path.stem) or DATE_RE.search(raw)
    date = date_match.group(1) if date_match else ""
    year_month = date[:7] if date else ""

    chunks: list[Chunk] = []
    section = ""
    seen_story = False
    cur: dict | None = None
    body: list[str] = []

    def flush() -> None:
        nonlocal cur, body
        if cur is not None:
            text = _normalize(" ".join(body))
            title = cur["title"]
            if text and not _is_junk(title, cur["url"], cur["section"]):
                combined = f"{title} {text}"
                chunks.append(
                    Chunk(
                        id=f"{category}/{date}#{len(chunks)}",
                        category=category,
                        date=date,
                        year_month=year_month,
                        section=cur["section"],
                        title=title,
                        url=cur["url"],
                        source_host=_source_host(cur["url"]),
                        raw_markdown=combined,
                        words=len(combined.split()),
                    )
                )
        cur, body = None, []

    for line in lines:
        s = line.strip()
        if not s:
            continue

        m = STORY_RE.match(s)
        if m:
            flush()
            seen_story = True
            cur = {
                "title": _normalize(READ_TIME_RE.sub("", m.group("title"))),
                "url": _strip_tracking_params(m.group("url").replace("&amp;", "&")),
                "section": section,
            }
            continue

        # The second H2 (the one after the first story) starts the footer.
        if H2_RE.match(s) and seen_story:
            break
        if H2_RE.match(s) or H1_RE.match(s):
            continue

        m = SECTION_RE.match(s)
        if m and not s.startswith("[###"):
            flush()
            section = _normalize(m.group("name"))
            continue

        if cur is not None:
            body.append(s)

    flush()

    # Drop stories with no body (parse artifacts) and de-dup reposts within
    # this single issue by normalized URL.
    out, seen_urls = [], set()
    for c in chunks:
        key = c.url.rstrip("/")
        if not c.raw_markdown.strip() or key in seen_urls:
            continue
        seen_urls.add(key)
        out.append(c)
    return out


def dedup_global(chunks: list[Chunk]) -> list[Chunk]:
    """Drop reposts across categories/issues by normalized URL + lowercased
    title (rule 11). ~2.9% of stories in the full corpus, mostly ads already
    removed by the junk-host filter."""
    seen: set[tuple[str, str]] = set()
    out: list[Chunk] = []
    for c in chunks:
        key = (c.url.rstrip("/"), c.title.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def chunk_dict(c: Chunk) -> dict:
    return asdict(c)
