"""
Shared pipeline-timing log: one TSV line per timed call, appended to the gitignored
`pipeline_timings.log` at the repo root. `dictionary.runStep` logs every orchestrated
step (kind `step`: the subprocess wall time); the heavyweight phases inside
`util.build_phonetic_theory` and `util.build_disambiguated_theory` log their internal
stages (kind `phase`); `runPipeline` logs one `pipeline` line per whole run (complete
or stopped at the `--steps` limit). A timing-log failure never breaks the pipeline.
"""
import os
import time
from contextlib import contextmanager
from datetime import datetime

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMINGS_LOG = os.path.join(_REPO_ROOT, "pipeline_timings.log")


def recordTiming(kind: str, label: str, seconds: float, status: str = "ok") -> None:
    """Append one line to pipeline_timings.log and echo it to stdout. Never raises."""
    line = (f"{datetime.now().isoformat(timespec='seconds')}\t{seconds:.1f}\t"
            f"{kind}\t{status}\t{label}")
    try:
        newFile = not os.path.exists(TIMINGS_LOG)
        with open(TIMINGS_LOG, "a", encoding="utf-8") as f:
            if newFile:
                _ = f.write("# timestamp\tseconds\tkind\tstatus\tlabel\n")
            _ = f.write(line + "\n")
    except OSError:
        pass  # a broken timing log must never break the pipeline
    print(f"[timing] {label}: {seconds:.1f} s")


@contextmanager
def timedCall(kind: str, label: str):
    """`with timedCall("phase", "..."):` around one call; records ok or failed."""
    start = time.monotonic()
    try:
        yield
    except BaseException as exc:
        recordTiming(kind, label, time.monotonic() - start,
                     f"failed: {type(exc).__name__}")
        raise
    recordTiming(kind, label, time.monotonic() - start)
