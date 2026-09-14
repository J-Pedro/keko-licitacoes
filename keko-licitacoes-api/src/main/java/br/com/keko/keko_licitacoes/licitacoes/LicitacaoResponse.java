package br.com.keko.keko_licitacoes.licitacoes;

import java.math.BigDecimal;
import java.util.List;

public record LicitacaoResponse(
		String fonte,
		String idExterno,
		String orgao,
		String cnpjOrgao,
		String unidade,
		String uf,
		String municipio,
		String modalidade,
		Integer modalidadeId,
		String objeto,
		String numeroEdital,
		String dataPublicacao,
		String dataAberturaProposta,
		String dataEncerramentoProposta,
		String situacao,
		BigDecimal valorEstimado,
		String sistemaOrigem,
		String link,
		List<String> matchedKeywords) {
}
