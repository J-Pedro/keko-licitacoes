package br.com.keko.keko_licitacoes.licitacoes;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.inOrder;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InOrder;

import br.com.keko.keko_licitacoes.pncp.PncpSearchClient;
import br.com.keko.keko_licitacoes.pncp.PncpSearchItem;
import br.com.keko.keko_licitacoes.pncp.PncpSearchResponse;

class LicitacaoSearchServiceTest {

	private PncpSearchClient pncpSearchClient;
	private KeywordSearchDelay keywordSearchDelay;
	private LicitacaoSearchService service;

	@BeforeEach
	void setUp() {
		pncpSearchClient = mock(PncpSearchClient.class);
		keywordSearchDelay = mock(KeywordSearchDelay.class);
		service = new LicitacaoSearchService(pncpSearchClient, keywordSearchDelay);
	}

	@Test
	void deveExecutarUmaConsultaPorPalavraMantendoFiltrosEIntervaloSequencial() {
		when(pncpSearchClient.buscarEditais(
				"edital", "-data", "todos", 2, 25, "notebook", "MG", "6,4", "application/json",
				"keko-licitacoes-api/0.0.1")).thenReturn(response(item("edital-1", "2026-09-01")));
		when(pncpSearchClient.buscarEditais(
				"edital", "-data", "todos", 2, 25, "monitor", "MG", "6,4", "application/json",
				"keko-licitacoes-api/0.0.1")).thenReturn(response(item("edital-2", "2026-09-02")));

		LicitacaoPageResponse resultado = service.buscar(
				List.of("notebook", "monitor"),
				List.of("mg"),
				List.of(6, 4),
				"todos",
				"edital",
				"-data",
				2,
				25);

		InOrder ordem = inOrder(pncpSearchClient, keywordSearchDelay);
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "todos", 2, 25, "notebook", "MG", "6,4", "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verify(keywordSearchDelay).aguardarEntreConsultas();
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "todos", 2, 25, "monitor", "MG", "6,4", "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verifyNoMoreInteractions();

		assertThat(resultado.resultados())
				.extracting(LicitacaoResponse::idExterno)
				.containsExactly("edital-2", "edital-1");
	}

	@Test
	void deveAcumularDeduplicarMesclarPalavrasEOrdenarDepoisDaAgregacao() {
		when(buscar("material de construcao")).thenReturn(response(
				item("edital-a", "2026-09-01"),
				item("edital-a", "2026-09-01"),
				item("edital-b", "2026-09-03")));
		when(buscar("equipamento")).thenReturn(response(
				item("edital-c", "2026-09-05"),
				item("edital-a", "2026-09-01")));

		LicitacaoPageResponse resultado = service.buscar(
				List.of("material de construcao", "equipamento"),
				List.of(),
				List.of(),
				"recebendo_proposta",
				"edital",
				"-data",
				1,
				10);

		assertThat(resultado.totalRegistros()).isEqualTo(3);
		assertThat(resultado.resultados())
				.extracting(LicitacaoResponse::idExterno)
				.containsExactly("edital-c", "edital-b", "edital-a");
		assertThat(porId(resultado, "edital-c").matchedKeywords()).containsExactly("equipamento");
		assertThat(porId(resultado, "edital-a").matchedKeywords())
				.containsExactly("material de construcao", "equipamento");
	}

	@Test
	void deveContinuarConsultandoDemaisPalavrasQuandoUmaFalhar() {
		when(buscar("notebook")).thenReturn(response(item("notebook-1", "2026-09-04")));
		when(buscar("computador")).thenThrow(new RuntimeException("erro pncp"));
		when(buscar("monitor")).thenReturn(response(item("monitor-1", "2026-09-05")));

		LicitacaoPageResponse resultado = service.buscar(
				List.of("notebook", "computador", "monitor"),
				List.of(),
				List.of(),
				"recebendo_proposta",
				"edital",
				"-data",
				1,
				10);

		assertThat(resultado.resultados())
				.extracting(LicitacaoResponse::idExterno)
				.containsExactly("monitor-1", "notebook-1");
		assertThat(resultado.erros()).containsExactly(new LicitacaoSearchError(
				"computador",
				"Nao foi possivel consultar esta palavra-chave no PNCP."));

		InOrder ordem = inOrder(pncpSearchClient, keywordSearchDelay);
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "recebendo_proposta", 1, 10, "notebook", null, null, "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verify(keywordSearchDelay).aguardarEntreConsultas();
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "recebendo_proposta", 1, 10, "computador", null, null, "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verify(keywordSearchDelay).aguardarEntreConsultas();
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "recebendo_proposta", 1, 10, "monitor", null, null, "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verifyNoMoreInteractions();
	}

	@Test
	void deveIgnorarPalavrasVaziasEDuplicadasAntesDeConsultar() {
		when(buscar("Notebook")).thenReturn(response(item("edital-1", "2026-09-01")));
		when(buscar("Monitor")).thenReturn(response(item("edital-2", "2026-09-02")));

		LicitacaoPageResponse resultado = service.buscar(
				List.of("  Notebook  ", "", "notebook", "Monitor"),
				List.of(),
				List.of(),
				"recebendo_proposta",
				"edital",
				"-data",
				1,
				10);

		assertThat(resultado.resultados())
				.extracting(LicitacaoResponse::idExterno)
				.containsExactly("edital-2", "edital-1");

		InOrder ordem = inOrder(pncpSearchClient, keywordSearchDelay);
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "recebendo_proposta", 1, 10, "Notebook", null, null, "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verify(keywordSearchDelay).aguardarEntreConsultas();
		ordem.verify(pncpSearchClient).buscarEditais(
				"edital", "-data", "recebendo_proposta", 1, 10, "Monitor", null, null, "application/json",
				"keko-licitacoes-api/0.0.1");
		ordem.verifyNoMoreInteractions();
	}

	private PncpSearchResponse buscar(String palavraChave) {
		return pncpSearchClient.buscarEditais(
				"edital",
				"-data",
				"recebendo_proposta",
				1,
				10,
				palavraChave,
				null,
				null,
				"application/json",
				"keko-licitacoes-api/0.0.1");
	}

	private LicitacaoResponse porId(LicitacaoPageResponse resultado, String idExterno) {
		return resultado.resultados()
				.stream()
				.filter((licitacao) -> idExterno.equals(licitacao.idExterno()))
				.findFirst()
				.orElseThrow();
	}

	private PncpSearchResponse response(PncpSearchItem... items) {
		return new PncpSearchResponse(List.of(items), items.length);
	}

	private PncpSearchItem item(String idExterno, String dataPublicacao) {
		return new PncpSearchItem(
				idExterno,
				"Orgao",
				"00000000000100",
				"Unidade",
				"MG",
				"Belo Horizonte",
				"Pregao - Eletronico",
				6,
				"Objeto",
				"Edital " + idExterno,
				"1/2026",
				dataPublicacao,
				null,
				null,
				"Divulgado no PNCP",
				BigDecimal.TEN,
				"edital",
				"/compras/" + idExterno);
	}
}
