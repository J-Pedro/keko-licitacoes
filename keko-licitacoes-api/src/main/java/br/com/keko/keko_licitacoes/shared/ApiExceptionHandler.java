package br.com.keko.keko_licitacoes.shared;

import java.time.Instant;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import feign.FeignException;

@RestControllerAdvice
public class ApiExceptionHandler {

	@ExceptionHandler(FeignException.class)
	public ProblemDetail handleFeignException(FeignException exception) {
		ProblemDetail problem = ProblemDetail.forStatusAndDetail(
				HttpStatus.BAD_GATEWAY,
				"Nao foi possivel consultar o PNCP agora. Tente novamente em instantes.");
		problem.setTitle("Falha na consulta ao PNCP");
		problem.setProperty("timestamp", Instant.now());
		problem.setProperty("statusPncp", exception.status());
		return problem;
	}
}
