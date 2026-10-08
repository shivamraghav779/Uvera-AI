"""Write the design vocabulary to a directory, one standalone page per entry.

    poetry run python -m scripts.export_vocabulary OUT_DIR [group/section-prefix]

Used to look at entries in a browser and by the check that opens every one of
them (``frontend/tests/e2e/vocabulary.mjs``). ``OUT_DIR/index.json`` lists what
was written.
"""

import json
import sys
from pathlib import Path

from app.domains.references import vocabulary


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out = Path(argv[0])
    prefix = argv[1] if len(argv) > 1 else ""
    index = []
    for entry in vocabulary.entries():
        if not f"{entry.slug.split('/')[0]}/{entry.category}".startswith(prefix):
            continue
        directory = out / entry.slug
        directory.mkdir(parents=True, exist_ok=True)
        for file in entry.files:
            (directory / file.path).write_text(file.content, encoding="utf-8")
        index.append({"slug": entry.slug, "name": entry.name, "category": entry.category})
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(f"{len(index)} entries written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
