"""Packages a layout solve for a remote machine: one tar.gz holding only what the solve needs (docs/PHONOLOGY_REWRITE_NEXT_SESSION.md section 6).

Run: python -m util.package_remote_solve --statistics LayoutStatistics.pickle [--output FILE.tar.gz]   (from the repo root)
Contents: the statistics file, the seed layout starboard3h.json, the `src/` modules that `util.optimize_keyboard` and `util.merge_layouts` really
import (found by importing them, not listed by hand), the two commands, requirements-remote.txt (the pins of requirements.txt for what the solve imports:
ortools, rich, tqdm), run_remote.sh and a MANIFEST.json (md5 of every file, the git commit, what the statistics were built from).
On the remote machine:
    tar xzf PACKAGE && cd remote_solve && python3 -m venv venv && venv/bin/pip install -r requirements-remote.txt
    PYTHON=venv/bin/python ./run_remote.sh 21600        # 6 h per part; WORKERS_* , SEED, OUT override the defaults, see the script
    -> result/merged.json (+ per-part layouts, incumbents, reports). Copy `result/` back; adopt a layout deliberately (cp to starboard3h.json).
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
from typing import Any

SEED_PATH = "starboard3h.json"
COMMANDS = ("util.optimize_keyboard", "util.merge_layouts")
REQUIRED_PACKAGES = ("ortools", "rich", "tqdm")
ROOT = "remote_solve"

RUN_SCRIPT = """#!/bin/bash
# Layout solve, one process per syllabic part, then the merge. Usage: ./run_remote.sh [SECONDS_PER_PART]   (default 3600)
# Environment: PYTHON (default python3), SEED (default 1), OUT (default result), STATISTICS (default LayoutStatistics.pickle),
#              WORKERS_ONSET / WORKERS_CODA / WORKERS_NUCLEUS (default: the cores split 5:5:2), SEED_LAYOUT (the hint layout, default starboard3h.json).
# After a crash the files in $OUT/incumbents ARE the result (best solution so far per part); combine them with util.merge_layouts. A rerun does NOT
# continue from them (CP-SAT takes a hint as a suggestion only), so use a new OUT and keep the old one.
set -u
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"; SEED="${SEED:-1}"; OUT="${OUT:-result}"; STATISTICS="${STATISTICS:-LayoutStatistics.pickle}"
SEED_LAYOUT="${SEED_LAYOUT:-starboard3h.json}"
TIME="${1:-3600}"
CORES="$(nproc)"
WORKERS_ONSET="${WORKERS_ONSET:-$(( CORES * 5 / 12 ))}"; WORKERS_CODA="${WORKERS_CODA:-$(( CORES * 5 / 12 ))}"
WORKERS_NUCLEUS="${WORKERS_NUCLEUS:-$(( CORES - WORKERS_ONSET - WORKERS_CODA ))}"
md5sum -c --quiet MANIFEST.md5 || { echo "MANIFEST.md5 check failed: the package is damaged"; exit 1; }
mkdir -p "$OUT/incumbents"
echo "cores $CORES, workers onset $WORKERS_ONSET coda $WORKERS_CODA nucleus $WORKERS_NUCLEUS, ${TIME}s per part, seed $SEED"
for PART_WORKERS in "onset:$WORKERS_ONSET" "coda:$WORKERS_CODA" "nucleus:$WORKERS_NUCLEUS"; do
  PART="${PART_WORKERS%%:*}"; WORKERS="${PART_WORKERS##*:}"
  "$PYTHON" -m util.optimize_keyboard --statistics "$STATISTICS" --parts "$PART" --time "$TIME" --workers "$WORKERS" --seed "$SEED" --seed-layout "$SEED_LAYOUT" \\
      --incumbent-dir "$OUT/incumbents" --report "$OUT/report_$PART.json" --output "$OUT/$PART.json" > "$OUT/$PART.log" 2>&1 &
done
wait
"$PYTHON" -m util.merge_layouts --output "$OUT/merged.json" onset="$OUT/onset.json" nucleus="$OUT/nucleus.json" coda="$OUT/coda.json" \\
  || { echo "merge failed: a part has no layout (see $OUT/*.log); the incumbents in $OUT/incumbents are still usable"; exit 1; }
