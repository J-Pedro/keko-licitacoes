package br.com.keko.keko_licitacoes.licitacoes;

import java.util.List;

public record LicitacaoPageResponse(
		Integer pagina,
		Integer tamanhoPagina,
		Integer totalRegistros,
		Integer totalPaginas,
		Integer paginasRestantes,
		List<LicitacaoResponse> resultados) {
}
