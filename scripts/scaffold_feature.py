from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = REPO_ROOT / "assets" / "feature-scaffold"
FEATURES_DIR = REPO_ROOT / "features"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "new-feature"


def titleize(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("-"))


def render(template: str, replacements: dict[str, str]) -> str:
    content = template
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a repository-owned OCI devcontainer feature"
    )
    parser.add_argument("name", nargs="+", help="Feature id or working title")
    parser.add_argument(
        "--title",
        help="Display name for the feature (defaults to a titleized feature id)",
    )
    parser.add_argument(
        "--description",
        help="Feature description for devcontainer-feature.json",
    )
    parser.add_argument(
        "--command",
        help="Primary command or binary that the feature is expected to expose",
    )
    args = parser.parse_args()

    if not ASSET_ROOT.exists():
        raise SystemExit(f"Feature scaffold assets not found: {ASSET_ROOT}")

    feature_input = " ".join(args.name).strip()
    feature_id = slugify(feature_input)
    feature_name = args.title or titleize(feature_id)
    feature_description = args.description or "Install [REPLACE: describe the tool or workflow]."
    feature_command = args.command or feature_id
    destination_root = FEATURES_DIR / feature_id
    if destination_root.exists():
        raise SystemExit(f"Feature already exists: {destination_root}")

    replacements = {
        "__FEATURE_ID__": feature_id,
        "__FEATURE_NAME__": feature_name,
        "__FEATURE_DESCRIPTION__": feature_description,
        "__FEATURE_COMMAND__": feature_command,
    }

    created: list[Path] = []
    for template in sorted(ASSET_ROOT.rglob("*.template")):
        relative = template.relative_to(ASSET_ROOT)
        destination = destination_root / relative.with_suffix("")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            render(template.read_text(encoding="utf-8"), replacements).rstrip() + "\n",
            encoding="utf-8",
        )
        created.append(destination)

    for path in created:
        if path.name in {"install.sh", "test.sh"}:
            make_executable(path)

    print(f"Scaffolded features/{feature_id}")
    for path in created:
        print(path.relative_to(REPO_ROOT))
    print("Next step: record the feature decision with `task init:adr -- decision-slug`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
