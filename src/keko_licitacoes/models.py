from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class Opportunity:
    source: str
    external_id: str | None
    buyer_name: str | None
    buyer_document: str | None
    department_name: str | None
    uf: str | None
    city: str | None
    modality: str | None
    modality_id: int | None
    object: str | None
    notice_number: str | None
    process_number: str | None
    publication_date: str | None
    proposal_opening_date: str | None
    proposal_closing_date: str | None
    status: str | None
    estimated_value: Decimal | None
    awarded_value: Decimal | None
    origin_system: str | None
    link: str | None
    raw: dict[str, Any] = field(repr=False)

    def to_dict(self, *, include_raw: bool = False) -> dict[str, Any]:
        data = asdict(self)
        data["estimated_value"] = _decimal_to_str(self.estimated_value)
        data["awarded_value"] = _decimal_to_str(self.awarded_value)

        if not include_raw:
            data.pop("raw", None)

        return data


def _decimal_to_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")
