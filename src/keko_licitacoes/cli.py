from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

from keko_licitacoes.models import Opportunity
from keko_licitacoes.sources.pncp import PNCPClient, PNCPError, PNCPSource, SearchPage, parse_modality_values


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "pncp":
        return run_pncp(args)

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keko-licitacoes",
        description="Coletor de licitacoes publicas.",
    )
    subparsers = parser.add_subparsers(dest="command")

    pncp = subparsers.add_parser("pncp", help="Busca licitacoes na API publica do PNCP.")
    pncp.add_argument("--data-inicial", type=parse_date, help="Mantido por compatibilidade; a busca do site nao exige data.")
    pncp.add_argument("--data-final", type=parse_date, help="Mantido por compatibilidade; a busca do site nao exige data.")
    pncp.add_argument("--uf", action="append", default=[], help="UF. Aceita repeticao ou lista separada por virgula.")
    pncp.add_argument(
        "--modalidade",
        action="append",
        default=[],
        help="Codigo PNCP ou alias. Ex.: pregao, concorrencia, dispensa ou 6.",
    )
    pncp.add_argument("--todas-modalidades", action="store_true")
    pncp.add_argument(
        "--palavra-chave",
        action="append",
        default=[],
        help="Termo de busca enviado como q para o portal. Aceita repeticao ou lista separada por virgula.",
    )
    pncp.add_argument(
        "--consulta",
        choices=("site", "publicacao", "atualizacao", "proposta"),
        default="site",
        help=(
            "Endpoint legado do PNCP. A CLI usa a busca do site por padrao."
        ),
    )
    pncp.add_argument("--pagina", type=positive_int, default=1, help="Pagina da busca, como em /app/editais?pagina=1.")
    pncp.add_argument("--status", default="recebendo_proposta", help="Status usado pela busca do site.")
    pncp.add_argument("--tipos-documento", default="edital", help="Tipo de documento usado pela busca do site.")
    pncp.add_argument("--ordenacao", default="-data", help="Ordenacao usada pela busca do site.")
    pncp.add_argument("--limite", type=positive_int, default=None)
    pncp.add_argument("--paginas-por-consulta", type=positive_int, default=None)
    pncp.add_argument("--tamanho-pagina", type=pncp_page_size, default=10)
    pncp.add_argument(
        "--dias-por-consulta",
        type=positive_int,
        default=None,
        help="Divide o periodo em janelas menores para reduzir timeouts do PNCP. Ex.: 1 ou 7.",
    )
    pncp.add_argument("--timeout", type=positive_float, default=30.0, help="Timeout em segundos por requisicao.")
    pncp.add_argument("--tentativas", type=non_negative_int, default=2, help="Numero de novas tentativas por pagina.")
    pncp.add_argument(
        "--intervalo-retry",
        type=non_negative_float,
        default=1.0,
        help="Espera inicial em segundos entre tentativas. O valor cresce a cada tentativa.",
    )
    pncp.add_argument(
        "--continuar-com-erros",
        action="store_true",
        help="Pula consultas que falharem apos as tentativas e salva os resultados parciais.",
    )
    pncp.add_argument("--formato", choices=("json", "csv"), default="json")
    pncp.add_argument("--saida", type=Path, default=None)
    pncp.add_argument("--incluir-bruto", action="store_true", help="Inclui payload original no JSON.")

    return parser


