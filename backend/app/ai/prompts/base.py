from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """A named, versioned system prompt.

    Bump ``version`` whenever the wording changes; it is returned in generation
    metadata so outputs can be traced to the prompt that produced them.
    """

    name: str
    version: str
    system: str
