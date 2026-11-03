from pathlib import Path

from ioassistant import cli, releaselog

CHANGELOG = """# Changelog

Intro text that is not a release.

## [0.6.0] - in development

### Added
- Not deployed yet.

## [0.5.13] - 2026-11-03

### Changed
- Transcripts: the primary source is the `meetingTranscriptUrl` of <each> day &
  the rest wraps onto a second line.

### Added
- A **bold** line with a [link](https://example.com/a?x=1&y=2).

## [0.5.12] - 2026-11-02

### Fixed
- Old fix.
"""


def test_parse_keeps_only_released_versions():
    releases = releaselog.parse(CHANGELOG)
    assert [(r["version"], r["date"]) for r in releases] == [("0.5.13", "2026-11-03"), ("0.5.12", "2026-11-02")]
    changed = releases[0]["categories"][0]
    assert changed[0] == "Changed" and len(changed[1]) == 1
    assert changed[1][0].endswith("the rest wraps onto a second line.")  # wrapped bullet joined


def test_render_table_escapes_and_orders():
    html = releaselog.render(releaselog.parse(CHANGELOG))
    assert html.startswith("<h2>RELEASE LOG</h2>")
    assert "0.6.0" not in html and "Not deployed" not in html
    assert html.index("0.5.13") < html.index("0.5.12")
    assert "<code>meetingTranscriptUrl</code>" in html and "&lt;each&gt;" in html and "&amp;" in html
    assert "<strong>bold</strong>" in html
    assert '<a href="https://example.com/a?x=1&amp;y=2">link</a>' in html


def test_render_without_releases():
    assert "No released versions yet." in releaselog.render([])


def test_merge_appends_then_replaces_in_place():
    section_old = releaselog.render(releaselog.parse("## [0.5.12] - 2026-11-02\n### Fixed\n- Old fix.\n"))
    section_new = releaselog.render(releaselog.parse(CHANGELOG))
    page = "<h1>Project</h1><p>Intro</p>"
    once = releaselog.merge(page, section_old)
    assert once.startswith(page) and once.endswith(section_old)
    twice = releaselog.merge(once, section_new)
    assert twice == page + section_new  # replaced, not duplicated
    assert releaselog.merge(twice, section_new) == twice  # idempotent


def test_merge_keeps_content_after_the_section():
    section = releaselog.render(releaselog.parse(CHANGELOG))
    page = "<h2>A</h2><p>a</p><h2 id=\"x\"><strong>Release&nbsp;Log</strong></h2><p>old</p><h2>After</h2><p>kept</p>"
    merged = releaselog.merge(page, section)
    assert merged == "<h2>A</h2><p>a</p>" + section + "<h2>After</h2><p>kept</p>"


def test_cli_release_log_merges_into_page_body(tmp_path, capsys):
    changelog, body, out = tmp_path / "CHANGELOG.md", tmp_path / "page.xhtml", tmp_path / "after.xhtml"
    changelog.write_text(CHANGELOG, encoding="utf-8")
    body.write_text("<p>Existing page</p>", encoding="utf-8")
    cli.main(["release-log", str(changelog), "--page-body", str(body), "--out", str(out)])
    assert Path(capsys.readouterr().out.strip()) == out
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<p>Existing page</p><h2>RELEASE LOG</h2>") and "0.5.13" in text
