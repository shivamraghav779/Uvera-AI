"""Types shared across domains."""

from pydantic import BaseModel, ConfigDict

Scalar = str | int | float | bool | None
DataRow = dict[str, Scalar]


class StrictModel(BaseModel):
    """Base for contracts where unknown fields must be rejected."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
