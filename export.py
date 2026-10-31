"""Copy my practice solutions out of honepad / open-gauntlet into this repo.

Usage (from anywhere):
    python E:\\interns\\ICA\\my-solutions\\export.py            # export + commit + push
    python E:\\interns\\ICA\\my-solutions\\export.py --no-push  # export + commit only

Each attempt is saved as <tool>/<problem>/<date>.py; identical code is skipped,
so running it repeatedly is safe. README.md is regenerated as an index.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
HONEPAD_WORK = Path.home() / ".honepad" / "work"
GAUNTLET_RUNS = Path.home() / ".open-gauntlet" / "runs"
SAVED = []   # relative paths written this run, used for the commit message


def digest(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def already_saved(folder, body):
    """True if some saved attempt in folder has the same code (ignoring our header)."""
    h = digest(body)
    for f in folder.glob("*.py"):
        saved = f.read_text(encoding="utf-8").split("# ---\n", 1)[-1]
        if digest(saved) == h:
            return True
    return False


def save(folder, stamp, header, body):
    folder.mkdir(parents=True, exist_ok=True)
    if not body.strip() or already_saved(folder, body):
        return False
    target = folder / f"{stamp}.py"
    n = 2
    while target.exists():
        target = folder / f"{stamp}_{n}.py"
        n += 1
    target.write_text(header + "# ---\n" + body, encoding="utf-8")
    SAVED.append(target.relative_to(REPO).as_posix())
    print(f"saved {SAVED[-1]}")
    return True


def mmss(seconds):
    return f"{int(seconds) // 60}:{int(seconds) % 60:02d}"


def export_honepad():
    if not HONEPAD_WORK.exists():
        return
    for work in HONEPAD_WORK.glob("*/python3/work.py"):
        problem = work.parent.parent.name
        when = datetime.fromtimestamp(work.stat().st_mtime)
        header = f"# honepad: {problem}\n# saved: {when:%Y-%m-%d %H:%M}\n"
        save(REPO / "honepad" / problem, f"{when:%Y-%m-%d_%H%M}",
             header, work.read_text(encoding="utf-8"))


def export_gauntlet():
    if not GAUNTLET_RUNS.exists():
        return
    for run_dir in GAUNTLET_RUNS.iterdir():
        meta_file, code_file = run_dir / "run.json", run_dir / "solution.py"
        if not (meta_file.exists() and code_file.exists()):
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        when = datetime.fromtimestamp((meta.get("startedAt") or meta["createdAt"]) / 1000)
        done = meta.get("completedLevels", [])
        times = ", ".join(f"L{k} {mmss(v)}" for k, v in sorted(meta.get("levelTimes", {}).items()))
        header = (
            f"# open-gauntlet: {meta['problemId']}\n"
            f"# started: {when:%Y-%m-%d %H:%M}\n"
            f"# completed levels: {done} ({meta.get('status')})\n"
            f"# finished at (elapsed): {times}\n"
        )
        save(REPO / "open-gauntlet" / meta["problemId"], f"{when:%Y-%m-%d_%H%M}",
             header, code_file.read_text(encoding="utf-8"))


def write_index():
    rows = []
    for f in sorted(REPO.glob("*/*/*.py")):
        head = f.read_text(encoding="utf-8").split("# ---\n", 1)[0]
        info = [l[2:] for l in head.splitlines()[1:] if l.startswith("# ")]
        rel = f.relative_to(REPO).as_posix()
        tool, problem = f.parts[-3], f.parts[-2]
        rows.append(f"| {tool} | {problem} | [{f.stem}]({rel}) | {'<br>'.join(info)} |")
    (REPO / "README.md").write_text(
        "# CodeSignal ICA practice\n\n"
        "My solutions to 4-level industry-coding practice problems "
        "(honepad, open-gauntlet), written under a 90-minute timer.\n\n"
        "| Tool | Problem | Attempt | Notes |\n|---|---|---|---|\n"
        + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True)


def sync(push):
    if not SAVED:
        print("nothing new to commit")
        return
    problems = sorted({"/".join(p.split("/")[:2]) for p in SAVED})
    git("add", "-A")
    git("commit", "-q", "-m", "Add attempt: " + ", ".join(problems))
    print("committed:", ", ".join(problems))
    if push:
        git("push", "-q")
        print("pushed to origin")


if __name__ == "__main__":
    export_honepad()
    export_gauntlet()
    write_index()
    sync(push="--no-push" not in sys.argv)
