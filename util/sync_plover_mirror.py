"""
Sync the Plover plugin into its install-source repository (github.com/jf5pier/stenalgo-plover), data included.

The mirror holds the same layout as `plover_stenalgo/` here (`pyproject.toml`, `plover_stenalgo/`), PLUS the generated
package assets `plover_stenalgo/dictionaries/` (the stock dictionary and the expression data), which are gitignored in
this repository so that only the mirror stores those blobs. A `pip install git+<mirror url>` therefore gets a
consistent pair. The mirror's own `README.md` and `.gitignore` are left alone.

Steps: rerun the plugin export (vendored core + the fingerprint-checked asset copy), replace the mirror's package
files with this repository's, commit there with the source commit in the message. `--push` pushes the mirror.

Run: python -m util.sync_plover_mirror MIRROR_CLONE [--push]
     (clone once: git clone git@github-personnal:jf5pier/stenalgo-plover.git MIRROR_CLONE)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from util.export_plover_plugin import REPO, exportAssets, generate

PLUGIN = REPO / "plover_stenalgo"
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info", "build", "dist")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def sync(mirror: Path, push: bool = False) -> str:
    """Copy the package into `mirror` and commit; returns the commit sha, or '' when nothing changed."""
    if not (mirror / ".git").exists():
        raise FileNotFoundError(f"{mirror} is not a git clone of the mirror repository")
    if git(mirror, "status", "--porcelain"):
        raise RuntimeError(f"{mirror} has uncommitted changes")
    for path, text in generate().items():          # the vendored core must be current before it is copied
        path.write_text(text, encoding="utf-8")
    exportAssets()
    shutil.copyfile(PLUGIN / "pyproject.toml", mirror / "pyproject.toml")
    target = mirror / "plover_stenalgo"
    shutil.rmtree(target, ignore_errors=True)
    shutil.copytree(PLUGIN / "plover_stenalgo", target, ignore=IGNORED)
    git(mirror, "add", "-A")
    if not git(mirror, "status", "--porcelain"):
        return ""
    source = git(REPO, "rev-parse", "--short", "HEAD")
    dirty = " (+ uncommitted changes)" if git(REPO, "status", "--porcelain", "--untracked-files=no") else ""
    git(mirror, "commit", "-q", "-m", f"Sync from stenalgo {source}{dirty}: plugin code and packaged theory data\n\n"
        "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    if push:
        git(mirror, "push", "-q", "origin", "HEAD")
    return git(mirror, "rev-parse", "--short", "HEAD")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("mirror", type=Path, help="local clone of the stenalgo-plover repository")
    parser.add_argument("--push", action="store_true", help="push the mirror's new commit")
    args = parser.parse_args()
    sha = sync(args.mirror.resolve(), args.push)
    print(f"mirror commit {sha}{' (pushed)' if sha and args.push else ''}" if sha else "mirror already up to date")


if __name__ == "__main__":
    main()
