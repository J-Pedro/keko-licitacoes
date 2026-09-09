package br.com.keko.keko_licitacoes;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@EnableFeignClients
@SpringBootApplication
public class KekoLicitacoesApplication {

	public static void main(String[] args) {
		SpringApplication.run(KekoLicitacoesApplication.class, args);
	}

}