def run_pncp(args: argparse.Namespace) -> int:
    if args.data_inicial and args.data_final and args.data_final < args.data_inicial:
        raise SystemExit("--data-final deve ser maior ou igual a --data-inicial.")

    try:
        if args.consulta == "site" and not args.modalidade and not args.todas_modalidades:
            modality_ids = []
        else:
            modality_ids = parse_modality_values(args.modalidade, include_all=args.todas_modalidades)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    ufs = split_cli_values(args.uf)
    keywords = split_cli_values(args.palavra_chave)

    source = PNCPSource(
        client=PNCPClient(
            page_size=args.tamanho_pagina,
            timeout_seconds=args.timeout,
            max_retries=args.tentativas,
            retry_delay_seconds=args.intervalo_retry,
        ),
        query_kind=args.consulta if args.consulta != "site" else "publicacao",
        max_pages_per_query=args.paginas_por_consulta,
        date_window_days=args.dias_por_consulta,
        continue_on_error=args.continuar_com_erros,
    )
    if args.consulta == "site":
        try:
            page = source.search_portal_page(
                page=args.pagina,
                modality_ids=modality_ids,
                ufs=ufs,
                keywords=keywords,
                status=args.status,
                document_types=args.tipos_documento,
                order=args.ordenacao,
            )
        except PNCPError as exc:
            raise SystemExit(f"Erro ao consultar o PNCP: {exc}") from exc

        if args.limite is not None:
            page.results = page.results[: args.limite]

        content = serialize_page(page, args.formato, include_raw=args.incluir_bruto)
        if args.saida:
            args.saida.parent.mkdir(parents=True, exist_ok=True)
            args.saida.write_text(content, encoding="utf-8")
            print(f"{len(page.results)} licitacoes da pagina {page.page} salvas em {args.saida}")
        else:
            print(content)
    else:
        if args.data_inicial is None or args.data_final is None:
            raise SystemExit("--data-inicial e --data-final sao obrigatorias nas consultas legadas.")
        try:
            results = source.search(
                start_date=args.data_inicial,
                end_date=args.data_final,
                modality_ids=modality_ids,
                ufs=ufs,
                keywords=keywords,
                limit=args.limite,
            )
        except PNCPError as exc:
            raise SystemExit(f"Erro ao consultar o PNCP: {exc}") from exc

        content = serialize_results(results, args.formato, include_raw=args.incluir_bruto)
        if args.saida:
            args.saida.parent.mkdir(parents=True, exist_ok=True)
            args.saida.write_text(content, encoding="utf-8")
            print(f"{len(results)} licitacoes salvas em {args.saida}")
        else:
            print(content)

    if source.skipped_queries:
        print(
            f"Aviso: {len(source.skipped_queries)} consulta(s) foram puladas por erro no PNCP.",
            file=sys.stderr,
        )
        for skipped_query in source.skipped_queries:
            print(f"- {skipped_query}", file=sys.stderr)

    return 0


def serialize_page(page: SearchPage, output_format: str, *, include_raw: bool = False) -> str:
    if output_format == "json":
        return json.dumps(page.to_dict(include_raw=include_raw), ensure_ascii=False, indent=2)

    return serialize_results(page.results, output_format, include_raw=include_raw)


def serialize_results(results: list[Opportunity], output_format: str, *, include_raw: bool = False) -> str:
    rows = [result.to_dict(include_raw=include_raw) for result in results]
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)

    fieldnames = [
        "source",
        "external_id",
        "buyer_name",
        "buyer_document",
        "department_name",
        "uf",
        "city",
        "modality",
        "modality_id",
        "object",
        "notice_number",
        "process_number",
        "publication_date",
        "proposal_opening_date",
        "proposal_closing_date",
        "status",
        "estimated_value",
        "awarded_value",
        "origin_system",
        "link",
    ]
    output = []
    writer = csv.DictWriter(_ListWriter(output), fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return "".join(output)


def parse_date(value: str) -> date:
    for date_format in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError("Use YYYY-MM-DD ou YYYYMMDD.")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Informe um numero maior que zero.")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Informe zero ou um numero maior.")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Informe um numero maior que zero.")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Informe zero ou um numero maior.")
    return parsed


def pncp_page_size(value: str) -> int:
    parsed = positive_int(value)
    if parsed < 1 or parsed > 500:
        raise argparse.ArgumentTypeError("Informe um tamanho de pagina entre 1 e 500.")
    return parsed


def split_cli_values(values: list[str]) -> list[str]:
    parts: list[str] = []
    for value in values:
        parts.extend(part.strip() for part in value.split(",") if part.strip())
    return parts


class _ListWriter:
    def __init__(self, output: list[str]) -> None:
        self.output = output

    def write(self, value: str) -> None:
        self.output.append(value)


if __name__ == "__main__":
    raise SystemExit(main())
