from __future__ import annotations

import json
import math
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

import requests

from keko_licitacoes.filters import any_keyword_matches, split_terms
from keko_licitacoes.models import Opportunity


PNCP_CONSULTA_BASE_URL = "https://pncp.gov.br/api/consulta"
PNCP_SEARCH_URL = "https://pncp.gov.br/api/search/"
PNCP_PORTAL_BASE_URL = "https://pncp.gov.br/app"

MODALITY_ALIASES = {
    "leilao-eletronico": 1,
    "leilao": 1,
    "dialogo-competitivo": 2,
    "dialogo": 2,
    "concurso": 3,
    "concorrencia-eletronica": 4,
    "concorrencia": 4,
    "concorrencia-presencial": 5,
    "pregao-eletronico": 6,
    "pregao": 6,
    "pregao-presencial": 7,
    "dispensa": 8,
    "inexigibilidade": 9,
    "manifestacao-interesse": 10,
    "pre-qualificacao": 11,
    "credenciamento": 12,
    "leilao-presencial": 13,
    "inaplicabilidade": 14,
    "chamada-publica": 15,
}

DEFAULT_MODALITY_IDS = (6, 4, 8)
ALL_KNOWN_MODALITY_IDS = tuple(range(1, 20))
PNCPQueryKind = Literal["publicacao", "atualizacao", "proposta"]


class PNCPError(RuntimeError):
    pass


@dataclass(slots=True)
class SearchPage:
    results: list[Opportunity]
    total_records: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total_records <= 0:
            return 0
        return math.ceil(self.total_records / self.page_size)

    @property
    def remaining_pages(self) -> int:
        return max(self.total_pages - self.page, 0)

    def to_dict(self, *, include_raw: bool = False) -> dict[str, Any]:
        return {
            "pagina": self.page,
            "tamanho_pagina": self.page_size,
            "total_registros": self.total_records,
            "total_paginas": self.total_pages,
            "paginas_restantes": self.remaining_pages,
            "resultados": [result.to_dict(include_raw=include_raw) for result in self.results],
        }


