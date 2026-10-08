"""Design archetypes: kinds of website, and what each one implies.

An archetype is not a template. It is a position on a few axes a designer
reasons along (how dense, how energetic, how warm, how formal, how decorated,
how image-led) plus the styles, palettes and structures that tend to serve it.
A product is rarely one archetype: ``ArchetypeBlend`` mixes several by weight
("60% premium technology, 25% editorial, 15% healthcare") and the mixed
position is what the rest of design intelligence works from.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache

from app.domains.generative_ui.schemas import Effect

_E = Effect
MAX_BLEND_PARTS = 4
MIN_WEIGHT = 10
_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class Traits:
    """Where a design sits on six axes, each from 0 to 1."""

    density: float  # 0 airy, one idea per view .. 1 dense, much on screen
    energy: float  # 0 still and quiet .. 1 loud, fast, saturated
    warmth: float  # 0 cool and technical .. 1 warm and human
    formality: float  # 0 playful .. 1 formal
    ornament: float  # 0 plain .. 1 decorated (gradients, glow, effects)
    imagery: float  # 0 no pictures .. 1 pictures carry the page

    def as_dict(self) -> dict[str, float]:
        return {
            "density": self.density,
            "energy": self.energy,
            "warmth": self.warmth,
            "formality": self.formality,
            "ornament": self.ornament,
            "imagery": self.imagery,
        }

    def describe(self) -> str:
        """The position in words, for a prompt."""

        def word(value: float, low: str, middle: str, high: str) -> str:
            return low if value < 0.36 else high if value > 0.64 else middle

        return ", ".join(
            [
                word(self.density, "airy", "balanced density", "information-dense"),
                word(self.energy, "calm", "measured energy", "high-energy"),
                word(self.warmth, "cool and technical", "neutral temperature", "warm and human"),
                word(self.formality, "informal", "professional", "formal"),
                word(self.ornament, "plain", "lightly decorated", "richly decorated"),
                word(self.imagery, "type-led", "some imagery", "image-led"),
            ]
        )


@dataclass(frozen=True, slots=True)
class Archetype:
    id: str
    name: str
    essence: str
    # Lower-case words that suggest this archetype when they appear in a brief.
    keywords: tuple[str, ...]
    traits: Traits
    # Ids of visual styles (design systems), best first.
    styles: tuple[str, ...]
    palettes: tuple[str, ...]
    heading_fonts: tuple[str, ...]
    imagery: str
    effects: tuple[Effect, ...]
    # What a designer does for this kind of site, and what gives an amateur away.
    signature: tuple[str, ...]
    avoid: tuple[str, ...]
    # Ids of narrative arcs (see ``architecture``) that suit its pages, best first.
    arcs: tuple[str, ...]


def _a(
    archetype_id: str,
    name: str,
    essence: str,
    keywords: tuple[str, ...],
    traits: tuple[float, float, float, float, float, float],
    *,
    styles: tuple[str, ...],
    palettes: tuple[str, ...],
    fonts: tuple[str, ...],
    imagery: str,
    effects: tuple[Effect, ...] = (),
    signature: tuple[str, ...],
    avoid: tuple[str, ...],
    arcs: tuple[str, ...],
) -> Archetype:
    return Archetype(
        archetype_id, name, essence, keywords, Traits(*traits), styles, palettes, fonts,
        imagery, effects, signature, avoid, arcs,
    )  # fmt: skip


#                                   density energy warmth formal ornament imagery
_ARCHETYPES: tuple[Archetype, ...] = (
    _a("premium", "Premium", "Confident restraint: fewer things, each given room and finish.",
       ("premium", "high-end", "refined", "polished", "flagship"),
       (0.30, 0.35, 0.45, 0.65, 0.35, 0.70),
       styles=("premium_saas", "luxury", "editorial", "ai_native"),
       palettes=("stone_ink", "mono_minimal", "noir_gold", "indigo_mist"),
       fonts=("geometric", "serif", "sans"), imagery="product",
       effects=(_E.REVEAL, _E.SPOTLIGHT, _E.PARALLAX),
       signature=("one idea per section, with generous space around it",
                  "large, well-lit product imagery", "a single restrained accent colour"),
       avoid=("many accent colours", "dense grids of small cards", "bouncy or constant motion"),
       arcs=("product_launch", "brand_story", "saas_conversion")),
    _a("luxury", "Luxury", "Scarcity and craft: silence, serif type and cinematic images.",
       ("luxury", "couture", "jewellery", "jewelry", "watch", "exclusive", "bespoke", "atelier"),
       (0.12, 0.18, 0.55, 0.90, 0.15, 0.90),
       styles=("luxury", "editorial"),
       palettes=("noir_gold", "stone_ink", "aubergine_gold", "mocha_mousse"),
       fonts=("serif",), imagery="photography",
       effects=(_E.REVEAL, _E.PARALLAX),
       signature=("very wide margins and few words", "full-bleed cinematic photography",
                  "serif display type at regular weight", "slow, almost imperceptible reveals"),
       avoid=("neon or saturated colour", "bounce or playful motion", "heavy shadows",
              "several gradients", "badges, counters and urgency devices"),
       arcs=("brand_story", "lookbook", "product_launch")),
    _a("editorial", "Editorial", "A publication's eye: type hierarchy, columns and pacing.",
       ("editorial", "magazine", "journal", "publication", "story", "longform", "essay"),
       (0.40, 0.30, 0.55, 0.70, 0.12, 0.75),
       styles=("editorial", "luxury", "creative_agency"),
       palettes=("stone_ink", "warm_sand", "mono_minimal", "mocha_mousse"),
       fonts=("serif", "grotesk"), imagery="photography",
       effects=(_E.REVEAL, _E.PARALLAX, _E.NOISE),
       signature=("asymmetric columns (7/5, 8/4)", "large headlines with small metadata",
                  "photographs treated as content, with captions"),
       avoid=("bordered cards in grids", "icon-in-a-circle feature lists", "gradients"),
       arcs=("editorial_story", "brand_story", "lookbook")),
    _a("minimal", "Minimal", "Only what is needed; alignment and whitespace do the work.",
       ("minimal", "minimalist", "simple", "clean", "essential"),
       (0.22, 0.20, 0.45, 0.60, 0.05, 0.35),
       styles=("modern_minimal", "editorial", "ai_native"),
       palettes=("mono_minimal", "stone_ink", "indigo_mist"),
       fonts=("sans", "geometric"), imagery="none",
       effects=(_E.REVEAL,),
       signature=("one accent used sparingly", "hairlines instead of boxes",
                  "a strict type scale with few sizes"),
       avoid=("decorative gradients", "shadows", "more than one effect", "filler sections"),
       arcs=("focused_pitch", "saas_conversion", "portfolio_showcase")),
    _a("corporate", "Corporate", "An established organisation: clear, credible, complete.",
       ("corporate", "company", "group", "holding", "consulting", "firm", "institution"),
       (0.50, 0.30, 0.45, 0.85, 0.15, 0.55),
       styles=("enterprise", "modern_minimal", "premium_saas"),
       palettes=("blue_white", "arctic_cyan", "mono_minimal", "stone_ink"),
       fonts=("sans", "geometric"), imagery="photography",
       effects=(_E.REVEAL, _E.COUNTER),
       signature=("clear top navigation with the organisation's main areas",
                  "figures and client logos as proof", "photographs of real people at work"),
       avoid=("playful illustration", "neon", "experimental layouts that hide information"),
       arcs=("corporate_profile", "enterprise_solution")),
    _a("enterprise", "Enterprise", "Software a procurement team trusts: sober and thorough.",
       ("enterprise", "b2b", "compliance", "erp", "procurement", "governance", "workforce"),
       (0.60, 0.25, 0.30, 0.90, 0.08, 0.30),
       styles=("enterprise", "premium_saas", "compact_pro", "modern_minimal"),
       palettes=("blue_white", "arctic_cyan", "slate_dark", "mono_minimal"),
       fonts=("sans",), imagery="product",
       effects=(_E.REVEAL,),
       signature=("security, compliance and integration shown early",
                  "product screens instead of illustration", "named customers and outcomes"),
       avoid=("effects of any kind beyond a quiet reveal", "vivid gradients", "casual copy"),
       arcs=("enterprise_solution", "saas_conversion", "security_assurance")),
    _a("saas", "SaaS", "A product you can try today: show it, prove it, start.",
       ("saas", "software", "platform", "subscription", "crm", "productivity", "workflow"),
       (0.48, 0.45, 0.45, 0.60, 0.35, 0.50),
       styles=("premium_saas", "modern_minimal", "ai_native", "soft"),
       palettes=("indigo_mist", "stone_ink", "arctic_cyan", "digital_lavender", "mono_minimal"),
       fonts=("geometric", "sans"), imagery="product",
       effects=(_E.REVEAL, _E.HOVER_LIFT, _E.SPOTLIGHT, _E.COUNTER),
       signature=("the product on screen within the first view",
                  "bento sections of unequal tiles", "one primary action repeated"),
       avoid=("three identical feature cards in a row, twice", "stock photos of handshakes",
              "purple gradients by default"),
       arcs=("saas_conversion", "product_launch", "focused_pitch")),
    _a("ai_saas", "AI SaaS", "An AI product: the interaction itself is the hero.",
       ("ai", "artificial intelligence", "llm", "copilot", "assistant", "agent", "gpt",
        "machine learning", "generative"),
       (0.42, 0.45, 0.40, 0.55, 0.40, 0.40),
       styles=("ai_native", "premium_saas", "dark_futuristic", "glass"),
       palettes=("stone_ink", "mono_minimal", "arctic_cyan", "indigo_mist", "violet_night"),
       fonts=("geometric", "grotesk"), imagery="abstract",
       effects=(_E.SPOTLIGHT, _E.REVEAL, _E.GRADIENT_MESH, _E.GLOW),
       signature=("a prompt, a conversation or an agent at work shown as the product",
                  "what the AI was given and where its answer came from",
                  "calm surfaces so generated content stands out"),
       avoid=("neon purple on black because it is AI", "glow on every card",
              "robots and brains as imagery"),
       arcs=("ai_product", "saas_conversion", "product_launch")),
    _a("ecommerce", "E-commerce", "A shop: find it, judge it, buy it.",
       ("shop", "store", "ecommerce", "e-commerce", "retail", "cart", "checkout", "products",
        "catalog", "catalogue"),
       (0.78, 0.55, 0.55, 0.45, 0.20, 0.90),
       styles=("ecommerce", "modern_minimal", "soft"),
       palettes=("mono_minimal", "stone_ink", "warm_sand", "coral_sunset"),
       fonts=("sans", "geometric"), imagery="product",
       effects=(_E.HOVER_LIFT, _E.REVEAL),
       signature=("category navigation always in reach", "compact product cards with price",
                  "filters beside results", "one unmistakable buy action"),
       avoid=("long brand stories before any product", "decorative effects on product cards",
              "low-contrast prices"),
       arcs=("commerce_discovery", "product_launch")),
    _a("marketplace", "Marketplace", "Two sides meeting: search first, trust everywhere.",
       ("marketplace", "listings", "sellers", "buyers", "hosts", "freelancers", "gig",
        "classifieds"),
       (0.75, 0.50, 0.60, 0.45, 0.15, 0.80),
       styles=("ecommerce", "modern_minimal", "soft", "travel"),
       palettes=("mono_minimal", "warm_sand", "peach_fuzz", "blue_white"),
       fonts=("sans", "rounded"), imagery="photography",
       effects=(_E.HOVER_LIFT, _E.REVEAL),
       signature=("search or browse as the first thing on the page",
                  "ratings, reviews and verification on every listing",
                  "a separate path for the supply side"),
       avoid=("hiding search below a brand hero", "listings without price or rating"),
       arcs=("marketplace_two_sided", "commerce_discovery")),
    _a("healthcare", "Healthcare", "Care and evidence: calm, legible, trustworthy.",
       ("health", "healthcare", "medical", "clinic", "clinical", "hospital", "patient",
        "diagnostic", "diagnosis", "pharma", "therapy", "telehealth", "doctor"),
       (0.40, 0.22, 0.65, 0.80, 0.12, 0.60),
       styles=("wellness", "premium_saas", "modern_minimal", "soft"),
       palettes=("sage_garden", "arctic_cyan", "blue_white", "emerald", "stone_ink"),
       fonts=("sans", "geometric", "serif"), imagery="photography",
       effects=(_E.REVEAL, _E.COUNTER),
       signature=("trust signals before claims: certification, clinical partners, evidence",
                  "plain language and large readable type", "people, not stock anatomy"),
       avoid=("neon or dark gaming aesthetics", "playful bounce", "alarming reds as accent",
              "unsupported superlatives"),
       arcs=("healthcare_trust", "enterprise_solution", "saas_conversion")),
    _a("fintech", "Fintech", "Money: precision, calm colour and visible safeguards.",
       ("fintech", "bank", "banking", "payments", "invest", "trading", "wallet", "insurance",
        "lending", "accounting", "finance"),
       (0.52, 0.32, 0.35, 0.82, 0.18, 0.35),
       styles=("fintech", "premium_saas", "enterprise", "modern_minimal"),
       palettes=("emerald", "arctic_cyan", "blue_white", "slate_dark", "ocean_depth"),
       fonts=("sans", "geometric"), imagery="product",
       effects=(_E.COUNTER, _E.REVEAL),
       signature=("tabular figures and exact numbers", "security and regulation stated plainly",
                  "the product's own screens as imagery"),
       avoid=("casino colours", "flashing motion", "vague claims about returns"),
       arcs=("fintech_trust", "saas_conversion", "enterprise_solution")),
    _a("education", "Education", "Learning: encouraging, structured and easy to start.",
       ("education", "course", "learning", "school", "university", "students", "tutor",
        "bootcamp", "academy", "edtech", "curriculum"),
       (0.50, 0.50, 0.75, 0.45, 0.30, 0.60),
       styles=("soft", "playful", "modern_minimal", "premium_saas"),
       palettes=("digital_lavender", "peach_fuzz", "sage_garden", "blue_white", "indigo_mist"),
       fonts=("rounded", "geometric", "sans"), imagery="illustration",
       effects=(_E.REVEAL, _E.HOVER_LIFT, _E.COUNTER),
       signature=("a clear path: what you learn, how long, what you get",
                  "outcomes and learner stories", "friendly rounded shapes"),
       avoid=("intimidating dense tables up front", "corporate stock imagery"),
       arcs=("education_enrolment", "saas_conversion")),
    _a("developer_tool", "Developer Tool", "For engineers: precise, fast, show the code.",
       ("developer", "api", "sdk", "cli", "devops", "open source", "infrastructure",
        "database", "framework", "deploy", "observability"),
       (0.60, 0.40, 0.20, 0.55, 0.20, 0.15),
       styles=("developer_tool", "dark_futuristic", "modern_minimal"),
       palettes=("graphite_lime", "slate_dark", "mono_minimal", "midnight_teal"),
       fonts=("mono", "grotesk", "sans"), imagery="none",
       effects=(_E.GRID, _E.GLOW, _E.REVEAL),
       signature=("a command or code sample in the first view", "exact, measurable claims",
                  "documentation and pricing one click away"),
       avoid=("stock photography", "marketing superlatives", "decorative illustration"),
       arcs=("developer_adoption", "saas_conversion")),
    _a("cybersecurity", "Cybersecurity", "Protection: serious, exact, no theatre.",
       ("security", "cybersecurity", "threat", "soc", "zero trust", "encryption",
        "vulnerability", "identity", "fraud"),
       (0.55, 0.35, 0.15, 0.88, 0.15, 0.20),
       styles=("enterprise", "dark_futuristic", "developer_tool", "premium_saas"),
       palettes=("slate_dark", "midnight_teal", "ocean_depth", "arctic_cyan", "blue_white"),
       fonts=("sans", "grotesk"), imagery="abstract",
       effects=(_E.GRID, _E.REVEAL),
       signature=("certifications and coverage stated up front",
                  "how it works as a clear sequence", "calm dark or cool light surfaces"),
       avoid=("hackers in hoodies", "matrix green clichés", "playful motion", "glow everywhere"),
       arcs=("security_assurance", "enterprise_solution")),
    _a("deep_tech", "Deep Tech", "Hard science made legible: the technology is the story.",
       ("deep tech", "deeptech", "semiconductor", "quantum", "biotech", "robotics", "space",
        "materials", "energy", "hardware", "photonics", "lab"),
       (0.38, 0.40, 0.25, 0.75, 0.30, 0.65),
       styles=("dark_futuristic", "premium_saas", "editorial", "ai_native"),
       palettes=("midnight_teal", "ocean_depth", "stone_ink", "arctic_cyan", "violet_night"),
       fonts=("grotesk", "geometric"), imagery="abstract",
       effects=(_E.GRID, _E.GLOW, _E.REVEAL, _E.PARALLAX),
       signature=("the breakthrough explained in one plain sentence",
                  "diagrams and close-up imagery of the technology",
                  "credibility: team, papers, partners, funding"),
       avoid=("science-fiction clichés", "claims without evidence", "consumer-style playfulness"),
       arcs=("deep_tech_credibility", "product_launch", "research_publication")),
    _a("research", "Research", "Scholarly: findings, methods and people, soberly presented.",
       ("research", "institute", "paper", "publication", "study", "scientific",
        "academic", "laboratory", "dataset"),
       (0.55, 0.18, 0.40, 0.88, 0.05, 0.35),
       styles=("editorial", "modern_minimal", "enterprise"),
       palettes=("stone_ink", "mono_minimal", "arctic_cyan", "blue_white"),
       fonts=("serif", "sans"), imagery="none",
       effects=(_E.REVEAL,),
       signature=("findings before fanfare", "readable long text with a clear measure",
                  "figures, citations and the people behind the work"),
       avoid=("marketing language", "effects", "decorative imagery unrelated to the work"),
       arcs=("research_publication", "deep_tech_credibility", "editorial_story")),
    _a("portfolio", "Portfolio", "One person's or studio's work: the work is the design.",
       ("portfolio", "designer", "photographer", "architect", "artist", "freelance", "showreel",
        "case studies"),
       (0.28, 0.40, 0.55, 0.50, 0.15, 0.92),
       styles=("editorial", "creative_agency", "modern_minimal"),
       palettes=("mono_minimal", "stone_ink", "warm_sand"),
       fonts=("serif", "grotesk"), imagery="photography",
       effects=(_E.REVEAL, _E.PARALLAX, _E.HOVER_LIFT),
       signature=("large project images with few words", "a strong, simple index of work",
                  "the interface recedes behind the work"),
       avoid=("feature grids and pricing tables", "interface chrome competing with the work"),
       arcs=("portfolio_showcase", "editorial_story")),
    _a("agency", "Agency", "Capability with attitude: oversized type and proof of work.",
       ("agency", "studio", "creative", "branding", "marketing agency", "production"),
       (0.35, 0.72, 0.55, 0.35, 0.40, 0.80),
       styles=("creative_agency", "neo_brutalist", "editorial"),
       palettes=("mono_minimal", "citrus_pop", "coral_sunset", "graphite_lime"),
       fonts=("grotesk",), imagery="photography",
       effects=(_E.MARQUEE, _E.REVEAL, _E.PARALLAX, _E.HOVER_LIFT, _E.NOISE),
       signature=("a statement headline at display size", "case studies with results",
                  "asymmetric layouts and a moving element"),
       avoid=("timid type", "generic service icons", "corporate blue"),
       arcs=("agency_capability", "portfolio_showcase")),
    _a("startup", "Startup", "A new idea, pitched clearly: problem, answer, momentum.",
       ("startup", "launch", "seed", "founder", "early access", "waitlist", "beta", "mvp"),
       (0.40, 0.60, 0.55, 0.42, 0.40, 0.50),
       styles=("premium_saas", "ai_native", "soft", "playful", "modern_minimal"),
       palettes=("indigo_mist", "digital_lavender", "peach_fuzz", "arctic_cyan", "stone_ink"),
       fonts=("geometric", "grotesk"), imagery="product",
       effects=(_E.REVEAL, _E.SPOTLIGHT, _E.GRADIENT_MESH, _E.COUNTER),
       signature=("the problem named in the visitor's words", "one bold claim and one action",
                  "early proof: users, backers, numbers"),
       avoid=("pretending to be an enterprise", "long navigation", "empty testimonial slots"),
       arcs=("focused_pitch", "saas_conversion", "product_launch")),
    _a("consumer", "Consumer", "For everyone: immediate, friendly and mobile-first.",
       ("consumer", "app", "mobile app", "lifestyle", "habit", "social", "personal", "family",
        "dating", "fitness"),
       (0.45, 0.65, 0.80, 0.25, 0.45, 0.70),
       styles=("soft", "playful", "glass", "modern_minimal"),
       palettes=("peach_fuzz", "coral_sunset", "digital_lavender", "sage_garden"),
       fonts=("rounded", "geometric"), imagery="illustration",
       effects=(_E.REVEAL, _E.HOVER_LIFT, _E.GRADIENT_MESH, _E.COUNTER),
       signature=("the benefit in a few friendly words", "the app shown in someone's hand",
                  "ratings and download actions"),
       avoid=("jargon", "dense comparison tables", "cold corporate palettes"),
       arcs=("consumer_app", "focused_pitch")),
    _a("gaming", "Gaming", "Hype: dark, loud, kinetic.",
       ("game", "gaming", "esports", "tournament", "streamer", "guild", "rpg", "arcade"),
       (0.55, 0.92, 0.40, 0.12, 0.85, 0.85),
       styles=("dark_futuristic", "glass", "neo_brutalist", "creative_agency"),
       palettes=("violet_night", "graphite_lime", "ocean_depth", "midnight_teal"),
       fonts=("grotesk",), imagery="illustration",
       effects=(_E.GLOW, _E.ANIMATED_GRADIENT, _E.SPOTLIGHT, _E.MARQUEE, _E.PARALLAX),
       signature=("key art across the whole first view", "bold, heavy display type",
                  "motion and glow on the main action"),
       avoid=("polite corporate layouts", "pastel palettes", "long paragraphs"),
       arcs=("entertainment_hype", "product_launch")),
    _a("media", "Media", "Much content, well ranked: the front page of something.",
       ("news", "media", "streaming", "podcast", "video", "blog", "newsletter", "broadcast",
        "articles"),
       (0.80, 0.50, 0.50, 0.55, 0.15, 0.85),
       styles=("editorial", "modern_minimal", "compact_pro"),
       palettes=("mono_minimal", "stone_ink", "slate_dark", "coral_sunset"),
       fonts=("serif", "grotesk", "sans"), imagery="photography",
       effects=(_E.REVEAL, _E.HOVER_LIFT),
       signature=("a lead story much larger than the rest", "clear sections and timestamps",
                  "dense lists that stay scannable"),
       avoid=("every item the same size", "marketing heroes in front of content"),
       arcs=("media_front_page", "editorial_story")),
    _a("fashion", "Fashion", "Desire: the photograph leads, the interface whispers.",
       ("fashion", "apparel", "clothing", "collection", "lookbook", "streetwear", "sneakers",
        "beauty", "cosmetics"),
       (0.35, 0.60, 0.55, 0.55, 0.20, 0.97),
       styles=("editorial", "luxury", "creative_agency", "ecommerce"),
       palettes=("mono_minimal", "stone_ink", "noir_gold", "coral_sunset"),
       fonts=("serif", "grotesk"), imagery="photography",
       effects=(_E.REVEAL, _E.PARALLAX, _E.MARQUEE),
       signature=("campaign imagery at full width", "small uppercase labels, large headlines",
                  "the collection as a lookbook before it is a grid"),
       avoid=("icons and feature lists", "busy backgrounds behind photographs", "many colours"),
       arcs=("lookbook", "commerce_discovery", "brand_story")),
    _a("automotive", "Automotive", "The machine as hero: cinematic, engineered, precise.",
       ("car", "automotive", "vehicle", "ev", "motorcycle", "dealership", "mobility"),
       (0.30, 0.55, 0.35, 0.72, 0.35, 0.95),
       styles=("luxury", "dark_futuristic", "editorial", "premium_saas"),
       palettes=("noir_gold", "mono_minimal", "slate_dark", "stone_ink"),
       fonts=("grotesk", "geometric", "serif"), imagery="photography",
       effects=(_E.PARALLAX, _E.REVEAL, _E.COUNTER),
       signature=("one vehicle, full-bleed, in dramatic light", "specifications as large figures",
                  "a configure or book-a-drive action"),
       avoid=("cluttered offers above the vehicle", "cartoonish illustration"),
       arcs=("product_launch", "brand_story")),
    _a("real_estate", "Real Estate", "Places to live or work: search, see, enquire.",
       ("real estate", "property", "apartments", "homes", "rental", "broker", "listing",
        "housing", "realty"),
       (0.60, 0.35, 0.65, 0.65, 0.15, 0.92),
       styles=("travel", "editorial", "modern_minimal", "ecommerce"),
       palettes=("stone_ink", "warm_sand", "sage_garden", "mono_minimal"),
       fonts=("serif", "sans"), imagery="photography",
       effects=(_E.REVEAL, _E.HOVER_LIFT, _E.PARALLAX),
       signature=("search by place and budget in the first view",
                  "large photographs with price, size and location",
                  "a map or neighbourhood context"),
       avoid=("listings without key facts", "abstract imagery instead of the property"),
       arcs=("listing_search", "marketplace_two_sided", "brand_story")),
    _a("travel", "Travel", "Somewhere else: inspire first, then make booking easy.",
       ("travel", "trip", "tour", "destination", "flights", "itinerary", "adventure",
        "tourism", "expedition"),
       (0.45, 0.50, 0.80, 0.45, 0.25, 0.97),
       styles=("travel", "editorial", "soft"),
       palettes=("warm_sand", "stone_ink", "ocean_depth", "sage_garden", "peach_fuzz"),
       fonts=("serif", "geometric"), imagery="photography",
       effects=(_E.PARALLAX, _E.REVEAL, _E.HOVER_LIFT),
       signature=("an immersive photograph of the place", "destinations as an image-led choice",
                  "reassurance near the booking action"),
       avoid=("forms before inspiration", "generic stock of airports", "cold palettes"),
       arcs=("travel_inspiration", "hospitality_booking")),
    _a("hospitality", "Hospitality", "A welcome: atmosphere, rooms or tables, reserve.",
       ("hotel", "resort", "restaurant", "cafe", "bar", "spa", "venue", "bed and breakfast",
        "dining", "hospitality"),
       (0.32, 0.30, 0.85, 0.62, 0.18, 0.95),
       styles=("travel", "luxury", "editorial", "wellness"),
       palettes=("warm_sand", "mocha_mousse", "stone_ink", "noir_gold", "sage_garden"),
       fonts=("serif",), imagery="photography",
       effects=(_E.REVEAL, _E.PARALLAX),
       signature=("atmospheric photography of the place itself",
                  "a reserve action always visible", "warm neutrals and serif headings"),
       avoid=("technology aesthetics", "dense tables", "bright saturated accents"),
       arcs=("hospitality_booking", "brand_story")),
    _a("product_launch", "Product Launch", "One product, one moment: build desire, then act.",
       ("launch", "introducing", "new product", "pre-order", "preorder", "unveil", "release",
        "announcement"),
       (0.22, 0.65, 0.45, 0.50, 0.50, 0.90),
       styles=("premium_saas", "dark_futuristic", "luxury", "glass", "creative_agency"),
       palettes=("mono_minimal", "noir_gold", "violet_night", "stone_ink", "ocean_depth"),
       fonts=("geometric", "grotesk"), imagery="product",
       effects=(_E.PARALLAX, _E.REVEAL, _E.SPOTLIGHT, _E.GLOW, _E.COUNTER),
       signature=("the product alone, very large", "a story told one beat per screen",
                  "a single action repeated at the end"),
       avoid=("navigation to many other things", "small product images", "feature dumps"),
       arcs=("product_launch", "brand_story")),
    # --- Modifiers: not industries, but qualities a brief asks for ------------------------
    _a("technology", "Technology", "Engineered and modern: precise geometry and cool light.",
       ("technology", "tech", "electronics", "device", "gadget", "sensor", "smart", "iot"),
       (0.40, 0.45, 0.25, 0.65, 0.30, 0.70),
       styles=("premium_saas", "dark_futuristic", "ai_native", "modern_minimal"),
       palettes=("stone_ink", "arctic_cyan", "mono_minimal", "ocean_depth", "slate_dark"),
       fonts=("geometric", "grotesk", "sans"), imagery="product",
       effects=(_E.REVEAL, _E.SPOTLIGHT, _E.GRID, _E.PARALLAX),
       signature=("the object or interface rendered crisply", "exact specifications",
                  "cool neutrals with one precise accent"),
       avoid=("warm rustic textures", "hand-drawn illustration"),
       arcs=("product_launch", "saas_conversion", "deep_tech_credibility")),
    _a("futuristic", "Futuristic", "Tomorrow, today: dark fields, luminous lines.",
       ("futuristic", "future", "cyber", "sci-fi", "neon", "web3", "crypto", "metaverse",
        "next-gen"),
       (0.40, 0.75, 0.15, 0.40, 0.80, 0.55),
       styles=("dark_futuristic", "glass"),
       palettes=("violet_night", "midnight_teal", "graphite_lime", "ocean_depth"),
       fonts=("grotesk", "geometric"), imagery="abstract",
       effects=(_E.GLOW, _E.GRID, _E.SPOTLIGHT, _E.ANIMATED_GRADIENT, _E.GLASS),
       signature=("a dark field with one luminous focal point", "thin lines and grids",
                  "glow reserved for what matters most"),
       avoid=("glow on everything", "light pastel palettes", "serif body text"),
       arcs=("product_launch", "ai_product", "entertainment_hype")),
    _a("playful", "Playful", "Fun on purpose: round, bright, bouncy.",
       ("playful", "fun", "kids", "children", "quirky", "colourful", "colorful", "cute",
        "toy", "party"),
       (0.45, 0.85, 0.90, 0.08, 0.60, 0.65),
       styles=("playful", "soft", "neo_brutalist"),
       palettes=("peach_fuzz", "coral_sunset", "citrus_pop", "digital_lavender"),
       fonts=("rounded",), imagery="illustration",
       effects=(_E.HOVER_LIFT, _E.REVEAL, _E.COUNTER, _E.GRADIENT_MESH, _E.MARQUEE),
       signature=("rounded shapes and bold friendly type", "illustration with character",
                  "motion that rewards interaction"),
       avoid=("grey corporate restraint", "thin light type", "long formal copy"),
       arcs=("consumer_app", "focused_pitch", "education_enrolment")),
    _a("wellness", "Wellness", "Slow down: natural colour, soft shapes, breathing room.",
       ("wellness", "yoga", "meditation", "mindfulness", "skincare", "organic", "nutrition",
        "self-care", "retreat"),
       (0.25, 0.18, 0.90, 0.50, 0.20, 0.85),
       styles=("wellness", "soft", "editorial"),
       palettes=("sage_garden", "peach_fuzz", "warm_sand", "mocha_mousse"),
       fonts=("serif", "rounded"), imagery="photography",
       effects=(_E.REVEAL,),
       signature=("muted natural colour", "unhurried spacing and soft imagery",
                  "gentle, reassuring copy"),
       avoid=("urgency devices", "hard edges and high contrast", "technical jargon"),
       arcs=("brand_story", "hospitality_booking", "consumer_app")),
    _a("nonprofit", "Nonprofit", "A cause: the people it serves, the difference, how to help.",
       ("nonprofit", "non-profit", "charity", "ngo", "foundation", "donate", "volunteer",
        "cause", "community"),
       (0.42, 0.40, 0.88, 0.60, 0.12, 0.85),
       styles=("soft", "editorial", "modern_minimal"),
       palettes=("sage_garden", "warm_sand", "emerald", "stone_ink"),
       fonts=("serif", "sans"), imagery="photography",
       effects=(_E.REVEAL, _E.COUNTER),
       signature=("real people and real outcomes", "impact in a few honest numbers",
                  "a clear way to give or join"),
       avoid=("slick sales language", "decorative effects", "stock imagery of anonymous hands"),
       arcs=("cause_appeal", "brand_story")),
)  # fmt: skip


@dataclass(frozen=True, slots=True)
class BlendPart:
    archetype: Archetype
    weight: int  # percent; the parts of a blend add up to 100


@dataclass(frozen=True, slots=True)
class ArchetypeBlend:
    """Several archetypes mixed by weight, heaviest first."""

    parts: tuple[BlendPart, ...]

    @property
    def lead(self) -> Archetype:
        return self.parts[0].archetype

    def weight_of(self, archetype_id: str) -> int:
        return next((p.weight for p in self.parts if p.archetype.id == archetype_id), 0)

    def weights(self) -> list[dict[str, int | str]]:
        return [{"id": part.archetype.id, "weight": part.weight} for part in self.parts]

    def label(self) -> str:
        return " + ".join(f"{part.weight}% {part.archetype.name}" for part in self.parts)

    def traits(self) -> Traits:
        """The weighted position of the blend on each axis."""

        def mixed(axis: str) -> float:
            total = sum(getattr(p.archetype.traits, axis) * p.weight for p in self.parts)
            return round(total / 100, 3)

        return Traits(*(mixed(axis) for axis in Traits.__dataclass_fields__))

    def ranked(self, attribute: str) -> list[str]:
        """Ids from every part's ``attribute`` list (styles, palettes, heading_fonts,
        arcs), ranked by weight and by position in each archetype's own preference."""
        scores: dict[str, float] = {}
        for part in self.parts:
            values: Sequence[str] = getattr(part.archetype, attribute)
            for index, value in enumerate(values):
                scores[value] = scores.get(value, 0.0) + part.weight * (1 - index / (len(values) + 1))
        return sorted(scores, key=lambda value: -scores[value])

    def score(self, attribute: str, value: str) -> float:
        """How strongly the blend favours ``value`` (0..1, relative to its favourite)."""
        scores: dict[str, float] = {}
        for part in self.parts:
            values: Sequence[str] = getattr(part.archetype, attribute)
            for index, candidate in enumerate(values):
                scores[candidate] = scores.get(candidate, 0.0) + part.weight * (
                    1 - index / (len(values) + 1)
                )
        best = max(scores.values(), default=0.0)
        return round(scores.get(value, 0.0) / best, 3) if best else 0.0

    def effects(self) -> list[Effect]:
        """Effects the blend has an affinity for, strongest first."""
        scores: dict[Effect, int] = {}
        for part in self.parts:
            for effect in part.archetype.effects:
                scores[effect] = scores.get(effect, 0) + part.weight
        return sorted(scores, key=lambda effect: -scores[effect])

    def signature(self, limit: int = 6) -> list[str]:
        return _weighted_lines(self.parts, "signature", limit)

    def avoid(self, limit: int = 8) -> list[str]:
        return _weighted_lines(self.parts, "avoid", limit)


