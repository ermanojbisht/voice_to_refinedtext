"""Unit and integration tests for ManualService and ManualViewer."""
import os
import tempfile
import pytest

from manual_service import ManualService


@pytest.fixture
def temp_manual_service(tmp_path):
    """Creates a ManualService backed by an isolated sample CONFIGURATION_GUIDE.md."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample_doc = (
        "# Sample User Guide\n\n"
        "Welcome to the sample manual.\n\n"
        "## 1. Quick-Start Hardware Presets\n"
        "### 1.1 Preset A\n"
        "```json\n"
        '{"SAMPLE_RATE": 16000}\n'
        "```\n\n"
        "> [!TIP]\n"
        "> Use RTX 3060 for fast latency.\n\n"
        "## 2. Core Voice Refiner Reference\n"
        "| Configuration Key | Type | Default |\n"
        "|---|---|---|\n"
        "| `SAMPLE_RATE` | `integer` | `16000` |\n\n"
        "## 9. Best Practice Matrix\n"
        "High accuracy speech profile.\n"
    )
    (docs_dir / "CONFIGURATION_GUIDE.md").write_text(sample_doc, encoding="utf-8")
    return ManualService(script_dir=str(tmp_path))


def test_manual_service_parses_chapters(temp_manual_service):
    chapters = temp_manual_service.get_chapters()
    assert len(chapters) == 3
    
    ch1 = chapters[0]
    assert ch1["id"] == 1
    assert ch1["title"] == "Quick-Start Hardware Presets"
    assert ch1["icon"] == "🚀"
    assert len(ch1["subsections"]) == 1
    assert ch1["subsections"][0]["title"] == "1.1 Preset A"

    ch2 = chapters[1]
    assert ch2["id"] == 2
    assert "Core Voice Refiner" in ch2["title"]
    assert ch2["icon"] == "⚙️"

    ch9 = chapters[2]
    assert ch9["id"] == 9
    assert ch9["icon"] == "⚡"


def test_manual_service_search(temp_manual_service):
    # Search for "RTX"
    results = temp_manual_service.search_manual("RTX")
    assert len(results) >= 1
    assert results[0]["id"] == 1

    # Search for "Refiner"
    results2 = temp_manual_service.search_manual("Refiner")
    assert any(r["id"] == 2 for r in results2)


def test_manual_service_html_generation(temp_manual_service):
    html_path = temp_manual_service.generate_html_manual(force=True)
    assert os.path.isfile(html_path)

    content = open(html_path, "r", encoding="utf-8").read()
    # Check that navigation links and cards exist
    assert "chapter-1" in content
    assert "chapter-2" in content
    assert "chapter-9" in content
    # Check that Catppuccin theme styling is present
    assert "--bg-base: #1e1e2e" in content
    # Check that callout transformation occurred
    assert 'class="callout callout-success"' in content
    assert "💡 TIP:" in content


def test_real_configuration_guide_parsing():
    """Verify the real docs/CONFIGURATION_GUIDE.md parses all 9 chapters cleanly."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = ManualService(script_dir=repo_root)
    chapters = service.get_chapters()
    assert len(chapters) == 9
    ids = [c["id"] for c in chapters]
    assert ids == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Verify best practice matrix chapter
    ch9 = chapters[8]
    assert ch9["id"] == 9
    assert "Speed + Accuracy" in ch9["title"]
    assert ch9["icon"] == "⚡"
