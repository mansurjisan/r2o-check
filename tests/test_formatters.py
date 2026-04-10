"""Tests for output formatters."""

from __future__ import annotations

import json
from pathlib import Path

from r2o_check.config import Config
from r2o_check.engine import LintResult, LintRunner
from r2o_check.formatters.html import format_results_html
from r2o_check.formatters.json_report import format_results_json
from r2o_check.formatters.markdown import format_results_markdown

FIXTURES = Path(__file__).parent / "fixtures"
RRFS = FIXTURES / "rrfs_style"


def _sample_results() -> tuple[list[LintResult], Config]:
    config = Config()
    runner = LintRunner(RRFS, config)
    return runner.run(), config


class TestJsonFormatter:
    def test_valid_json(self) -> None:
        results, config = _sample_results()
        text = format_results_json(results, config)
        data = json.loads(text)
        assert "version" in data
        assert "summary" in data
        assert "results" in data

    def test_schema_fields(self) -> None:
        results, config = _sample_results()
        data = json.loads(format_results_json(results, config))
        assert data["repo_type"] == "operational_model"
        assert data["summary"]["total"] == len(results)
        first = data["results"][0]
        assert "rule_id" in first
        assert "status" in first
        assert "message" in first

    def test_empty_results(self) -> None:
        config = Config()
        text = format_results_json([], config)
        data = json.loads(text)
        assert data["summary"]["total"] == 0
        assert data["results"] == []


class TestMarkdownFormatter:
    def test_has_summary_table(self) -> None:
        results, config = _sample_results()
        md = format_results_markdown(results, config)
        assert "| \u2705 Pass" in md
        assert "r2o-check lint results" in md

    def test_has_collapsible_sections(self) -> None:
        results, config = _sample_results()
        # Default mode hides passes; use include_passes
        md = format_results_markdown(
            results, config, include_passes=True
        )
        assert "<details" in md
        assert "</details>" in md

    def test_default_hides_passes(self) -> None:
        results, config = _sample_results()
        md = format_results_markdown(results, config)
        assert "rules passed" in md

    def test_has_footer(self) -> None:
        results, config = _sample_results()
        md = format_results_markdown(results, config)
        assert "r2o-check" in md
        assert "repo_type" in md

    def test_empty_results(self) -> None:
        config = Config()
        md = format_results_markdown([], config)
        assert "r2o-check lint results" in md


class TestHtmlFormatter:
    def test_valid_html(self) -> None:
        results, config = _sample_results()
        html = format_results_html(results, config)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html
        assert "<style>" in html

    def test_has_summary(self) -> None:
        results, config = _sample_results()
        html = format_results_html(results, config)
        assert "passed" in html
        assert "warnings" in html

    def test_has_table_rows(self) -> None:
        results, config = _sample_results()
        html = format_results_html(results, config)
        assert "<tr" in html
        assert "R2O" in html

    def test_self_contained(self) -> None:
        """No external CSS/JS references."""
        results, config = _sample_results()
        html = format_results_html(results, config)
        assert "http" not in html.split("<style>")[0]

    def test_empty_results(self) -> None:
        config = Config()
        html = format_results_html([], config)
        assert "<!DOCTYPE html>" in html
