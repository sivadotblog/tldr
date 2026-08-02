from pathlib import Path

import pytest

from tldr_embeddings.chunker import parse_file, dedup_global

FIXTURES = Path(__file__).parent / "fixtures"

FIXTURE_FILES = [
    FIXTURES / "ai" / "2025-09-29.md",
    FIXTURES / "infosec" / "2026-02-10.md",
    FIXTURES / "data" / "2026-01-15.md",
]


@pytest.fixture(params=FIXTURE_FILES, ids=lambda p: f"{p.parent.name}/{p.name}")
def chunks(request):
    return parse_file(request.param)


def test_produces_chunks(chunks):
    assert len(chunks) > 0


def test_category_and_date_from_path(chunks):
    for c in chunks:
        assert c.category in {"ai", "infosec", "data"}
        assert len(c.date) == 10 and c.date[4] == "-" and c.date[7] == "-"
        assert c.year_month == c.date[:7]


def test_ids_are_unique_and_ordinal(chunks):
    ids = [c.id for c in chunks]
    assert len(ids) == len(set(ids))
    for i, c in enumerate(chunks):
        assert c.id == f"{c.category}/{c.date}#{i}"


# --- footer / masthead exclusion -------------------------------------------

FOOTER_STRINGS = [
    "Join 620,000 readers",
    "Join 400,000 readers",
    "Join 410,000 readers",
    "Privacy",
    "Careers",
    "Timestamp:",
    "Subscribe",
]

MASTHEAD_STRINGS = [
    "[TLDR](/)",
    "[Newsletters](/newsletters)",
    "[Advertise](https://advertise.tldr.tech/)",
]


def test_no_footer_leakage(chunks):
    for c in chunks:
        for junk in FOOTER_STRINGS:
            assert junk not in c.raw_markdown, f"footer text leaked into chunk {c.id}: {junk!r}"


def test_no_masthead_leakage(chunks):
    for c in chunks:
        for junk in MASTHEAD_STRINGS:
            assert junk not in c.raw_markdown


def test_no_timestamp_epoch_leakage(chunks):
    # the trailing "Timestamp: 1759191974" line must never survive into a chunk
    for c in chunks:
        assert not any(tok.isdigit() and len(tok) == 10 for tok in c.raw_markdown.split())


# --- sponsor / ad exclusion --------------------------------------------------


def test_sponsor_tagged_stories_excluded(chunks):
    for c in chunks:
        assert "(sponsor" not in c.title.lower()


def test_junk_host_stories_excluded(chunks):
    junk_hosts = ("advertise.tldr.tech", "jobs.ashbyhq.com", "refer.tldr.tech")
    for c in chunks:
        assert not any(h in c.url for h in junk_hosts)


def test_infosec_fixture_drops_known_sponsor(chunks):
    # infosec/2026-02-10.md has a Flashpoint (Sponsor) story in the fixture;
    # confirm it never appears.
    titles = " ".join(c.title for c in chunks)
    assert "Dark Side of AI" not in titles


# --- text normalization -------------------------------------------------------


def test_no_markdown_links_remain(chunks):
    for c in chunks:
        assert "](" not in c.raw_markdown
        assert "](" not in c.title


def test_no_emoji_remain(chunks):
    import re

    emoji_re = re.compile(
        "["
        "\U0001F300-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+"
    )
    for c in chunks:
        assert not emoji_re.search(c.raw_markdown), c.raw_markdown
        assert not emoji_re.search(c.title), c.title


def test_single_line_no_newlines(chunks):
    for c in chunks:
        assert "\n" not in c.raw_markdown
        assert "\r" not in c.raw_markdown
        assert "  " not in c.raw_markdown  # no double-spaces from collapsing


def test_urls_stripped_of_tracking_params(chunks):
    for c in chunks:
        assert "utm_" not in c.url
        assert "sfcampaign_" not in c.url


def test_html_entities_unescaped(chunks):
    for c in chunks:
        assert "&amp;" not in c.raw_markdown
        assert "&amp;" not in c.url


def test_source_host_derived(chunks):
    for c in chunks:
        if c.url:
            assert c.source_host
            assert not c.source_host.startswith("www.")


# --- known-good content survives ---------------------------------------------


def test_ai_fixture_has_expected_story():
    chunks = parse_file(FIXTURES / "ai" / "2025-09-29.md")
    titles = " ".join(c.title for c in chunks)
    assert "Veritas" in titles


def test_data_fixture_has_expected_story():
    chunks = parse_file(FIXTURES / "data" / "2026-01-15.md")
    text = " ".join(c.raw_markdown for c in chunks)
    assert "Vinted" in text


def test_infosec_fixture_has_expected_story():
    chunks = parse_file(FIXTURES / "infosec" / "2026-02-10.md")
    titles = " ".join(c.title for c in chunks)
    assert "UNC3886" in titles or "Singapore" in titles


# --- idempotency ---------------------------------------------------------------


def test_reparsing_same_file_is_identical():
    a = parse_file(FIXTURES / "ai" / "2025-09-29.md")
    b = parse_file(FIXTURES / "ai" / "2025-09-29.md")
    assert [c.id for c in a] == [c.id for c in b]
    assert [c.raw_markdown for c in a] == [c.raw_markdown for c in b]


# --- global dedup -------------------------------------------------------------


def test_dedup_global_removes_repeated_url():
    a = parse_file(FIXTURES / "ai" / "2025-09-29.md")
    doubled = a + a  # simulate the same story appearing in two categories
    deduped = dedup_global(doubled)
    assert len(deduped) == len(a)
