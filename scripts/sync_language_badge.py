"""Generate the README language badge from the shipped web language manifest."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    languages = json.loads((ROOT / "web/messages/languages.json").read_text(encoding="utf-8"))
    readme = ROOT / "README.md"
    current = readme.read_text(encoding="utf-8")
    rendered, count = re.subn(
        r"https://img\.shields\.io/badge/languages-\d+-33417f",
        f"https://img.shields.io/badge/languages-{len(languages)}-33417f",
        current,
    )
    if count != 1:
        parser.exit(1, "Expected exactly one language badge in the README.\n")
    if args.check and rendered != current:
        parser.exit(1, "Run python -m scripts.sync_language_badge to regenerate the language badge.\n")
    if rendered != current:
        readme.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
