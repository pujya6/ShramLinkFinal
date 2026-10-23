"""Source packaging must exclude private runtime files and use committed content."""

import json
import subprocess
import zipfile

import pytest

from scripts.package_handoff import build_archive, safe_path


def test_private_paths_are_excluded():
    for name in [
        ".env",
        ".env.production",
        "instance/demo.sqlite3",
        "user.db-wal",
        "cookies.txt",
        "session.json",
        ".venv/bin/python",
        "__pycache__/x.pyc",
        "test-results/page.png",
        "private.key",
        "credentials.json",
        "../escape",
    ]:
        assert not safe_path(name), name
    for name in [
        ".env.example",
        "app/security.py",
        "app/models/__init__.py",
        "tests/test_security_and_setup.py",
    ]:
        assert safe_path(name), name


def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for args in [
        ["init", "-q"],
        ["config", "user.name", "Synthetic packaging test"],
        ["config", "user.email", "package@example.invalid"],
    ]:
        subprocess.run(["git", *args], cwd=root, check=True)
    return root


def commit(root):
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "Synthetic test"], cwd=root, check=True)


def test_archive_uses_committed_source_and_exact_revision(tmp_path):
    root = repository(tmp_path)
    (root / "README.md").write_text("committed source")
    (root / ".env").write_text("synthetic private configuration")
    (root / "private.db").write_bytes(b"synthetic database")
    commit(root)
    (root / "README.md").write_text("uncommitted changes")
    (root / "working-only.txt").write_text("must not appear")
    output = tmp_path / "source.zip"
    result = build_archive(root, "HEAD", "HEAD", output)
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {
            "ShramLink/README.md",
            "ShramLink/HANDOFF_REVISION.json",
        }
        assert archive.read("ShramLink/README.md") == b"committed source"
        manifest = json.loads(archive.read("ShramLink/HANDOFF_REVISION.json"))
        assert manifest["final_commit"] == result["base_commit"]
        assert sorted(manifest["excluded_paths"]) == [".env", "private.db"]


def test_archive_rejects_credential_pattern_without_creating_zip(tmp_path):
    root = repository(tmp_path)
    (root / "config.txt").write_text("xai-" + "x" * 32)  # synthetic scanner canary
    commit(root)
    output = tmp_path / "source.zip"
    with pytest.raises(ValueError, match="Potential credential"):
        build_archive(root, "HEAD", "HEAD", output)
    assert not output.exists()
