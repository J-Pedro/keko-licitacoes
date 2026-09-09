package br.com.keko.keko_licitacoes.pncp;

import java.math.BigDecimal;

import com.fasterxml.jackson.annotation.JsonProperty;

public record PncpSearchItem(
		@JsonProperty("numero_controle_pncp") String numeroControlePncp,
		@JsonProperty("orgao_nome") String orgaoNome,
		@JsonProperty("orgao_cnpj") String orgaoCnpj,
		@JsonProperty("unidade_nome") String unidadeNome,
		@JsonProperty("uf") String uf,
		@JsonProperty("municipio_nome") String municipioNome,
		@JsonProperty("modalidade_licitacao_nome") String modalidadeLicitacaoNome,
		@JsonProperty("modalidade_licitacao_id") Integer modalidadeLicitacaoId,
		@JsonProperty("description") String descricao,
		@JsonProperty("title") String titulo,
		@JsonProperty("numero") String numero,
		@JsonProperty("data_publicacao_pncp") String dataPublicacaoPncp,
		@JsonProperty("data_inicio_vigencia") String dataInicioVigencia,
		@JsonProperty("data_fim_vigencia") String dataFimVigencia,
		@JsonProperty("situacao_nome") String situacaoNome,
		@JsonProperty("valor_global") BigDecimal valorGlobal,
		@JsonProperty("document_type") String tipoDocumento,
		@JsonProperty("item_url") String itemUrl) {
}
