package br.com.keko.keko_licitacoes.pncp;

import java.util.List;

public record PncpSearchResponse(
		List<PncpSearchItem> items,
		Integer total) {
}
