package br.com.keko.keko_licitacoes.pncp;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(name = "pncpSearchClient", url = "${pncp.search.url}", configuration = PncpFeignConfiguration.class)
public interface PncpSearchClient {

	@GetMapping("/api/search/")
	PncpSearchResponse buscarEditais(
			@RequestParam("tipos_documento") String tiposDocumento,
			@RequestParam("ordenacao") String ordenacao,
			@RequestParam("status") String status,
			@RequestParam("pagina") Integer pagina,
			@RequestParam("tam_pagina") Integer tamanhoPagina,
			@RequestParam(value = "q", required = false) String palavraChave,
			@RequestParam(value = "ufs", required = false) String ufs,
			@RequestParam(value = "modalidades", required = false) String modalidades,
			@RequestHeader("Accept") String accept,
			@RequestHeader("User-Agent") String userAgent);
}
