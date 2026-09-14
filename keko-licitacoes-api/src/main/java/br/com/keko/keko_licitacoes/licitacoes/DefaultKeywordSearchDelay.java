package br.com.keko.keko_licitacoes.licitacoes;

import org.springframework.stereotype.Component;

@Component
public class DefaultKeywordSearchDelay implements KeywordSearchDelay {

	private static final long DELAY_MS = 5000;

	@Override
	public void aguardarEntreConsultas() {
		try {
			Thread.sleep(DELAY_MS);
		} catch (InterruptedException exception) {
			Thread.currentThread().interrupt();
			throw new IllegalStateException("Busca interrompida durante o intervalo entre consultas.", exception);
		}
	}
}
