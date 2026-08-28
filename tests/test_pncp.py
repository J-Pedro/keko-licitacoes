from decimal import Decimal
from datetime import date

import pytest

from keko_licitacoes.sources.pncp import (
    PNCPError,
    PNCPSource,
    map_publication,
    map_search_item,
    parse_modality_values,
)


def test_parse_modality_values_accepts_alias_and_codes() -> None:
    assert parse_modality_values(["pregao,8", "concorrencia"]) == [6, 8, 4]


def test_parse_modality_values_accepts_pncp_display_name() -> None:
    assert parse_modality_values(["Pregao - Eletronico"]) == [6]


def test_parse_modality_values_defaults_to_project_modalities() -> None:
    assert parse_modality_values([]) == [6, 4, 8]


def test_parse_modality_values_rejects_unknown_alias() -> None:
    with pytest.raises(ValueError):
        parse_modality_values(["modalidade-inexistente"])


def test_map_publication_normalizes_pncp_payload() -> None:
    payload = {
        "numeroControlePNCP": "123-1-000001/2026",
        "orgaoEntidade": {"razaoSocial": "MUNICIPIO TESTE", "cnpj": "123"},
        "unidadeOrgao": {"ufSigla": "RS", "municipioNome": "Porto Alegre", "nomeUnidade": "Compras"},
        "modalidadeNome": "Pregao - Eletronico",
        "modalidadeId": 6,
        "objetoCompra": "Aquisicao de calhas",
        "numeroCompra": "10/2026",
        "processo": "20/2026",
        "dataPublicacaoPncp": "2026-08-27T10:00:00",
        "dataAberturaProposta": "2026-08-28T10:00:00",
        "dataEncerramentoProposta": "2026-09-05T10:00:00",
        "situacaoCompraNome": "Divulgada no PNCP",
        "valorTotalEstimado": "123.45",
        "valorTotalHomologado": None,
        "usuarioNome": "Compras.gov.br",
        "linkSistemaOrigem": "https://example.com/edital",
    }

    opportunity = map_publication(payload)

    assert opportunity.source == "PNCP"
    assert opportunity.external_id == "123-1-000001/2026"
    assert opportunity.uf == "RS"
    assert opportunity.city == "Porto Alegre"
    assert opportunity.estimated_value == Decimal("123.45")
    assert opportunity.link == "https://example.com/edital"


def test_map_search_item_normalizes_portal_payload() -> None:
    payload = {
        "numero_controle_pncp": "123-1-000001/2026",
        "orgao_nome": "MUNICIPIO TESTE",
        "orgao_cnpj": "123",
        "unidade_nome": "Compras",
        "uf": "RS",
        "municipio_nome": "Porto Alegre",
        "modalidade_licitacao_nome": "Pregao - Eletronico",
        "modalidade_licitacao_id": "6",
        "description": "Aquisicao de calhas",
        "title": "Edital nº 10/2026",
        "data_publicacao_pncp": "2026-08-27T10:00:00",
        "data_inicio_vigencia": "2026-08-28T10:00",
        "data_fim_vigencia": "2026-09-05T10:00",
        "situacao_nome": "Divulgada no PNCP",
        "valor_global": "123.45",
        "item_url": "/compras/123/2026/1",
        "document_type": "edital",
    }

    opportunity = map_search_item(payload)

    assert opportunity.external_id == "123-1-000001/2026"
    assert opportunity.buyer_name == "MUNICIPIO TESTE"
    assert opportunity.modality_id == 6
    assert opportunity.object == "Aquisicao de calhas"
    assert opportunity.link == "https://pncp.gov.br/app/compras/123/2026/1"


def test_source_searches_one_portal_page_with_pagination_metadata() -> None:
    client = FakePNCPClient()
    source = PNCPSource(client=client)

    page = source.search_portal_page(
        page=2,
        modality_ids=[6],
        ufs=["rs"],
        keywords=["calha"],
    )

    assert len(page.results) == 1
    assert page.page == 2
    assert page.page_size == 10
    assert page.total_records == 21
    assert page.total_pages == 3
    assert page.remaining_pages == 1
    assert client.portal_calls == [
        {
            "page": 2,
            "ufs": ["rs"],
            "modality_ids": [6],
            "query": "calha",
            "status": "recebendo_proposta",
            "document_types": "edital",
            "order": "-data",
        }
    ]


