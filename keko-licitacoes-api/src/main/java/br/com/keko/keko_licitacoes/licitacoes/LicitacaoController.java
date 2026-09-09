package br.com.keko.keko_licitacoes.licitacoes;

import java.util.List;

import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@CrossOrigin(origins = { "http://localhost:4200", "http://127.0.0.1:4200" })
@RestController
@RequestMapping("/api/licitacoes")
public class LicitacaoController {

	private final LicitacaoSearchService licitacaoSearchService;

	public LicitacaoController(LicitacaoSearchService licitacaoSearchService) {
		this.licitacaoSearchService = licitacaoSearchService;
	}

	@GetMapping
	public LicitacaoPageResponse buscar(
			@RequestParam(value = "palavraChave", required = false) String palavraChave,
			@RequestParam(value = "uf", required = false) List<String> ufs,
			@RequestParam(value = "modalidade", required = false) List<Integer> modalidades,
			@RequestParam(value = "status", required = false, defaultValue = "recebendo_proposta") String status,
			@RequestParam(value = "tiposDocumento", required = false, defaultValue = "edital") String tiposDocumento,
			@RequestParam(value = "ordenacao", required = false, defaultValue = "-data") String ordenacao,
			@RequestParam(value = "pagina", required = false, defaultValue = "1") Integer pagina,
			@RequestParam(value = "tamanhoPagina", required = false, defaultValue = "10") Integer tamanhoPagina) {
		return licitacaoSearchService.buscar(
				palavraChave,
				ufs,
				modalidades,
				status,
				tiposDocumento,
				ordenacao,
				pagina,
				tamanhoPagina);
	}
}
