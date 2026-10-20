"""Tests for Unified PEP 621 pyproject.toml and Dependency Packaging.

Verifies:
- pyproject.toml is syntactically valid and PEP 621 compliant
- No rigid '==' pins exist that would break on Ubuntu 22.04 (Python 3.10) vs Ubuntu 26.04 (Python 3.14)
- All declared console scripts and entry points resolve to callable functions
- Optional extras ([all], [gpu], [gui], [docs], [test]) are correctly structured
- requirements.txt acts as a backwards-compatible shim pointing to pyproject.toml
"""
import os
import tomllib
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).parent.parent


def test_pyproject_toml_parses_valid_toml():
    """Verifies that pyproject.toml exists and parses cleanly."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist at repo root"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    assert "project" in data
    assert data["project"]["name"] == "voice-to-refinedtext"
    assert data["project"]["version"] == "0.2.0"
    assert data["project"]["requires-python"] == ">=3.10"


def test_no_obsolete_strict_version_pins():
    """Verifies no rigid '==' pins in main dependencies (to ensure multi-Ubuntu compatibility)."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = data["project"].get("dependencies", [])
    assert len(deps) > 0, "Main dependencies must not be empty"

    for dep in deps:
        # Check package version specifier (before any environment marker ';')
        pkg_spec = dep.split(";")[0].strip()
        assert "==" not in pkg_spec, f"Rigid version pin '==' found in core dependency: '{pkg_spec}'. Use '>=' for multi-OS support."


def test_optional_extras_definitions():
    """Verifies standard extras [all], [gpu], [gui], [docs], [test] exist."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    extras = data["project"].get("optional-dependencies", {})
    expected_extras = ["gpu", "vulkan", "gui", "docs", "test", "all"]
    for extra in expected_extras:
        assert extra in extras, f"Missing optional extra: [{extra}]"

    # 'all' must bundle the other extras
    all_extra = extras["all"]
    assert any("voice-to-refinedtext[" in item for item in all_extra)


def test_entry_points_are_importable_and_callable():
    """Verifies that all CLI entry points in pyproject.toml point to callable functions."""
    pyproject_path = REPO_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    scripts = data["project"].get("scripts", {})
    assert "voice-refiner" in scripts
    assert "voice-doctor" in scripts
    assert "audio2idea" in scripts

    for cmd, entry_str in scripts.items():
        mod_name, func_name = entry_str.split(":")
        mod = __import__(mod_name, fromlist=[func_name])
        func = getattr(mod, func_name)
        assert callable(func), f"Entry point '{cmd}' ({entry_str}) is not callable"

    gui_scripts = data["project"].get("gui-scripts", {})
    assert "audio2idea-gui" in gui_scripts
    mod_name, func_name = gui_scripts["audio2idea-gui"].split(":")
    mod = __import__(mod_name, fromlist=[func_name])
    func = getattr(mod, func_name)
    assert callable(func)


def test_requirements_txt_shim():
    """Verifies requirements.txt exists and acts as a backwards-compatible PEP 621 shim."""
    req_path = REPO_ROOT / "requirements.txt"
    assert req_path.is_file(), "requirements.txt must exist for backwards compatibility"

    content = req_path.read_text(encoding="utf-8")
    assert "-e .[all]" in content