@dataclass(slots=True)
class PNCPClient:
    base_url: str = PNCP_CONSULTA_BASE_URL
    search_url: str = PNCP_SEARCH_URL
    timeout_seconds: float = 30
    page_size: int = 10
    max_retries: int = 2
    retry_delay_seconds: float = 1

    def __post_init__(self) -> None:
        if self.page_size < 1 or self.page_size > 500:
            raise ValueError("PNCP page_size must be between 1 and 500.")
        if self.timeout_seconds <= 0:
            raise ValueError("PNCP timeout_seconds must be greater than zero.")
        if self.max_retries < 0:
            raise ValueError("PNCP max_retries must be zero or greater.")
        if self.retry_delay_seconds < 0:
            raise ValueError("PNCP retry_delay_seconds must be zero or greater.")

    def search_publications(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "dataInicial": _format_pncp_date(start_date),
            "dataFinal": _format_pncp_date(end_date),
            "codigoModalidadeContratacao": modality_id,
            "pagina": page,
            "tamanhoPagina": self.page_size,
        }
        if uf:
            params["uf"] = uf.upper()

        return self._get_json("/v1/contratacoes/publicacao", params)

    def search_updates(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "dataInicial": _format_pncp_date(start_date),
            "dataFinal": _format_pncp_date(end_date),
            "codigoModalidadeContratacao": modality_id,
            "pagina": page,
            "tamanhoPagina": self.page_size,
        }
        if uf:
            params["uf"] = uf.upper()

        return self._get_json("/v1/contratacoes/atualizacao", params)

    def search_open_proposals(
        self,
        *,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "dataFinal": _format_pncp_date(end_date),
            "codigoModalidadeContratacao": modality_id,
            "pagina": page,
            "tamanhoPagina": self.page_size,
        }
        if uf:
            params["uf"] = uf.upper()

        return self._get_json("/v1/contratacoes/proposta", params)

    def search_portal_editais(
        self,
        *,
        page: int = 1,
        ufs: Iterable[str] | None = None,
        modality_ids: Iterable[int] | None = None,
        query: str | None = None,
        status: str = "recebendo_proposta",
        document_types: str = "edital",
        order: str = "-data",
    ) -> dict[str, Any]:
        if page <= 0:
            raise ValueError("page must be greater than zero.")

        params: dict[str, str | int] = {
            "tipos_documento": document_types,
            "ordenacao": order,
            "status": status,
            "pagina": page,
            "tam_pagina": self.page_size,
        }

        normalized_ufs = [uf.strip().upper() for uf in (ufs or []) if uf.strip()]
        if normalized_ufs:
            params["ufs"] = ",".join(normalized_ufs)

        normalized_modalities = [str(modality_id) for modality_id in (modality_ids or [])]
        if normalized_modalities:
            params["modalidades"] = ",".join(normalized_modalities)

        normalized_query = (query or "").strip()
        if normalized_query:
            params["q"] = normalized_query

        return self._get_json_url(self.search_url, params)

    def _get_json(self, path: str, params: dict[str, str | int]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        return self._get_json_url(url, params)

    def _get_json_url(self, url: str, params: dict[str, str | int]) -> dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "keko-licitacoes/0.1",
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                if response.status_code == 204:
                    return _empty_page(params)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                    time.sleep(self._retry_delay(response, attempt))
                    continue

                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                response = exc.response
                status = response.status_code if response is not None else "unknown"
                details = _response_details(response) if response is not None else str(exc)
                if status == 429:
                    raise PNCPError(
                        "PNCP returned HTTP 429: request limit exceeded. "
                        "Wait a few minutes, reduce concurrent runs, or use a larger --intervalo-retry. "
                        f"Details: {details}"
                    ) from exc
                raise PNCPError(f"PNCP returned HTTP {status}: {details}") from exc
            except json.JSONDecodeError as exc:
                raise PNCPError(f"PNCP returned invalid JSON: {exc}") from exc
            except (requests.Timeout, requests.RequestException) as exc:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_seconds * (attempt + 1))
                    continue
                attempts = self.max_retries + 1
                raise PNCPError(
                    f"Could not reach PNCP after {attempts} attempt(s): {exc}. "
                    "The PNCP API may be unstable or overloaded; try a smaller date window, "
                    "a narrower UF/modality filter, or a higher timeout."
                ) from exc

        raise PNCPError("Could not reach PNCP after retries.")

    def _retry_delay(self, response: requests.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), 0)
            except ValueError:
                pass
        return self.retry_delay_seconds * (2**attempt)


