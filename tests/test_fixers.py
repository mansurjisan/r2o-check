"""Tests for auto-fix functionality."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from r2o_check.cli import main
from r2o_check.fixers.structure import fix_missing_directories
from r2o_check.fixers.versions import fix_missing_version_files


class TestStructureFixers:
    def test_dry_run_proposes_fixes(self, tmp_path: Path) -> None:
        actions = fix_missing_directories(tmp_path, dry_run=True)
        assert len(actions) == 8
        assert all(not a.applied for a in actions)
        # Dirs should NOT be created in dry run.
        assert not (tmp_path / "ecf").exists()

    def test_apply_creates_dirs(self, tmp_path: Path) -> None:
        actions = fix_missing_directories(tmp_path, dry_run=False)
        assert len(actions) == 8
        assert all(a.applied for a in actions)
        for a in actions:
            assert a.path.is_dir()
            assert (a.path / ".gitkeep").exists()

    def test_idempotent(self, tmp_path: Path) -> None:
        fix_missing_directories(tmp_path, dry_run=False)
        # Second run: nothing to fix.
        actions = fix_missing_directories(tmp_path, dry_run=False)
        assert len(actions) == 0

    def test_partial_fix(self, tmp_path: Path) -> None:
        (tmp_path / "jobs").mkdir()
        (tmp_path / "scripts").mkdir()
        actions = fix_missing_directories(tmp_path, dry_run=False)
        assert len(actions) == 6  # 8 - 2 existing


class TestVersionsFixers:
    def test_dry_run_proposes(self, tmp_path: Path) -> None:
        actions = fix_missing_version_files(tmp_path, dry_run=True)
        assert len(actions) == 2
        assert all(not a.applied for a in actions)

    def test_apply_creates_files(self, tmp_path: Path) -> None:
        actions = fix_missing_version_files(tmp_path, dry_run=False)
        assert len(actions) == 2
        assert all(a.applied for a in actions)
        run_ver = tmp_path / "versions" / "run.ver"
        build_ver = tmp_path / "versions" / "build.ver"
        assert run_ver.is_file()
        assert build_ver.is_file()
        assert "export" in run_ver.read_text()

    def test_idempotent(self, tmp_path: Path) -> None:
        fix_missing_version_files(tmp_path, dry_run=False)
        actions = fix_missing_version_files(tmp_path, dry_run=False)
        assert len(actions) == 0

    def test_partial(self, tmp_path: Path) -> None:
        ver = tmp_path / "versions"
        ver.mkdir()
        (ver / "run.ver").write_text("export x_ver=1\n")
        actions = fix_missing_version_files(tmp_path, dry_run=False)
        assert len(actions) == 1
        assert actions[0].rule_id == "R2OVER002"


class TestFixCLI:
    def test_dry_run_default(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["fix", str(tmp_path)])
        assert result.exit_code == 0
        assert "WOULD FIX" in result.output
        assert "DRY RUN" in result.output

    def test_apply_flag(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(tmp_path), "--apply"]
        )
        assert result.exit_code == 0
        assert "APPLIED" in result.output
        assert (tmp_path / "ecf").is_dir()

    def test_nothing_to_fix(self) -> None:
        from pathlib import Path

        fixtures = Path(__file__).parent / "fixtures"
        compliant = fixtures / "compliant_minimal"
        runner = CliRunner()
        result = runner.invoke(main, ["fix", str(compliant)])
        assert result.exit_code == 0
        assert "Nothing to fix" in result.output
