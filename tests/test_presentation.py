from ioassistant import presentation


def test_presentation_renders_clickable_agents_and_steps(tmp_path):
    html = presentation.render()
    for name, *_ in presentation.AGENTS:
        assert name in html
    assert html.count("class='agent'") == len(presentation.AGENTS) == 8
    assert html.count("class='node'") == len(presentation.STEPS) == 8
    assert "id='prev'" in html and "id='next'" in html and "@font-face" in html
    assert "#FFFFFF" not in html.upper() and "#000000" not in html


def test_presentation_build_writes_file(tmp_path):
    out = presentation.build(tmp_path / "p.html")
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")
