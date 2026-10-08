"""Page architecture: the story a page tells, and what a generic page looks like.

A page is planned as a *narrative arc*: an ordered list of beats, each with a
role in persuading or serving the visitor ("trust", "problem", "evidence").
The arc depends on what the site is for. A beat names the patterns that can
play it, so the planner chooses a structure by reasoning about the visitor and
then picks patterns for each beat, instead of reaching for
hero / three cards / testimonials / pricing / footer every time.

``generic_findings`` recognises that default skeleton, and other signs of an
unconsidered page, in a plan or a built screen.
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from itertools import pairwise


class SectionRole(StrEnum):
    """What a section does for the visitor."""

    HERO = "hero"
    TRUST = "trust"
    PROBLEM = "problem"
    SOLUTION = "solution"
    PRODUCT_STORY = "product_story"
    FEATURES = "features"
    DEMONSTRATION = "demonstration"
    BENEFITS = "benefits"
    TECHNOLOGY = "technology"
    EVIDENCE = "evidence"
    SOCIAL_PROOF = "social_proof"
    CATEGORIES = "categories"
    FEATURED = "featured"
    OFFERS = "offers"
    CATALOGUE = "catalogue"
    RECOMMENDATIONS = "recommendations"
    REVIEWS = "reviews"
    PRICING = "pricing"
    COMPARISON = "comparison"
    QUESTIONS = "questions"
    PROCESS = "process"
    GALLERY = "gallery"
    PEOPLE = "people"
    ACTION = "action"
    FOOTER = "footer"


@dataclass(frozen=True, slots=True)
class Beat:
    role: SectionRole
    # Pattern ids that can play this beat, most characteristic first.
    patterns: tuple[str, ...]
    intent: str


@dataclass(frozen=True, slots=True)
class NarrativeArc:
    id: str
    name: str
    # When this arc is the right one.
    when: str
    beats: tuple[Beat, ...]
    note: str = ""

    def outline(self) -> str:
        return " -> ".join(beat.role.value for beat in self.beats)


_R = SectionRole
_FOOT = Beat(_R.FOOTER, ("footer",), "Where everything else lives.")


def _b(role: SectionRole, patterns: str, intent: str) -> Beat:
    return Beat(role, tuple(patterns.split()), intent)


_ARCS: tuple[NarrativeArc, ...] = (
    NarrativeArc(
        "product_launch", "Product launch",
        "One product is being introduced and the page exists to build desire for it.",
        (_b(_R.HERO, "hero.immersive hero.product hero.centered", "The product alone, very large, with its one-line promise."),
         _b(_R.PRODUCT_STORY, "media.overlay feature_grid.alternating", "Why it exists: the idea behind it, told with imagery."),
         _b(_R.FEATURES, "feature_grid.bento feature_grid.alternating", "What is new, a few things only, each shown."),
         _b(_R.DEMONSTRATION, "media.framed gallery.carousel steps.cards", "The product in use."),
         _b(_R.BENEFITS, "stats.inline feature_grid.list", "What it changes for its owner, in figures where possible."),
         _b(_R.SOCIAL_PROOF, "testimonials.spotlight logo_cloud.static", "One strong voice, not a wall of quotes."),
         _b(_R.ACTION, "cta.centered cta.split", "The single action: order, reserve or join."),
         _FOOT),
        "One beat per screenful. No pricing table, no feature dump."),
    NarrativeArc(
        "brand_story", "Brand story",
        "The brand's world matters more than any single feature (luxury, hospitality, lifestyle).",
        (_b(_R.HERO, "hero.immersive hero.editorial", "Atmosphere first: one image, few words."),
         _b(_R.PRODUCT_STORY, "media.image_right media.image_left", "What the brand believes, in a short text beside an image."),
         _b(_R.GALLERY, "gallery.editorial gallery.masonry", "The world of the brand in pictures."),
         _b(_R.FEATURED, "collection.media media.overlay", "What can be had: a few pieces, not a catalogue."),
         _b(_R.SOCIAL_PROOF, "testimonials.spotlight", "A single endorsement, quietly set."),
         _b(_R.ACTION, "cta.split cta.centered", "An invitation, not a sales push."),
         _FOOT),
        "Few sections, each given a great deal of room."),
    NarrativeArc(
        "saas_conversion", "SaaS conversion",
        "Software people can sign up for; the page must show it, prove it and start a trial.",
        (_b(_R.HERO, "hero.product hero.split hero.centered", "The outcome promised, with the product visible."),
         _b(_R.TRUST, "logo_cloud.static logo_cloud.marquee stats.inline", "Who already relies on it."),
         _b(_R.PROBLEM, "feature_grid.list media.image_left", "The cost of the old way, in the customer's words."),
         _b(_R.SOLUTION, "feature_grid.bento feature_grid.alternating", "How the product answers it: unequal tiles, the main capability largest."),
         _b(_R.DEMONSTRATION, "media.framed steps.numbered command", "A real workflow from start to finish."),
         _b(_R.EVIDENCE, "stats.inline testimonials.spotlight comparison", "Measured results from named customers."),
         _b(_R.PRICING, "pricing", "Only when price is part of the decision on this page."),
         _b(_R.ACTION, "cta.centered cta.banner", "Start now, with the objection removed (free trial, no card)."),
         _FOOT),
        "Proof comes before price. Leave out beats the product cannot honestly fill."),
    NarrativeArc(
        "focused_pitch", "Focused pitch",
        "An early product or a single offer: one claim, one action, little else.",
        (_b(_R.HERO, "hero.centered hero.split", "The problem and the answer in one statement."),
         _b(_R.SOLUTION, "feature_grid.alternating media.framed", "The two or three things that make it work."),
         _b(_R.PROCESS, "steps.numbered steps.cards", "How someone gets started."),
         _b(_R.EVIDENCE, "stats.inline testimonials.spotlight", "Whatever early proof exists."),
         _b(_R.ACTION, "cta.centered", "Join, with the same action as the hero."),
         _FOOT),
        "Short on purpose. Five sections is plenty."),
    NarrativeArc(
        "ai_product", "AI product",
        "The product is an AI system; visitors need to see it think and to trust its answers.",
        (_b(_R.HERO, "hero.product hero.centered", "What it does for you, with the interaction itself on show."),
         _b(_R.DEMONSTRATION, "command media.framed", "A real prompt and a real answer, or an agent completing a task."),
         _b(_R.TECHNOLOGY, "steps.timeline feature_grid.bento", "How it reaches an answer: what it reads, which tools it uses, where it cites."),
         _b(_R.BENEFITS, "feature_grid.alternating stats.inline", "What changes in the user's day."),
         _b(_R.TRUST, "feature_grid.list logo_cloud.static", "Data handling, accuracy, human control."),
         _b(_R.EVIDENCE, "testimonials.spotlight stats.inline", "Results from people who use it."),
         _b(_R.ACTION, "cta.centered cta.banner", "Try it on your own material."),
         _FOOT),
        "Show the product working before describing it. Trust is a beat of its own."),
    NarrativeArc(
        "enterprise_solution", "Enterprise solution",
        "A considered purchase by an organisation: several stakeholders, long evaluation.",
        (_b(_R.HERO, "hero.split hero.product", "The business outcome, stated soberly."),
         _b(_R.TRUST, "logo_cloud.static stats.inline", "Named customers and scale."),
         _b(_R.PROBLEM, "media.image_left feature_grid.list", "The operational problem and what it costs."),
         _b(_R.SOLUTION, "feature_grid.alternating feature_grid.bento", "Capabilities grouped by the team that uses them."),
         _b(_R.TECHNOLOGY, "feature_grid.list steps.timeline", "Security, compliance, integration and deployment."),
         _b(_R.EVIDENCE, "testimonials.spotlight stats.inline comparison", "A customer's result with figures."),
         _b(_R.ACTION, "cta.split cta.banner", "Talk to sales or book a demonstration."),
         _FOOT)),
    NarrativeArc(
        "security_assurance", "Security assurance",
        "A security or compliance product, where credibility is the whole sale.",
        (_b(_R.HERO, "hero.centered hero.split", "What is protected, in exact terms."),
         _b(_R.TRUST, "logo_cloud.static stats.inline", "Certifications, audits and who relies on it."),
         _b(_R.PROBLEM, "feature_grid.list stats.inline", "The exposure, with real figures."),
         _b(_R.PROCESS, "steps.timeline steps.numbered", "How protection works, step by step."),
         _b(_R.FEATURES, "feature_grid.bento feature_grid.grid", "Coverage, without theatre."),
         _b(_R.EVIDENCE, "testimonials.spotlight comparison", "Proof from a security leader."),
         _b(_R.ACTION, "cta.banner cta.split", "Request an assessment."),
         _FOOT)),
    NarrativeArc(
        "healthcare_trust", "Healthcare trust",
        "A health product or service: nothing is believed until trust is established.",
        (_b(_R.HERO, "hero.split hero.centered", "The benefit to patients or clinicians, calmly stated."),
         _b(_R.TRUST, "logo_cloud.static stats.inline", "Clinical partners, approvals and certification, straight away."),
         _b(_R.PROBLEM, "media.image_left feature_grid.list", "The clinical or operational problem."),
         _b(_R.SOLUTION, "feature_grid.alternating media.image_right", "What the product does about it, in plain language."),
         _b(_R.TECHNOLOGY, "steps.timeline feature_grid.bento", "How it works, and how data and safety are handled."),
         _b(_R.BENEFITS, "stats.inline feature_grid.list", "Clinical and business value, separately."),
         _b(_R.EVIDENCE, "testimonials.spotlight comparison stats.inline", "Studies, validation figures, a clinician's account."),
         _b(_R.PRODUCT_STORY, "media.framed", "The product as clinicians see it."),
         _b(_R.ACTION, "cta.split cta.centered", "Request a demonstration or speak to the team."),
         _FOOT),
        "Evidence carries this page; superlatives damage it."),
    NarrativeArc(
        "fintech_trust", "Fintech trust",
        "A product that handles money: safety and exactness before excitement.",
        (_b(_R.HERO, "hero.product hero.split", "What you can do with your money, precisely."),
         _b(_R.TRUST, "stats.inline logo_cloud.static", "Regulation, safeguards and scale."),
         _b(_R.FEATURES, "feature_grid.bento feature_grid.alternating", "The few capabilities that matter, with the product on show."),
         _b(_R.PROCESS, "steps.numbered", "Opening an account, start to finish."),
         _b(_R.COMPARISON, "comparison pricing", "Fees and limits, in full."),
         _b(_R.EVIDENCE, "testimonials.cards stats.inline", "Customers and outcomes."),
         _b(_R.QUESTIONS, "faq", "The questions people ask before trusting a product with money."),
         _b(_R.ACTION, "cta.centered", "Open an account."),
         _FOOT)),
    NarrativeArc(
        "developer_adoption", "Developer adoption",
        "A tool for engineers, who decide by trying it.",
        (_b(_R.HERO, "hero.centered hero.product", "What it does, measurably, with the install command."),
         _b(_R.DEMONSTRATION, "command media.framed", "Real code or a real command, before anything else."),
         _b(_R.FEATURES, "feature_grid.grid feature_grid.bento", "Capabilities stated exactly."),
         _b(_R.TECHNOLOGY, "steps.timeline feature_grid.list", "Architecture, limits, compatibility."),
         _b(_R.TRUST, "logo_cloud.static stats.inline", "Who runs it in production; stars, downloads, uptime."),
         _b(_R.PRICING, "pricing", "Plain pricing, including the free tier."),
         _b(_R.ACTION, "cta.banner", "Read the docs or start building."),
         _FOOT),
        "No stock photography and no adjectives a benchmark could not support."),
    NarrativeArc(
        "deep_tech_credibility", "Deep tech credibility",
        "Hard technology that few visitors understand yet; the page must explain and convince.",
        (_b(_R.HERO, "hero.immersive hero.centered hero.editorial", "The breakthrough in one plain sentence."),
         _b(_R.PROBLEM, "media.image_left stats.inline", "The limit the world is stuck at."),
         _b(_R.TECHNOLOGY, "feature_grid.alternating steps.timeline", "How the technology works, with diagrams or close-up imagery."),
         _b(_R.BENEFITS, "stats.inline feature_grid.bento", "What it makes possible, in applications."),
         _b(_R.EVIDENCE, "stats.inline comparison testimonials.spotlight", "Results, papers, pilots."),
         _b(_R.PEOPLE, "feature_grid.list logo_cloud.static", "The team, partners and backers."),
         _b(_R.ACTION, "cta.split cta.centered", "Partner, invest or join."),
         _FOOT)),
    NarrativeArc(
        "research_publication", "Research",
        "An institute, lab or research programme presenting its work.",
        (_b(_R.HERO, "hero.editorial hero.centered", "What is being studied and why it matters."),
         _b(_R.FEATURED, "feature_grid.alternating media.image_right", "The leading finding or project."),
         _b(_R.EVIDENCE, "stats.inline", "The work in figures: publications, datasets, collaborations."),
         _b(_R.CATALOGUE, "feature_grid.list gallery.editorial", "Areas of research."),
         _b(_R.PEOPLE, "feature_grid.list testimonials.spotlight", "The researchers."),
         _b(_R.ACTION, "cta.banner", "Collaborate, apply or read."),
         _FOOT)),
    NarrativeArc(
        "commerce_discovery", "Commerce discovery",
        "A shop with a range of products: help people find and choose.",
        (_b(_R.HERO, "hero.split hero.immersive", "The season's offer or lead product, with a way straight into the range."),
         _b(_R.CATEGORIES, "gallery.grid gallery.carousel", "The departments, as images."),
         _b(_R.FEATURED, "collection.media gallery.carousel", "Featured products with price."),
         _b(_R.OFFERS, "cta.banner media.overlay", "A current offer."),
         _b(_R.CATALOGUE, "collection.media", "The product grid: compact cards, image, name, price, action."),
         _b(_R.RECOMMENDATIONS, "collection.media gallery.carousel", "What else suits this shopper."),
         _b(_R.REVIEWS, "testimonials.cards stats.inline", "Ratings and what buyers say."),
         _FOOT),
        "Products appear within the first two sections. No long brand story before them."),
    NarrativeArc(
        "marketplace_two_sided", "Marketplace",
        "Buyers and sellers (or guests and hosts) meet here; search leads.",
        (_b(_R.HERO, "hero.centered hero.split", "What you can find here, with search as the action."),
         _b(_R.CATEGORIES, "gallery.grid gallery.carousel", "Ways to browse."),
         _b(_R.FEATURED, "collection.media", "Listings with price and rating."),
         _b(_R.PROCESS, "steps.numbered steps.cards", "How it works for the demand side."),
         _b(_R.TRUST, "stats.inline feature_grid.list", "Verification, protection, guarantees."),
         _b(_R.REVIEWS, "testimonials.cards", "Both sides, in their words."),
         _b(_R.ACTION, "cta.split", "The supply side's invitation: list, host or sell."),
         _FOOT)),
    NarrativeArc(
        "listing_search", "Listing search",
        "People arrive to search listings (property, jobs, vehicles).",
        (_b(_R.HERO, "hero.immersive hero.split", "Search by place and need, over an image of what is on offer."),
         _b(_R.FEATURED, "collection.media gallery.grid", "Featured listings with the key facts."),
         _b(_R.CATEGORIES, "gallery.grid", "Areas or kinds to browse."),
         _b(_R.BENEFITS, "feature_grid.alternating stats.inline", "Why search here."),
         _b(_R.REVIEWS, "testimonials.cards testimonials.spotlight", "People who found what they wanted."),
         _b(_R.ACTION, "cta.split cta.banner", "Enquire, or list your own."),
         _FOOT)),
    NarrativeArc(
        "travel_inspiration", "Travel inspiration",
        "Trips and destinations: inspire, then make choosing and booking easy.",
        (_b(_R.HERO, "hero.immersive", "The place, full-bleed."),
         _b(_R.CATEGORIES, "gallery.grid gallery.carousel", "Destinations as an image-led choice."),
         _b(_R.PRODUCT_STORY, "feature_grid.alternating media.overlay", "What a journey is like."),
         _b(_R.FEATURED, "collection.media", "Trips with dates and price."),
         _b(_R.REVIEWS, "testimonials.cards", "Travellers' accounts."),
         _b(_R.ACTION, "cta.split", "Plan or book, with reassurance beside it."),
         _FOOT)),
    NarrativeArc(
        "hospitality_booking", "Hospitality booking",
        "A hotel, restaurant or venue: atmosphere, what is offered, reserve.",
        (_b(_R.HERO, "hero.immersive hero.editorial", "The place itself, with a reserve action."),
         _b(_R.PRODUCT_STORY, "media.image_right media.image_left", "What staying or dining here is like."),
         _b(_R.GALLERY, "gallery.editorial gallery.masonry", "Rooms, tables, details."),
         _b(_R.FEATURED, "collection.media feature_grid.alternating", "Rooms, menus or experiences."),
         _b(_R.REVIEWS, "testimonials.spotlight", "A guest's words."),
         _b(_R.ACTION, "cta.split", "Reserve, with location and hours."),
         _FOOT)),
    NarrativeArc(
        "editorial_story", "Editorial story",
        "The page is read like an article or publication.",
        (_b(_R.HERO, "hero.editorial", "A headline and a photograph, set like a cover."),
         _b(_R.PRODUCT_STORY, "media.image_right media.image_left", "The opening argument in a text column beside an image."),
         _b(_R.GALLERY, "gallery.editorial", "Images with captions."),
         _b(_R.FEATURED, "media.overlay feature_grid.alternating", "A second movement of the story."),
         _b(_R.EVIDENCE, "stats.inline testimonials.spotlight", "A pull quote or a few figures."),
         _b(_R.ACTION, "cta.centered", "What to read or do next."),
         _FOOT),
        "Asymmetric columns; no bordered cards."),
    NarrativeArc(
        "lookbook", "Lookbook",
        "A collection presented as imagery before it is a shop.",
        (_b(_R.HERO, "hero.immersive hero.editorial", "The campaign image."),
         _b(_R.GALLERY, "gallery.editorial gallery.masonry", "The collection as looks."),
         _b(_R.PRODUCT_STORY, "media.overlay media.image_left", "The idea of the season."),
         _b(_R.FEATURED, "collection.media gallery.carousel", "Pieces, with price."),
         _b(_R.ACTION, "cta.split", "Shop the collection."),
         _FOOT)),
    NarrativeArc(
        "portfolio_showcase", "Portfolio showcase",
        "A person's or studio's work is the content.",
        (_b(_R.HERO, "hero.editorial hero.centered", "Who this is and what they make, briefly."),
         _b(_R.GALLERY, "gallery.editorial gallery.masonry gallery.grid", "Selected work, large."),
         _b(_R.FEATURED, "media.image_right media.overlay", "One project in depth."),
         _b(_R.PEOPLE, "media.image_left stats.inline", "The practice: approach, clients, recognition."),
         _b(_R.SOCIAL_PROOF, "testimonials.spotlight logo_cloud.static", "A client's words."),
         _b(_R.ACTION, "cta.centered", "Start a project."),
         _FOOT),
        "No feature grids, no pricing. The interface recedes behind the work."),
    NarrativeArc(
        "agency_capability", "Agency capability",
        "An agency selling its thinking and its results.",
        (_b(_R.HERO, "hero.editorial hero.centered", "A statement at display size."),
         _b(_R.TRUST, "logo_cloud.marquee logo_cloud.static", "Clients, moving."),
         _b(_R.GALLERY, "gallery.editorial gallery.masonry", "Case studies with results."),
         _b(_R.FEATURES, "feature_grid.list feature_grid.alternating", "What the agency does, without generic icons."),
         _b(_R.PROCESS, "steps.timeline steps.numbered", "How an engagement runs."),
         _b(_R.EVIDENCE, "stats.inline testimonials.spotlight", "Outcomes in figures."),
         _b(_R.ACTION, "cta.centered cta.split", "Start a conversation."),
         _FOOT)),
    NarrativeArc(
        "corporate_profile", "Corporate profile",
        "An established organisation presenting itself to customers, partners and candidates.",
        (_b(_R.HERO, "hero.split hero.immersive", "What the organisation does and for whom."),
         _b(_R.EVIDENCE, "stats.inline", "Scale and history in a few figures."),
         _b(_R.FEATURES, "feature_grid.alternating feature_grid.bento", "Business areas or services."),
         _b(_R.TRUST, "logo_cloud.static testimonials.spotlight", "Clients and partners."),
         _b(_R.PEOPLE, "media.image_left feature_grid.list", "Leadership, values, careers."),
         _b(_R.ACTION, "cta.banner cta.split", "Get in touch."),
         _FOOT)),
    NarrativeArc(
        "education_enrolment", "Education enrolment",
        "Courses or programmes people enrol in.",
        (_b(_R.HERO, "hero.split hero.centered", "What you will be able to do afterwards."),
         _b(_R.EVIDENCE, "stats.inline logo_cloud.static", "Outcomes: learners, completion, where they went."),
         _b(_R.CATALOGUE, "collection.media feature_grid.bento", "Courses or tracks."),
         _b(_R.PROCESS, "steps.timeline steps.numbered", "The path: what you learn, how long, what you get."),
         _b(_R.PEOPLE, "testimonials.cards media.image_right", "Learners and teachers."),
         _b(_R.PRICING, "pricing comparison", "Cost and what is included."),
         _b(_R.QUESTIONS, "faq", "What applicants ask."),
         _b(_R.ACTION, "cta.centered", "Enrol or try a lesson."),
         _FOOT)),
    NarrativeArc(
        "consumer_app", "Consumer app",
        "An app for everyone, usually on a phone.",
        (_b(_R.HERO, "hero.split hero.product", "The benefit in a few friendly words, with the app in view."),
         _b(_R.FEATURES, "feature_grid.alternating feature_grid.bento", "Three moments of use, each shown."),
         _b(_R.PROCESS, "steps.cards steps.numbered", "Getting started in under a minute."),
         _b(_R.REVIEWS, "testimonials.cards stats.inline", "Ratings and real users."),
         _b(_R.ACTION, "cta.centered", "Download."),
         _FOOT)),
    NarrativeArc(
        "entertainment_hype", "Entertainment hype",
        "A game, show or event: excitement is the product.",
        (_b(_R.HERO, "hero.immersive", "Key art across the whole view, one action."),
         _b(_R.PRODUCT_STORY, "media.overlay feature_grid.alternating", "The world or premise."),
         _b(_R.GALLERY, "gallery.carousel gallery.masonry", "Screens, scenes, characters."),
         _b(_R.FEATURES, "feature_grid.bento", "Modes, features, what is new."),
         _b(_R.SOCIAL_PROOF, "stats.inline logo_cloud.marquee testimonials.cards", "Players, scores, press."),
         _b(_R.ACTION, "cta.centered", "Play, watch or get tickets."),
         _FOOT)),
    NarrativeArc(
        "media_front_page", "Media front page",
        "Much content, ranked: the front of a publication or channel.",
        (_b(_R.HERO, "hero.editorial hero.split", "The lead story, far larger than the rest."),
         _b(_R.FEATURED, "collection.media gallery.editorial", "The next most important items."),
         _b(_R.CATEGORIES, "gallery.grid feature_grid.list", "Sections of the publication."),
         _b(_R.CATALOGUE, "collection.media", "The latest, dense but scannable."),
         _b(_R.ACTION, "cta.banner", "Subscribe."),
         _FOOT)),
    NarrativeArc(
        "cause_appeal", "Cause appeal",
        "A nonprofit or community asking for support.",
        (_b(_R.HERO, "hero.immersive hero.split", "Who is helped, shown as people."),
         _b(_R.PROBLEM, "media.image_left stats.inline", "The need, honestly."),
         _b(_R.SOLUTION, "feature_grid.alternating steps.timeline", "What the organisation does about it."),
         _b(_R.EVIDENCE, "stats.inline testimonials.spotlight", "Impact in figures and one story."),
         _b(_R.ACTION, "cta.split cta.centered", "Give, volunteer or join."),
         _FOOT)),
)  # fmt: skip


class NarrativeRegistry:
    def __init__(self, arcs: Iterable[NarrativeArc] = _ARCS) -> None:
        self._arcs = {arc.id: arc for arc in arcs}

    def all(self) -> tuple[NarrativeArc, ...]:
        return tuple(self._arcs.values())

    def get(self, arc_id: str) -> NarrativeArc | None:
        return self._arcs.get(arc_id)

    def candidates(self, ranked_ids: Sequence[str], limit: int = 3) -> list[NarrativeArc]:
        """The first ``limit`` known arcs of ``ranked_ids`` (an archetype blend's ranking)."""
        found = [self._arcs[arc_id] for arc_id in ranked_ids if arc_id in self._arcs]
        return found[:limit] or [self._arcs["saas_conversion"]]


@lru_cache
def build_default_narrative_registry() -> NarrativeRegistry:
    return NarrativeRegistry()


# --- What generic looks like -----------------------------------------------------------

# The component kinds, in order, of the page every generator produces by default.
_DEFAULT_SKELETON = ("hero", "feature_grid", "testimonials", "pricing", "cta")
_CARD_GRIDS = frozenset({"feature_grid", "testimonials", "pricing", "stats", "steps", "collection"})
MAX_CARD_GRID_RUN = 2
MAX_SAME_KIND = 2
MIN_DISTINCT_KINDS = 4


def kind_of(pattern_or_type: str) -> str:
    """``feature_grid.bento`` and ``feature_grid`` are the same kind of section."""
    return pattern_or_type.split(".", 1)[0]


def _is_subsequence(needle: Sequence[str], haystack: Sequence[str]) -> bool:
    remaining = iter(haystack)
    return all(item in remaining for item in needle)


def generic_findings(sections: Sequence[str], *, title: str = "This page") -> list[str]:
    """Why a marketing page's section order reads as a default template.

    ``sections`` are pattern ids or component types in page order. Each finding
    says what is generic and what to do instead; an empty list means the
    structure shows decisions.
    """
    kinds = [kind_of(section) for section in sections if kind_of(section) != "footer"]
    variants = [section for section in sections if "." in section]
    findings: list[str] = []
    if len(kinds) < 3:
        return findings
    body = [kind for kind in kinds if kind != "logo_cloud"]
    extra = len(body) - len(_DEFAULT_SKELETON)
    if _is_subsequence(_DEFAULT_SKELETON, body) and extra <= 1:
        findings.append(
            f"{title} is the default template (hero, feature cards, testimonials, pricing, "
            "call to action). Build it from a narrative arc for this product instead: decide "
            "what a visitor must believe at each step and give every step its own kind of "
            "section."
        )
    run, longest = 1, 1
    for previous, current in pairwise(kinds):
        both_grids = previous in _CARD_GRIDS and current in _CARD_GRIDS
        run = run + 1 if both_grids else 1
        longest = max(longest, run)
    if longest > MAX_CARD_GRID_RUN:
        findings.append(
            f"{title} has {longest} card-grid sections in a row, which reads as one repeated "
            "block. Put a full-width image, a split media section or a single large statement "
            "between them."
        )
    counts = Counter(kinds)
    repeated = sorted(kind for kind, count in counts.items() if count > MAX_SAME_KIND)
    if repeated:
        findings.append(
            f"{title} uses the same kind of section more than twice ({', '.join(repeated)}). "
            "Say it once, well, or change the form the second time."
        )
    grid_variants = [v for v in variants if v == "feature_grid.grid"]
    if len(grid_variants) > 1:
        findings.append(
            f"{title} has {len(grid_variants)} plain grids of equal feature cards. Keep at most "
            "one; use a bento of unequal tiles or alternating image-and-text for the other."
        )
    if len(kinds) >= 6 and len(set(kinds)) < MIN_DISTINCT_KINDS:
        findings.append(
            f"{title} has {len(kinds)} sections but only {len(set(kinds))} kinds of them. Vary "
            "the rhythm: alternate dense and open, text-led and image-led."
        )
    return findings
