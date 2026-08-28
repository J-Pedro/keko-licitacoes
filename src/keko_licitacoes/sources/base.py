from __future__ import annotations

from collections.abc import Iterable, Protocol
from datetime import date

from keko_licitacoes.models import Opportunity


class OpportunitySource(Protocol):
    name: str

    def search(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_ids: Iterable[int],
        ufs: Iterable[str] | None = None,
        keywords: Iterable[str] | None = None,
        limit: int | None = None,
    ) -> list[Opportunity]:
        ...