for PART in onset nucleus coda; do echo "== $PART"; cat "$OUT/report_$PART.json"; done
echo "done: $OUT/merged.json"
"""


def md5Of(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def importedRepoFiles() -> list[str]:
    """The repo files the two commands import, relative paths, found in a clean interpreter."""
    code = ("import sys, os, importlib\n"
            f"for m in {list(COMMANDS)!r}: importlib.import_module(m)\n"
            "repo = os.getcwd()\n"
            "print('\\n'.join(sorted(os.path.relpath(m.__file__, repo) for m in sys.modules.values()\n"
            "    if getattr(m, '__file__', None) and os.path.abspath(m.__file__).startswith(repo + os.sep))))\n")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, env={**os.environ, "PYTHONPATH": os.getcwd()})
    # only the project's own sources: a virtualenv kept inside the repo (env/, venv/, .venv/ ...) puts third-party modules under the repo path too
    return [line for line in out.stdout.splitlines() if line.split(os.sep)[0] in ("src", "util") and line.endswith(".py")]


def pinnedRequirements(path: str = "requirements.txt") -> list[str]:
    wanted = {name.lower() for name in REQUIRED_PACKAGES}
    with open(path) as rfile:
        lines = [line.strip() for line in rfile if line.strip() and not line.startswith("#")]
    pins = [line for line in lines if line.split("==")[0].lower().replace("_", "-") in wanted]
    missing = wanted - {line.split("==")[0].lower() for line in pins}
    if missing:
        raise SystemExit(f"{path} has no pin for {sorted(missing)}")
    return pins


def gitCommit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.strip()
    return (result.stdout.strip() or "unknown") + (" (+ uncommitted changes)" if dirty else "")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m util.package_remote_solve", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--statistics", required=True, metavar="PATH", help="a util.build_layout_statistics file")
    parser.add_argument("--output", metavar="FILE", default=None, help="default remote_solve_<date>.tar.gz")
    args = parser.parse_args(argv)
    for path in (args.statistics, SEED_PATH):
        if not os.path.exists(path):
            raise SystemExit(f"{path} not found.")

    files: dict[str, bytes] = {}
    for path in importedRepoFiles():
        with open(path, "rb") as ffile:
            files[path] = ffile.read()
    with open(args.statistics, "rb") as ffile:
        files["LayoutStatistics.pickle"] = ffile.read()
    with open(SEED_PATH, "rb") as ffile:
        files[SEED_PATH] = ffile.read()
    files["requirements-remote.txt"] = ("\n".join(pinnedRequirements()) + "\n").encode()
    files["run_remote.sh"] = RUN_SCRIPT.encode()

    from src.layoutstatistics import loadLayoutStatistics
    meta = loadLayoutStatistics(args.statistics)["meta"]
    manifest: dict[str, Any] = {"built": time.strftime("%Y-%m-%d %H:%M:%S"), "commit": gitCommit(), "statistics": meta,
                                "files": {name: md5Of(data) for name, data in sorted(files.items())}}
    files["MANIFEST.json"] = json.dumps(manifest, indent=2, default=str).encode()
    files["MANIFEST.md5"] = "".join(f"{md5Of(data)}  {name}\n" for name, data in sorted(files.items()) if name != "MANIFEST.json").encode()

    output = args.output or f"remote_solve_{time.strftime('%Y%m%d')}.tar.gz"
    with tarfile.open(output, "w:gz") as tar:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(f"{ROOT}/{name}")
            info.size = len(data)
            info.mtime = int(time.time())
            info.mode = 0o755 if name.endswith(".sh") else 0o644
            tar.addfile(info, io.BytesIO(data))
    size = os.path.getsize(output)
    if size > 5_000_000:
        print(f"WARNING: {size / 1e6:.1f} MB, expected about 0.2 MB: look at `tar tzvf {output} | sort -k3 -n | tail`")
    print(f"Wrote {output}: {len(files)} files, {os.path.getsize(output) / 1e6:.1f} MB, commit {manifest['commit']}.")
    print("Python files:", ", ".join(name for name in sorted(files) if name.endswith(".py")))


if __name__ == "__main__":
    main()