def _weighted_lines(parts: Sequence[BlendPart], attribute: str, limit: int) -> list[str]:
    """Lines from each part in turn, heavier parts contributing more of theirs."""
    queues = [list(getattr(part.archetype, attribute)) for part in parts]
    quota = [max(1, round(limit * part.weight / 100)) for part in parts]
    lines: list[str] = []
    for queue, allowed in zip(queues, quota, strict=True):
        lines += queue[:allowed]
    return list(dict.fromkeys(lines))[:limit]


class ArchetypeRegistry:
    def __init__(self, archetypes: Iterable[Archetype] = _ARCHETYPES) -> None:
        self._archetypes = {archetype.id: archetype for archetype in archetypes}
        # "AI SaaS", "ai-saas" and "ai saas" all name the same archetype.
        self._aliases = {
            _SLUG.sub("", key): archetype.id
            for archetype in self._archetypes.values()
            for key in (archetype.id, archetype.name.lower())
        }

    def all(self) -> tuple[Archetype, ...]:
        return tuple(self._archetypes.values())

    def get(self, archetype_id: str) -> Archetype | None:
        return self._archetypes.get(archetype_id)

    def resolve(self, name: str) -> Archetype | None:
        """The archetype a model meant by ``name``, tolerating spelling and case."""
        key = _SLUG.sub("", name.lower())
        found = self._aliases.get(key)
        if found is None:
            # "premium technology" names two; the first known word wins.
            for word in re.split(r"[^a-z0-9]+", name.lower()):
                found = self._aliases.get(word)
                if found:
                    break
        return self._archetypes.get(found) if found else None

    def evidence(self, brief: str) -> dict[str, int]:
        """How many of each archetype's keywords appear in ``brief`` (only those that do)."""
        text = f" {brief.lower()} "
        counts = {
            archetype.id: sum(
                1
                for keyword in archetype.keywords
                if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text)
            )
            for archetype in self._archetypes.values()
        }
        return {archetype_id: count for archetype_id, count in counts.items() if count}

    def blend(
        self, proposed: Sequence[Mapping[str, object]], brief: str = ""
    ) -> ArchetypeBlend:
        """A valid blend from what a model proposed and what the brief itself says.

        Unknown names are dropped and duplicates merged. An archetype the brief
        plainly names but the proposal left out is added with a small share, so a
        "healthcare AI startup" cannot come out with no healthcare in it. Weights
        are then cut to the largest ``MAX_BLEND_PARTS`` and scaled to total 100.
        With nothing usable, the blend is whatever the brief's words suggest, or
        a plain SaaS site.
        """
        weights: dict[str, float] = {}
        for item in proposed:
            archetype = self.resolve(str(item.get("id") or item.get("name") or ""))
            if archetype is None:
                continue
            try:
                weight = float(item.get("weight") or 0)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                weight = 0.0
            if weight > 0:
                weights[archetype.id] = weights.get(archetype.id, 0.0) + weight
        evidence = self.evidence(brief)
        if weights:
            total = sum(weights.values())
            weights = {key: value * 100 / total for key, value in weights.items()}
            for archetype_id, hits in sorted(evidence.items(), key=lambda item: -item[1]):
                if archetype_id not in weights and hits >= 2:
                    weights[archetype_id] = 15.0
        else:
            weights = {key: float(hits) for key, hits in evidence.items()} or {"saas": 1.0}
        kept = sorted(weights.items(), key=lambda item: -item[1])[:MAX_BLEND_PARTS]
        return ArchetypeBlend(_to_percent(kept, self._archetypes))


def _to_percent(
    weights: Sequence[tuple[str, float]], archetypes: Mapping[str, Archetype]
) -> tuple[BlendPart, ...]:
    """Whole percentages that add up to exactly 100, dropping parts too small to matter."""
    total = sum(weight for _, weight in weights)
    shares = [(key, weight * 100 / total) for key, weight in weights]
    shares = [(key, share) for key, share in shares if share >= MIN_WEIGHT] or shares[:1]
    total = sum(share for _, share in shares)
    rounded = [(key, round(share * 100 / total)) for key, share in shares]
    # Rounding can leave the sum a point or two off; the lead part absorbs it.
    drift = 100 - sum(weight for _, weight in rounded)
    rounded[0] = (rounded[0][0], rounded[0][1] + drift)
    return tuple(BlendPart(archetypes[key], weight) for key, weight in rounded)


@lru_cache
def build_default_archetype_registry() -> ArchetypeRegistry:
    return ArchetypeRegistry()
