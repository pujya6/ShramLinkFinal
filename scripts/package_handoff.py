"""Build a clean source ZIP from committed Git blobs, never from working files.

Usage: python scripts/package_handoff.py --output ../ShramLink-release-source.zip
The archive manifest records the exact base/final SHAs and changed paths.
"""

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

BASE_SHA = "0bea8e29aca12a2f48c08b9c748f6b7b6f127f33"
BLOCKED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "instance",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "test-results",
    ".DS_Store",
}
SECRET_PATTERNS = [
    rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    rb"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}",
    rb"\bxai-[A-Za-z0-9]{24,}",
    rb"\bAKIA[A-Z0-9]{16}\b",
]


def safe_path(name):
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and not BLOCKED_PARTS.intersection(path.parts)
        and not (path.name.startswith(".env") and path.name != ".env.example")
        and not re.search(r"cookie|credential|session|secret", path.name, re.I)
        and not re.search(
            r"\.(?:db|sqlite\d*|pyc|pyo|log|pem|key)(?:-|$)", path.name, re.I
        )
    )


def build_archive(root, ref, base, output):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)

    final = git("rev-parse", ref + "^{commit}").decode().strip()
    base = git("rev-parse", base + "^{commit}").decode().strip()
    changes = git("diff", "--name-status", base, final).decode().splitlines()
    entries, excluded = [], []
    for record in git("ls-tree", "-rz", "--full-tree", final).split(b"\0"):
        if not record:
            continue
        header, name = record.split(b"\t", 1)
        mode, kind, sha = header.decode().split()
        name = name.decode()
        if not safe_path(name):
            excluded.append(name)
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("Unsupported source entry: " + name)
        data = git("cat-file", "blob", sha)
        if any(re.search(pattern, data) for pattern in SECRET_PATTERNS):
            raise ValueError(
                "Potential credential detected in " + name + "; archive not created"
            )
        entries.append((name, data))
    manifest = dict(
        format="shramlink-source-handoff-v1",
        base_commit=base,
        final_commit=final,
        schema_changes_from_base="None; V3 schema and additive initializer retained",
        modified_files=changes,
        excluded_paths=excluded,
        files=[
            dict(path=name, sha256=hashlib.sha256(data).hexdigest())
            for name, data in entries
        ],
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr("ShramLink/" + name, data)
        archive.writestr(
            "ShramLink/HANDOFF_REVISION.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--base", default=BASE_SHA)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_archive(
        Path(__file__).resolve().parents[1], args.ref, args.base, args.output
    )
    print(
        f"Source archive: {args.output}; final commit: {result['final_commit']}; "
        f"files: {len(result['files'])}; excluded private paths: {len(result['excluded_paths'])}"
    )
