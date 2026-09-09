package br.com.keko.keko_licitacoes.pncp;

import org.springframework.context.annotation.Bean;

import feign.Retryer;

public class PncpFeignConfiguration {

	@Bean
	Retryer pncpRetryer() {
		return new Retryer.Default(1_000, 3_000, 3);
	}
}