@dataclass(slots=True)
class PNCPSource:
    client: PNCPClient
    name: str = "PNCP"
    query_kind: PNCPQueryKind = "publicacao"
    max_pages_per_query: int | None = None
    date_window_days: int | None = None
    continue_on_error: bool = False
    skipped_queries: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.max_pages_per_query is not None and self.max_pages_per_query <= 0:
            raise ValueError("max_pages_per_query must be greater than zero.")
        if self.date_window_days is not None and self.date_window_days <= 0:
            raise ValueError("date_window_days must be greater than zero.")
        if self.query_kind not in {"publicacao", "atualizacao", "proposta"}:
            raise ValueError("query_kind must be publicacao, atualizacao, or proposta.")

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
        keyword_terms = split_terms(keywords)
        normalized_ufs = [uf.strip().upper() for uf in (ufs or []) if uf.strip()]
        uf_values: list[str | None] = normalized_ufs or [None]
        results: list[Opportunity] = []
        seen_ids: set[str] = set()

        date_windows = [(start_date, end_date)] if self.query_kind == "proposta" else _iter_date_windows(
            start_date,
            end_date,
            self.date_window_days,
        )

        for window_start, window_end in date_windows:
            for modality_id in modality_ids:
                for uf in uf_values:
                    page = 1
                    while True:
                        try:
                            response = self._search_page(
                                start_date=window_start,
                                end_date=window_end,
                                modality_id=modality_id,
                                uf=uf,
                                page=page,
                            )
                        except PNCPError as exc:
                            if not self.continue_on_error:
                                raise
                            self.skipped_queries.append(
                                _format_skipped_query(window_start, window_end, modality_id, uf, page, exc)
                            )
                            break

                        for item in response.get("data", []):
                            opportunity = map_publication(item)
                            if opportunity.external_id and opportunity.external_id in seen_ids:
                                continue
                            if keyword_terms and not _matches_keywords(opportunity, keyword_terms):
                                continue

                            if opportunity.external_id:
                                seen_ids.add(opportunity.external_id)
                            results.append(opportunity)

                            if limit is not None and len(results) >= limit:
                                return results

                        remaining = int(response.get("paginasRestantes") or 0)
                        if remaining <= 0:
                            break
                        if self.max_pages_per_query is not None and page >= self.max_pages_per_query:
                            break
                        page += 1

        return results

    def search_portal_page(
        self,
        *,
        page: int = 1,
        modality_ids: Iterable[int] | None = None,
        ufs: Iterable[str] | None = None,
        keywords: Iterable[str] | None = None,
        status: str = "recebendo_proposta",
        document_types: str = "edital",
        order: str = "-data",
    ) -> SearchPage:
        keyword_terms = split_terms(keywords)
        response = self.client.search_portal_editais(
            page=page,
            ufs=ufs,
            modality_ids=modality_ids,
            query=" ".join(keyword_terms),
            status=status,
            document_types=document_types,
            order=order,
        )

        results = [map_search_item(item) for item in response.get("items", [])]
        total_records = _to_int(response.get("total")) or len(results)
        return SearchPage(
            results=results,
            total_records=total_records,
            page=page,
            page_size=self.client.page_size,
        )

    def _search_page(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None,
        page: int,
    ) -> dict[str, Any]:
        if self.query_kind == "publicacao":
            return self.client.search_publications(
                start_date=start_date,
                end_date=end_date,
                modality_id=modality_id,
                uf=uf,
                page=page,
            )
        if self.query_kind == "atualizacao":
            return self.client.search_updates(
                start_date=start_date,
                end_date=end_date,
                modality_id=modality_id,
                uf=uf,
                page=page,
            )
        return self.client.search_open_proposals(
            end_date=end_date,
            modality_id=modality_id,
            uf=uf,
            page=page,
        )


def parse_modality_values(values: Iterable[str] | None, *, include_all: bool = False) -> list[int]:
    if include_all:
        return list(ALL_KNOWN_MODALITY_IDS)
    if not values:
        return list(DEFAULT_MODALITY_IDS)

    modality_ids: list[int] = []
    for value in values:
        for part in value.split(","):
            token = _normalize_modality_token(part)
            if not token:
                continue
            if token.isdigit():
                modality_id = int(token)
            else:
                try:
                    modality_id = MODALITY_ALIASES[token]
                except KeyError as exc:
                    known = ", ".join(sorted(MODALITY_ALIASES))
                    raise ValueError(f"Unknown modality '{part}'. Known aliases: {known}") from exc
            if modality_id not in modality_ids:
                modality_ids.append(modality_id)
    return modality_ids


def map_publication(item: dict[str, Any]) -> Opportunity:
    org = item.get("orgaoEntidade") or {}
    unit = item.get("unidadeOrgao") or {}

    return Opportunity(
        source="PNCP",
        external_id=item.get("numeroControlePNCP"),
        buyer_name=org.get("razaoSocial"),
        buyer_document=org.get("cnpj"),
        department_name=unit.get("nomeUnidade"),
        uf=unit.get("ufSigla"),
        city=unit.get("municipioNome"),
        modality=item.get("modalidadeNome"),
        modality_id=_to_int(item.get("modalidadeId")),
        object=item.get("objetoCompra"),
        notice_number=item.get("numeroCompra"),
        process_number=item.get("processo"),
        publication_date=item.get("dataPublicacaoPncp"),
        proposal_opening_date=item.get("dataAberturaProposta"),
        proposal_closing_date=item.get("dataEncerramentoProposta"),
        status=item.get("situacaoCompraNome"),
        estimated_value=_to_decimal(item.get("valorTotalEstimado")),
        awarded_value=_to_decimal(item.get("valorTotalHomologado")),
        origin_system=item.get("usuarioNome"),
        link=_best_link(item),
        raw=item,
    )


