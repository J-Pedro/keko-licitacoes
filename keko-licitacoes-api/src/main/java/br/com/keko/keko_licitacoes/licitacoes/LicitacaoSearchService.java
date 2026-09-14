package br.com.keko.keko_licitacoes.licitacoes;

import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import br.com.keko.keko_licitacoes.pncp.PncpSearchClient;
import br.com.keko.keko_licitacoes.pncp.PncpSearchItem;
import br.com.keko.keko_licitacoes.pncp.PncpSearchResponse;

@Service
public class LicitacaoSearchService {

	private static final String PNCP_APP_BASE_URL = "https://pncp.gov.br/app";
	private static final String ERRO_CONSULTA_PALAVRA = "Nao foi possivel consultar esta palavra-chave no PNCP.";

	private final PncpSearchClient pncpSearchClient;
	private final KeywordSearchDelay keywordSearchDelay;

	public LicitacaoSearchService(PncpSearchClient pncpSearchClient, KeywordSearchDelay keywordSearchDelay) {
		this.pncpSearchClient = pncpSearchClient;
		this.keywordSearchDelay = keywordSearchDelay;
	}

	public LicitacaoPageResponse buscar(
			List<String> palavrasChave,
			List<String> ufs,
			List<Integer> modalidades,
			String status,
			String tiposDocumento,
			String ordenacao,
			Integer pagina,
			Integer tamanhoPagina) {
		int paginaNormalizada = Math.max(Optional.ofNullable(pagina).orElse(1), 1);
		int tamanhoNormalizado = limitar(Optional.ofNullable(tamanhoPagina).orElse(10), 1, 100);
		List<String> palavrasNormalizadas = normalizarPalavrasChave(palavrasChave);

		if (palavrasNormalizadas.isEmpty()) {
			PncpSearchResponse response = consultarPncp(
					null,
					ufs,
					modalidades,
					status,
					tiposDocumento,
					ordenacao,
					paginaNormalizada,
					tamanhoNormalizado);

			List<LicitacaoResponse> resultados = itens(response)
					.stream()
					.map(this::mapear)
					.toList();

			return criarResposta(
					paginaNormalizada,
					tamanhoNormalizado,
					Optional.ofNullable(response).map(PncpSearchResponse::total).orElse(resultados.size()),
					resultados,
					List.of());
		}

		List<LicitacaoResponse> resultados = new ArrayList<>();
		List<LicitacaoSearchError> erros = new ArrayList<>();

		for (int indice = 0; indice < palavrasNormalizadas.size(); indice++) {
			String palavraChave = palavrasNormalizadas.get(indice);

			try {
				PncpSearchResponse response = consultarPncp(
						palavraChave,
						ufs,
						modalidades,
						status,
						tiposDocumento,
						ordenacao,
						paginaNormalizada,
						tamanhoNormalizado);

				resultados.addAll(itens(response)
						.stream()
						.map((item) -> mapear(item, palavraChave))
						.toList());
			} catch (RuntimeException exception) {
				erros.add(new LicitacaoSearchError(palavraChave, ERRO_CONSULTA_PALAVRA));
			}

			if (indice < palavrasNormalizadas.size() - 1) {
				keywordSearchDelay.aguardarEntreConsultas();
			}
		}

		List<LicitacaoResponse> consolidados = deduplicarEOrdenar(resultados);

		return criarResposta(
				paginaNormalizada,
				tamanhoNormalizado,
				consolidados.size(),
				consolidados,
				erros);
	}

	private PncpSearchResponse consultarPncp(
			String palavraChave,
			List<String> ufs,
			List<Integer> modalidades,
			String status,
			String tiposDocumento,
			String ordenacao,
			Integer pagina,
			Integer tamanhoPagina) {
		return pncpSearchClient.buscarEditais(
				valorOuPadrao(tiposDocumento, "edital"),
				valorOuPadrao(ordenacao, "-data"),
				valorOuPadrao(status, "recebendo_proposta"),
				pagina,
				tamanhoPagina,
				normalizarTextoOpcional(palavraChave),
				normalizarLista(ufs),
				normalizarListaNumerica(modalidades),
				"application/json",
				"keko-licitacoes-api/0.0.1");
	}

	private List<PncpSearchItem> itens(PncpSearchResponse response) {
		return Optional.ofNullable(response)
				.map(PncpSearchResponse::items)
				.orElseGet(List::of);
	}

	private LicitacaoPageResponse criarResposta(
			int pagina,
			int tamanhoPagina,
			int totalRegistros,
			List<LicitacaoResponse> resultados,
			List<LicitacaoSearchError> erros) {
		int totalPaginas = totalRegistros == 0 ? 0 : (int) Math.ceil((double) totalRegistros / tamanhoPagina);
		int paginasRestantes = Math.max(totalPaginas - pagina, 0);
		return new LicitacaoPageResponse(
				pagina,
				tamanhoPagina,
				totalRegistros,
				totalPaginas,
				paginasRestantes,
				resultados,
				erros);
	}

	private LicitacaoResponse mapear(PncpSearchItem item) {
		return mapear(item, null);
	}

	private LicitacaoResponse mapear(PncpSearchItem item, String palavraChave) {
		return new LicitacaoResponse(
				"PNCP",
				item.numeroControlePncp(),
				item.orgaoNome(),
				item.orgaoCnpj(),
				item.unidadeNome(),
				item.uf(),
				item.municipioNome(),
				item.modalidadeLicitacaoNome(),
				item.modalidadeLicitacaoId(),
				item.descricao(),
				valorOuPadrao(item.titulo(), item.numero()),
				item.dataPublicacaoPncp(),
				item.dataInicioVigencia(),
				item.dataFimVigencia(),
				item.situacaoNome(),
				item.valorGlobal(),
				item.tipoDocumento(),
				linkDoPortal(item),
				StringUtils.hasText(palavraChave) ? List.of(palavraChave.trim()) : List.of());
	}

