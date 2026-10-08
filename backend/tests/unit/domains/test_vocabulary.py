"""The design vocabulary is complete, numbered as in the brief, and every entry is real code."""

import re
from collections import Counter

import pytest

from app.domains.references import vocabulary
from app.domains.references.importers import VocabularyImporter
from app.domains.references.schemas import ReferenceKind, ReferenceSource
from app.domains.references.vocabulary.base import Section

# (title, size, first item, last item) for every section, in the order of the brief.
PATTERNS = [
    ("Navigation & App Shell", 40),
    ("Buttons & Actions", 40),
    ("Cards & Containers", 40),
    ("Bento & Dashboard Patterns", 30),
    ("Forms & Inputs", 40),
    ("Selection & Controls", 30),
    ("AI-Specific UI", 50),
    ("Chat & Communication", 30),
    ("Tables & Data", 30),
    ("Data Visualization", 40),
    ("Feedback & Status", 30),
    ("Overlays & Focused Interactions", 20),
    ("Advanced Layout & Interaction", 30),
    ("Files, Media & Content", 20),
    ("Premium / Wow UI Patterns", 30),
]
EFFECTS = [
    ("Hover & Pointer Effects", 40, "", ""),
    ("Click & Press Effects", 30, "", ""),
    ("Entrance Animations", 30, "Fade in", "Spring in"),
    ("Exit Animations", 20, "Fade out", "Particle dissolve"),
    ("Scroll Effects", 30, "", ""),
    ("Text Effects", 30, "Typewriter effect", "Text kinetic typography"),
    ("Background Effects", 30, "Gradient background", "Floating particles"),
    ("Glass & Material Effects", 20, "Glassmorphism", "Dynamic transparency"),
    ("Shadow & Depth Effects", 20, "Soft shadow", "Elevation transition"),
    ("Border & Edge Effects", 20, "Animated border", "Morphing corners"),
    ("Loading Effects", 30, "Spinner", "Indeterminate wave"),
    ("Notification & Feedback Effects", 25, "Toast slide-in", "Status wave"),
    ("Card Effects", 25, "Card lift", "Card depth stacking"),
    ("Image & Media Effects", 25, "Image fade", "Image spotlight"),
    ("Modal / Drawer Effects", 25, "Modal fade", "Tooltip spring"),
    ("Navigation Effects", 20, "Active indicator slide", "Navigation indicator animation"),
    ("Data Visualization Effects", 30, "Chart draw animation", "Chart interpolation"),
    ("AI / Agent Effects", 30, "AI thinking pulse", "Conversation branching animation"),
    ("Premium / Experimental Effects", 20, "Liquid morphing", "Particle-to-object morph"),
]
# Upper-case markers only: "todo" is also a perfectly good name for a kanban column.
PLACEHOLDER = re.compile(r"\b(TODO|FIXME|XXX)\b|(?i:lorem ipsum|placeholder code|not implemented)")


def _group(name: str) -> list[Section]:
    return [section for section in vocabulary.sections() if section.group == name]


def test_the_five_hundred_patterns_are_all_there_in_the_briefs_sections() -> None:
    sections = _group("patterns")

    assert [(section.title, len(section.items)) for section in sections] == PATTERNS
    assert sum(len(section.items) for section in sections) == 500


def test_the_five_hundred_effects_are_all_there_in_the_briefs_sections() -> None:
    sections = _group("effects")

    assert [(section.title, len(section.items)) for section in sections] == [
        (title, size) for title, size, _, _ in EFFECTS
    ]
    assert sum(len(section.items) for section in sections) == 500
    for section, (_, _, first, last) in zip(sections, EFFECTS, strict=True):
        if first:
            assert (section.items[0].name, section.items[-1].name) == (first, last)


@pytest.mark.parametrize("group", ["patterns", "effects"])
def test_numbering_runs_from_one_to_five_hundred_without_a_gap(group: str) -> None:
    expected = 1
    for section in _group(group):
        assert section.start == expected, f"{section.title} should start at {expected}"
        expected += len(section.items)
    assert expected == 501


def test_the_six_combinations_from_the_brief_are_recipes() -> None:
    (section,) = _group("recipes")

    assert [item.name.split(":")[0] for item in section.items] == [
        "Card",
        "AI response",
        "Primary CTA",
        "Dashboard",
        "AI agent workflow",
        "Glass sidebar",
    ]
    # Each recipe names the four effects it combines.
    assert all(item.name.count(" + ") == 3 for item in section.items)


def test_every_entry_is_runnable_code_and_not_a_placeholder() -> None:
    for section in vocabulary.sections():
        for item in section.items:
            where = f"{section.title} / {item.name}"
            assert item.html.strip().startswith("<"), where
            assert "{" in item.css and "}" in item.css, where
            assert item.note.strip(), f"{where} has no description"
            for part in (item.html, item.css, item.js):
                assert not PLACEHOLDER.search(part), where


def test_no_two_entries_of_a_section_are_the_same_code() -> None:
    for section in vocabulary.sections():
        seen = Counter((item.html, item.css, item.js) for item in section.items)
        repeated = [item.name for item in section.items if seen[(item.html, item.css, item.js)] > 1]
        # "Slide in" and "Slide right" are the same motion under two names in the brief.
        assert set(repeated) <= {"Slide in", "Slide right"}, f"{section.title}: {repeated}"


def test_entries_have_unique_slugs_and_carry_their_code_as_files() -> None:
    references = list(vocabulary.entries())

    assert len(references) == 1006
    assert len({reference.slug for reference in references}) == 1006
    assert Counter(reference.kind for reference in references) == {
        ReferenceKind.COMPONENT: 500,
        ReferenceKind.EFFECT: 500,
        ReferenceKind.RECIPE: 6,
    }
    for reference in references:
        files = {file.path: file.content for file in reference.files}
        assert {"index.html", "markup.html", "styles.css"} <= set(files), reference.slug
        # The standalone page is the same code, assembled: it can be opened as it is.
        assert files["index.html"].startswith("<!doctype html>")
        assert files["markup.html"].strip() in files["index.html"]
        assert files["styles.css"].strip() in files["index.html"]
        if "script.js" in files:
            assert files["script.js"] in files["index.html"]
            # Scoped, so several entries can share a page.
            assert files["script.js"].startswith("(() => {")


def test_slugs_carry_the_number_from_the_brief() -> None:
    by_slug = {reference.slug: reference for reference in vocabulary.entries()}

    assert by_slug["effects/211-glassmorphism"].category == "glass-material-effects"
    assert by_slug["effects/500-particle-to-object-morph"].kind is ReferenceKind.EFFECT
    assert "#211" in by_slug["effects/211-glassmorphism"].tags
    assert any(slug.startswith("patterns/001-") for slug in by_slug)
    assert any(slug.startswith("patterns/500-") for slug in by_slug)


async def test_the_importer_yields_the_whole_vocabulary_as_the_projects_own_work() -> None:
    references = [reference async for reference in VocabularyImporter().components()]

    assert len(references) == 1006
    assert {reference.source for reference in references} == {ReferenceSource.VOCABULARY}
    assert {reference.license for reference in references} == {"Project"}
    assert all(reference.source_url.startswith("vocabulary://") for reference in references)