def map_search_item(item: dict[str, Any]) -> Opportunity:
    return Opportunity(
        source="PNCP",
        external_id=item.get("numero_controle_pncp"),
        buyer_name=item.get("orgao_nome"),
        buyer_document=item.get("orgao_cnpj"),
        department_name=item.get("unidade_nome"),
        uf=item.get("uf"),
        city=item.get("municipio_nome"),
        modality=item.get("modalidade_licitacao_nome"),
        modality_id=_to_int(item.get("modalidade_licitacao_id")),
        object=item.get("description"),
        notice_number=item.get("title") or item.get("numero"),
        process_number=None,
        publication_date=item.get("data_publicacao_pncp"),
        proposal_opening_date=item.get("data_inicio_vigencia"),
        proposal_closing_date=item.get("data_fim_vigencia"),
        status=item.get("situacao_nome"),
        estimated_value=_to_decimal(item.get("valor_global")),
        awarded_value=None,
        origin_system=item.get("document_type"),
        link=_portal_item_link(item),
        raw=item,
    )


def _matches_keywords(opportunity: Opportunity, keyword_terms: Iterable[str]) -> bool:
    return any_keyword_matches(
        [
            opportunity.object,
            opportunity.buyer_name,
            opportunity.department_name,
            opportunity.city,
            opportunity.notice_number,
            opportunity.process_number,
            opportunity.origin_system,
            opportunity.raw.get("informacaoComplementar"),
        ],
        keyword_terms,
    )


def _best_link(item: dict[str, Any]) -> str:
    for key in ("linkSistemaOrigem", "linkProcessoEletronico"):
        value = item.get(key)
        if value:
            return str(value)

    control_number = item.get("numeroControlePNCP")
    if control_number:
        return f"{PNCP_PORTAL_BASE_URL}/editais/{control_number}"

    return f"{PNCP_PORTAL_BASE_URL}/editais"


def _portal_item_link(item: dict[str, Any]) -> str:
    item_url = item.get("item_url")
    if item_url:
        return f"{PNCP_PORTAL_BASE_URL}{item_url}"
    return f"{PNCP_PORTAL_BASE_URL}/editais"


def _format_pncp_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def _response_details(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type", "")
    text = response.text.strip()
    if "html" in content_type.lower():
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
    return text[:1000]


def _iter_date_windows(start_date: date, end_date: date, window_days: int | None) -> Iterable[tuple[date, date]]:
    if window_days is None:
        yield start_date, end_date
        return

    current = start_date
    delta = timedelta(days=window_days - 1)
    while current <= end_date:
        window_end = min(current + delta, end_date)
        yield current, window_end
        current = window_end + timedelta(days=1)


def _format_skipped_query(
    start_date: date,
    end_date: date,
    modality_id: int,
    uf: str | None,
    page: int,
    error: PNCPError,
) -> str:
    uf_text = uf or "todas"
    return (
        f"{start_date.isoformat()} a {end_date.isoformat()}, modalidade {modality_id}, "
        f"UF {uf_text}, pagina {page}: {error}"
    )


def _empty_page(params: dict[str, str | int]) -> dict[str, Any]:
    return {
        "data": [],
        "totalRegistros": 0,
        "totalPaginas": 0,
        "numeroPagina": params.get("pagina", 1),
        "paginasRestantes": 0,
        "empty": True,
    }


def _normalize_modality_token(value: str) -> str:
    from keko_licitacoes.filters import normalize_text

    token = normalize_text(value)
    return re.sub(r"[^a-z0-9]+", "-", token).strip("-")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
