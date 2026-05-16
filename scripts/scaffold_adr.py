from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = REPO_ROOT / "assets" / "adr-scaffold"
DECISIONS_DIR = REPO_ROOT / "docs" / "explanation" / "decisions"
README_PATH = DECISIONS_DIR / "README.md"
ADR_PREFIX = "ADR-"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "decision"


def titleize_slug(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[-_]+", value) if part)


def next_adr_number() -> int:
    numbers = []
    for path in DECISIONS_DIR.glob(f"{ADR_PREFIX}[0-9][0-9][0-9][0-9]-*.md"):
        match = re.match(rf"{ADR_PREFIX}([0-9]{{4}})-", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers, default=0) + 1


def render(template: str, replacements: dict[str, str]) -> str:
    content = template
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def ensure_readme() -> None:
    if README_PATH.exists():
        return

    README_PATH.parent.mkdir(parents=True, exist_ok=True)
    README_PATH.write_text(
        "\n".join(
            [
                "# Architecture Decisions",
                "",
                "Use this directory for durable architecture decision records (ADRs).",
                "",
                "Naming convention:",
                "",
                "- `ADR-0001-short-title.md`",
                "- `ADR-0002-another-decision.md`",
                "",
                "ADRs record the choice. K-Briefs record the learning and evidence that",
                "support that choice.",
                "",
                "Prefer linking ADRs to requirements, specifications, tests, and K-Briefs",
                "so the decision remains traceable over time.",
                "",
                "## Index",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def append_index_entry(path: Path, title: str) -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    entry = f"- [{path.stem}: {title}](./{path.name})"
    if entry in readme:
        return
    README_PATH.write_text(readme.rstrip() + "\n" + entry + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a repository ADR under docs/explanation/decisions/"
    )
    parser.add_argument("title", nargs="+", help="Human-readable ADR title")
    args = parser.parse_args()

    if not ASSET_ROOT.exists():
        raise SystemExit(f"ADR scaffold assets not found: {ASSET_ROOT}")

    ensure_readme()
    title_input = " ".join(args.title).strip()
    title = (
        titleize_slug(title_input)
        if " " not in title_input and "-" in title_input
        else title_input
    )
    adr_number = next_adr_number()
    slug = slugify(title_input)
    adr_id = f"{ADR_PREFIX}{adr_number:04d}"
    destination = DECISIONS_DIR / f"{adr_id}-{slug}.md"
    if destination.exists():
        raise SystemExit(f"ADR already exists: {destination}")

    template = (ASSET_ROOT / "ADR.md.template").read_text(encoding="utf-8")
    content = render(
        template,
        {
            "__ADR_NUMBER__": f"{adr_number:04d}",
            "__ADR_TITLE__": title,
            "__ADR_DATE__": date.today().isoformat(),
        },
    )
    destination.write_text(content.rstrip() + "\n", encoding="utf-8")
    append_index_entry(destination, title)
    print(destination.relative_to(REPO_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
