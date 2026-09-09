# Keko Licitacoes

Aplicacao para consultar editais de licitacao publicados no PNCP. O projeto esta dividido em dois modulos:

- `keko-licitacoes-front`: frontend Angular.
- `keko-licitacoes-api`: backend Java com Spring Boot.

## Funcionalidades

- Busca de editais por palavra-chave.
- Filtros por UF, status, modalidade e ordenacao.
- Paginacao dos resultados.
- Exibicao de orgao, municipio, datas, valor estimado e link para abrir o edital no PNCP.

## Requisitos

- Java 21.
- Node.js e npm.
- Maven Wrapper incluso no backend.

## Como rodar

### 1. Backend Java

Entre na pasta da API:

```bash
cd keko-licitacoes-api
```

No Windows:

```bash
.\mvnw.cmd spring-boot:run
```

No Linux/macOS:

```bash
./mvnw spring-boot:run
```

A API sobe em:

```text
http://localhost:8080
```

Endpoint principal:

```text
GET http://localhost:8080/api/licitacoes
```

Parametros aceitos:

- `palavraChave`: termo de busca.
- `uf`: uma ou mais UFs.
- `modalidade`: uma ou mais modalidades pelo codigo do PNCP.
- `status`: status da licitacao. Padrao: `recebendo_proposta`.
- `tiposDocumento`: tipo de documento. Padrao: `edital`.
- `ordenacao`: ordenacao dos resultados. Padrao: `-data`.
- `pagina`: pagina desejada. Padrao: `1`.
- `tamanhoPagina`: quantidade por pagina. Padrao: `10`.

Exemplo:

```text
http://localhost:8080/api/licitacoes?palavraChave=calhas&uf=SP&pagina=1&tamanhoPagina=10
```

### 2. Frontend Angular

Em outro terminal, entre na pasta do frontend:

```bash
cd keko-licitacoes-front
```

Instale as dependencias:

```bash
npm install
```

Rode a aplicacao:

```bash
npm start
```

O frontend fica disponivel em:

```text
http://localhost:4200
```

O Angular consome a API em `http://localhost:8080/api/licitacoes`, entao mantenha o backend rodando antes de buscar editais pela tela.

## Testes e build

Backend:

```bash
cd keko-licitacoes-api
.\mvnw.cmd test
```

Frontend:

```bash
cd keko-licitacoes-front
npm test
npm run build
```

## Configuracao

As configuracoes principais do backend ficam em:

```text
keko-licitacoes-api/src/main/resources/application.properties
```

Valores atuais:

- Porta da API: `8080`.
- URL base do PNCP: `https://pncp.gov.br`.
- CORS liberado para `http://localhost:4200` e `http://127.0.0.1:4200`.

## Estrutura

```text
keko/
  keko-licitacoes-api/    Backend Spring Boot
  keko-licitacoes-front/  Frontend Angular
  README.md
```
