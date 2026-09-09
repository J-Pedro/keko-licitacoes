package br.com.keko.keko_licitacoes.licitacoes;

import java.util.List;
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

	private final PncpSearchClient pncpSearchClient;

	public LicitacaoSearchService(PncpSearchClient pncpSearchClient) {
		this.pncpSearchClient = pncpSearchClient;
	}

	public LicitacaoPageResponse buscar(
			String palavraChave,
			List<String> ufs,
			List<Integer> modalidades,
			String status,
			String tiposDocumento,
			String ordenacao,
			Integer pagina,
			Integer tamanhoPagina) {
		int paginaNormalizada = Math.max(Optional.ofNullable(pagina).orElse(1), 1);
		int tamanhoNormalizado = limitar(Optional.ofNullable(tamanhoPagina).orElse(10), 1, 100);

		PncpSearchResponse response = pncpSearchClient.buscarEditais(
				valorOuPadrao(tiposDocumento, "edital"),
				valorOuPadrao(ordenacao, "-data"),
				valorOuPadrao(status, "recebendo_proposta"),
				paginaNormalizada,
				tamanhoNormalizado,
				normalizarTextoOpcional(palavraChave),
				normalizarLista(ufs),
				normalizarListaNumerica(modalidades),
				"application/json",
				"keko-licitacoes-api/0.0.1");

		List<LicitacaoResponse> resultados = Optional.ofNullable(response)
				.map(PncpSearchResponse::items)
				.orElseGet(List::of)
				.stream()
				.map(this::mapear)
				.toList();

		int totalRegistros = Optional.ofNullable(response)
				.map(PncpSearchResponse::total)
				.orElse(resultados.size());
		int totalPaginas = totalRegistros == 0 ? 0 : (int) Math.ceil((double) totalRegistros / tamanhoNormalizado);
		int paginasRestantes = Math.max(totalPaginas - paginaNormalizada, 0);

		return new LicitacaoPageResponse(
				paginaNormalizada,
				tamanhoNormalizado,
				totalRegistros,
				totalPaginas,
				paginasRestantes,
				resultados);
	}

	private LicitacaoResponse mapear(PncpSearchItem item) {
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
				linkDoPortal(item));
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