	private List<LicitacaoResponse> deduplicarEOrdenar(List<LicitacaoResponse> resultados) {
		Map<String, LicitacaoResponse> porIdentificador = new LinkedHashMap<>();

		for (int indice = 0; indice < resultados.size(); indice++) {
			LicitacaoResponse licitacao = resultados.get(indice);
			String chave = chaveDaLicitacao(licitacao, indice);
			LicitacaoResponse existente = porIdentificador.get(chave);

			if (existente == null) {
				porIdentificador.put(chave, comPalavrasEncontradas(licitacao, licitacao.matchedKeywords()));
				continue;
			}

			porIdentificador.put(chave, comPalavrasEncontradas(
					existente,
					mesclarPalavras(existente.matchedKeywords(), licitacao.matchedKeywords())));
		}

		return porIdentificador.values()
				.stream()
				.sorted(Comparator.comparing(this::dataEdital).reversed())
				.toList();
	}

	private LicitacaoResponse comPalavrasEncontradas(LicitacaoResponse licitacao, List<String> matchedKeywords) {
		return new LicitacaoResponse(
				licitacao.fonte(),
				licitacao.idExterno(),
				licitacao.orgao(),
				licitacao.cnpjOrgao(),
				licitacao.unidade(),
				licitacao.uf(),
				licitacao.municipio(),
				licitacao.modalidade(),
				licitacao.modalidadeId(),
				licitacao.objeto(),
				licitacao.numeroEdital(),
				licitacao.dataPublicacao(),
				licitacao.dataAberturaProposta(),
				licitacao.dataEncerramentoProposta(),
				licitacao.situacao(),
				licitacao.valorEstimado(),
				licitacao.sistemaOrigem(),
				licitacao.link(),
				mesclarPalavras(List.of(), matchedKeywords));
	}

	private String chaveDaLicitacao(LicitacaoResponse licitacao, int indice) {
		if (StringUtils.hasText(licitacao.idExterno())) {
			return licitacao.idExterno().trim();
		}

		if (StringUtils.hasText(licitacao.link())) {
			return "link:" + licitacao.link().trim();
		}

		return "sem-identificador:" + indice;
	}

	private List<String> mesclarPalavras(List<String> atuais, List<String> novas) {
		Map<String, String> palavras = new LinkedHashMap<>();

		for (String palavra : atuais) {
			adicionarPalavra(palavras, palavra);
		}

		for (String palavra : novas) {
			adicionarPalavra(palavras, palavra);
		}

		return List.copyOf(palavras.values());
	}

	private void adicionarPalavra(Map<String, String> palavras, String palavra) {
		if (StringUtils.hasText(palavra)) {
			String normalizada = palavra.trim();
			palavras.putIfAbsent(normalizada.toLowerCase(Locale.ROOT), normalizada);
		}
	}

	private Instant dataEdital(LicitacaoResponse licitacao) {
		if (!StringUtils.hasText(licitacao.dataPublicacao())) {
			return Instant.EPOCH;
		}

		String dataPublicacao = licitacao.dataPublicacao().trim();

		try {
			return OffsetDateTime.parse(dataPublicacao).toInstant();
		} catch (DateTimeParseException exception) {
			try {
				return LocalDate.parse(dataPublicacao).atStartOfDay().toInstant(ZoneOffset.UTC);
			} catch (DateTimeParseException ignored) {
				return Instant.EPOCH;
			}
		}
	}

	private String linkDoPortal(PncpSearchItem item) {
		if (StringUtils.hasText(item.itemUrl())) {
			return PNCP_APP_BASE_URL + item.itemUrl().replaceFirst("^/compras/", "/editais/");
		}
		return PNCP_APP_BASE_URL + "/editais";
	}

	private String valorOuPadrao(String valor, String padrao) {
		return StringUtils.hasText(valor) ? valor.trim() : padrao;
	}

	private int limitar(int valor, int minimo, int maximo) {
		return Math.max(minimo, Math.min(valor, maximo));
	}

	private String normalizarTextoOpcional(String valor) {
		return StringUtils.hasText(valor) ? valor.trim() : null;
	}

	private List<String> normalizarPalavrasChave(List<String> valores) {
		if (valores == null || valores.isEmpty()) {
			return List.of();
		}

		Map<String, String> palavras = new LinkedHashMap<>();

		for (String valor : valores) {
			adicionarPalavra(palavras, valor);
		}

		return List.copyOf(palavras.values());
	}

	private String normalizarLista(List<String> valores) {
		if (valores == null || valores.isEmpty()) {
			return null;
		}

		String lista = valores.stream()
				.filter(StringUtils::hasText)
				.map(String::trim)
				.map(String::toUpperCase)
				.distinct()
				.collect(Collectors.joining(","));

		return StringUtils.hasText(lista) ? lista : null;
	}

	private String normalizarListaNumerica(List<Integer> valores) {
		if (valores == null || valores.isEmpty()) {
			return null;
		}

		String lista = valores.stream()
				.distinct()
				.map(String::valueOf)
				.collect(Collectors.joining(","));

		return StringUtils.hasText(lista) ? lista : null;
	}
}
