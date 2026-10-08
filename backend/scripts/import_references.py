"""Fill the reference component library.

    poetry run python -m scripts.import_references ui_layouts
    poetry run python -m scripts.import_references magic_ui
    poetry run python -m scripts.import_references bootstrap
    poetry run python -m scripts.import_references vocabulary
    poetry run python -m scripts.import_references twenty_first --code 20
    poetry run python -m scripts.import_references all

Sources
    ui_layouts     https://www.ui-layouts.com   MIT, read from its GitHub repository
    magic_ui       https://magicui.design       MIT, read from its GitHub repository
    bootstrap      https://getbootstrap.com     MIT (docs CC BY 3.0), read from its GitHub
                   repository: example pages, documentation pages with their stylesheet
                   partials, and the stylesheet foundation
    vocabulary     the platform's own design vocabulary (500 patterns, 500 effects and
                   recipes), written in app/domains/references/vocabulary
    twenty_first   https://21st.dev             official API; needs TWENTYFIRST_API_KEY.
                   Search (metadata) is free. ``--code N`` also fetches the source of up
                   to N components, which uses the key's allowance; it stops by itself
                   when 21st.dev declines. The site itself is never crawled: its terms
                   forbid that.

``--path DIR`` reads an open-source project from a local checkout instead of downloading.
Running an import again updates what changed and leaves the rest alone.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.database.connection import Database
from app.domains.references.importers import (
    BOOTSTRAP_BRANCH,
    BOOTSTRAP_DIRECTORIES,
    BOOTSTRAP_REPOSITORY,
    REGISTRY_SOURCES,
    BootstrapImporter,
    ReferenceImporter,
    ShadcnRegistryImporter,
    TwentyFirstImporter,
    VocabularyImporter,
    download_directories,
    download_registry,
    temporary_checkout,
)
from app.domains.references.repository import ReferenceRepository
from app.domains.references.schemas import ImportReport, ReferenceSource
from app.domains.references.service import ReferenceLibrary

DOWNLOAD_TIMEOUT_SECONDS = 120.0


async def _run(importer: ReferenceImporter, database: Database) -> ImportReport:
    async with database.session() as session:
        return await ReferenceLibrary(ReferenceRepository(session), session).import_from(importer)


async def import_source(
    source: ReferenceSource,
    *,
    database: Database,
    client: httpx.AsyncClient,
    path: Path | None,
    code_budget: int,
    per_query: int,
) -> ImportReport:
    if source is ReferenceSource.TWENTY_FIRST:
        key = get_settings().twentyfirst_api_key
        if key is None or not key.get_secret_value():
            raise SystemExit(
                "TWENTYFIRST_API_KEY is not set. Create a key at https://21st.dev/mcp and put "
                "it in backend/.env. (The other sources need no key.)"
            )
        importer: ReferenceImporter = TwentyFirstImporter(
            client, key.get_secret_value(), code_budget=code_budget, per_query=per_query
        )
        return await _run(importer, database)

    if source is ReferenceSource.VOCABULARY:
        return await _run(VocabularyImporter(), database)
    if source is ReferenceSource.BOOTSTRAP:
        if path is not None:
            return await _run(BootstrapImporter(path), database)
        with temporary_checkout() as directory:
            checkout = Path(directory)
            print(f"  downloading {BOOTSTRAP_REPOSITORY} …", flush=True)
            revision = await download_directories(
                client,
                BOOTSTRAP_REPOSITORY,
                BOOTSTRAP_BRANCH,
                BOOTSTRAP_DIRECTORIES,
                checkout,
                timeout_seconds=DOWNLOAD_TIMEOUT_SECONDS,
            )
            return await _run(BootstrapImporter(checkout, revision), database)

    config = REGISTRY_SOURCES[source]
    if path is not None:
        return await _run(ShadcnRegistryImporter(config, path), database)
    with temporary_checkout() as directory:
        checkout = Path(directory)
        print(f"  downloading {config.repository} …", flush=True)
        revision = await download_registry(
            client, config, checkout, timeout_seconds=DOWNLOAD_TIMEOUT_SECONDS
        )
        return await _run(ShadcnRegistryImporter(config, checkout, revision), database)


def _print(report: ImportReport) -> None:
    print(
        f"  {report.source.value}: {report.seen} components "
        f"({report.created} new, {report.updated} updated, {report.unchanged} unchanged), "
        f"{report.with_code} with source code"
    )
    for line in report.skipped[:10]:
        print(f"    skipped {line}")
    if len(report.skipped) > 10:
        print(f"    … and {len(report.skipped) - 10} more skipped")
    if report.note:
        print(f"    note: {report.note}")


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="scripts.import_references", description=__doc__)
    parser.add_argument("source", choices=[*(s.value for s in ReferenceSource), "all"])
    parser.add_argument("--path", type=Path, help="local checkout of an open-source registry")
    parser.add_argument(
        "--code", type=int, default=0, help="21st.dev: fetch source for up to N components"
    )
    parser.add_argument(
        "--per-query", type=int, default=12, help="21st.dev: results kept per search (max 50)"
    )
    args = parser.parse_args(argv)
    if args.path is not None and (args.source in {"all", ReferenceSource.TWENTY_FIRST.value}):
        parser.error("--path applies to one open-source project (ui_layouts, magic_ui, bootstrap)")
    if args.path is not None and not args.path.is_dir():
        parser.error(f"{args.path} is not a directory")

    settings = get_settings()
    if args.source == "all":
        # Without a key the open-source registries are still imported.
        has_key = settings.twentyfirst_api_key is not None
        sources = [s for s in ReferenceSource if has_key or s is not ReferenceSource.TWENTY_FIRST]
        if not has_key:
            print("  twenty_first: skipped (TWENTYFIRST_API_KEY is not set)")
    else:
        sources = [ReferenceSource(args.source)]

    database = Database(settings.database_url)
    failed = False
    try:
        async with httpx.AsyncClient() as client:
            for source in sources:
                try:
                    report = await import_source(
                        source,
                        database=database,
                        client=client,
                        path=args.path,
                        code_budget=args.code,
                        per_query=args.per_query,
                    )
                except AppException as exc:
                    failed = True
                    print(f"  {source.value}: FAILED — {exc.message}", file=sys.stderr)
                else:
                    _print(report)
    finally:
        await database.dispose()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