def test_source_splits_search_by_date_window() -> None:
    client = FakePNCPClient()
    source = PNCPSource(client=client, date_window_days=1)

    results = source.search(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 3),
        modality_ids=[6],
        ufs=["RS"],
    )

    assert len(results) == 3
    assert [(call["start_date"], call["end_date"]) for call in client.calls] == [
        (date(2026, 8, 1), date(2026, 8, 1)),
        (date(2026, 8, 2), date(2026, 8, 2)),
        (date(2026, 8, 3), date(2026, 8, 3)),
    ]


def test_source_can_continue_after_pncp_error() -> None:
    client = FakePNCPClient(fail_on_start_date=date(2026, 8, 1))
    source = PNCPSource(client=client, date_window_days=1, continue_on_error=True)

    results = source.search(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 2),
        modality_ids=[6],
        ufs=["RS"],
    )

    assert len(results) == 1
    assert len(source.skipped_queries) == 1
    assert "2026-08-01 a 2026-08-01" in source.skipped_queries[0]


def test_source_can_search_by_updates() -> None:
    client = FakePNCPClient()
    source = PNCPSource(client=client, query_kind="atualizacao")

    results = source.search(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 2),
        modality_ids=[6],
        ufs=["RS"],
    )

    assert len(results) == 1
    assert client.calls[0]["kind"] == "atualizacao"


def test_source_can_search_open_proposals() -> None:
    client = FakePNCPClient()
    source = PNCPSource(client=client, query_kind="proposta", date_window_days=1)

    results = source.search(
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 3),
        modality_ids=[6],
        ufs=["RS"],
    )

    assert len(results) == 1
    assert len(client.calls) == 1
    assert client.calls[0]["kind"] == "proposta"
    assert client.calls[0]["end_date"] == date(2026, 8, 3)


class FakePNCPClient:
    def __init__(self, fail_on_start_date: date | None = None) -> None:
        self.fail_on_start_date = fail_on_start_date
        self.calls = []
        self.portal_calls = []
        self.page_size = 10

    def search_portal_editais(
        self,
        *,
        page: int = 1,
        ufs=None,
        modality_ids=None,
        query: str | None = None,
        status: str = "recebendo_proposta",
        document_types: str = "edital",
        order: str = "-data",
    ) -> dict:
        self.portal_calls.append(
            {
                "page": page,
                "ufs": list(ufs or []),
                "modality_ids": list(modality_ids or []),
                "query": query,
                "status": status,
                "document_types": document_types,
                "order": order,
            }
        )
        return {
            "items": [
                {
                    "numero_controle_pncp": f"portal-page-{page}",
                    "modalidade_licitacao_id": "6",
                    "uf": "RS",
                }
            ],
            "total": 21,
        }

    def search_publications(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict:
        return self._search(
            kind="publicacao",
            start_date=start_date,
            end_date=end_date,
            modality_id=modality_id,
            uf=uf,
            page=page,
        )

    def search_updates(
        self,
        *,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict:
        return self._search(
            kind="atualizacao",
            start_date=start_date,
            end_date=end_date,
            modality_id=modality_id,
            uf=uf,
            page=page,
        )

    def search_open_proposals(
        self,
        *,
        end_date: date,
        modality_id: int,
        uf: str | None = None,
        page: int = 1,
    ) -> dict:
        return self._search(
            kind="proposta",
            start_date=end_date,
            end_date=end_date,
            modality_id=modality_id,
            uf=uf,
            page=page,
        )

    def _search(
        self,
        *,
        kind: str,
        start_date: date,
        end_date: date,
        modality_id: int,
        uf: str | None,
        page: int,
    ) -> dict:
        self.calls.append(
            {
                "kind": kind,
                "start_date": start_date,
                "end_date": end_date,
                "modality_id": modality_id,
                "uf": uf,
                "page": page,
            }
        )
        if start_date == self.fail_on_start_date:
            raise PNCPError("temporarily unavailable")
        return {
            "data": [
                {
                    "numeroControlePNCP": f"{start_date.isoformat()}-{modality_id}",
                    "modalidadeId": modality_id,
                    "unidadeOrgao": {"ufSigla": uf},
                }
            ],
            "paginasRestantes": 0,
        }
