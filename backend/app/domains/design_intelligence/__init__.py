"""Design intelligence: what the platform knows about designing a website.

Everything here is deterministic knowledge and rules, with no model calls:

    archetypes      kinds of website and what each implies for a design
    strategy        what was understood about a product before designing it
    references      design knowledge extracted from existing websites
    architecture    narrative structures for pages, and what "generic" looks like
    dna             the one design language every screen of a product follows
    compatibility   which design choices work together and which do not
    primitives      the renderable effects, with what each costs a design
    critique        how a rendered result is judged and what to redo

The agentic workflow in ``app.ai.orchestration.design`` asks models to reason
and then holds their answers to these rules.
"""
