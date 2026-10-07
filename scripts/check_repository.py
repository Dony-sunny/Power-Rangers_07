"""Read-only local publication checks. Prints file locations, never secret values."""

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent


def check():
    problems = []
    links = 0
    for document in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
        for target in re.findall(
            r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)",
            document.read_text(encoding="utf-8"),
        ):
            target = target.strip("<>").split("#")[0]
            if not target or re.match(r"^[a-zA-Z]+:", target):
                continue
            links += 1
            if not (document.parent / unquote(target)).exists():
                problems.append(
                    f"Broken local link: {document.relative_to(ROOT)} → {target}"
                )
    tracked = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    patterns = [
        r"AKIA[0-9A-Z]{16}",
        r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
        r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    ]
    for relative in tracked:
        path = ROOT / relative
        if not path.is_file():
            continue
        if (
            path.name == ".env"
            or path.suffix in {".db", ".log"}
            or any(part in {"node_modules", ".venv", ".runtime"} for part in path.parts)
        ):
            problems.append(f"Runtime/secret artifact included: {relative}")
        if path.stat().st_size > 5 * 1024 * 1024:
            problems.append(f"Review large artifact (>5 MB): {relative}")
        if path.suffix in {".png", ".jpg", ".jpeg", ".pdf", ".xlsx"}:
            continue
        content = path.read_text(encoding="utf-8-sig", errors="replace")
        if any(re.search(pattern, content) for pattern in patterns):
            problems.append(
                f"Potential credential signature (value redacted): {relative}"
            )
    diff = subprocess.run(
        ["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True
    )
    if diff.returncode:
        problems.append("Git diff whitespace check failed; inspect git diff --check.")
    for problem in problems:
        print(problem)
    print(
        f"Checked {links} local documentation links and {len(tracked)} publication files; {len(problems)} findings."
    )
    print(
        "Pattern scan is a basic review, not proof that all possible secrets are absent. Review staged diffs before publication."
    )
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(check())
