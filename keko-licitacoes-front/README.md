# Keko Licitações — Frontend

Interface Angular 21 do [Keko Licitações](../README.md). Permite montar uma busca com várias palavras-chave (em forma de chips), aplicar filtros de UF, modalidade, situação e itens por página, e navegar pelos editais retornados pela API.

## Comandos

| Comando | O que faz |
|---|---|
| `npm ci` | Instala as dependências |
| `npm start` | Servidor de desenvolvimento em `http://localhost:4200` |
| `npm test` | Testes unitários com Vitest |
| `npm run build` | Build de produção em `dist/keko-licitacoes-front/browser` |

## Configuração

A URL da API fica nos arquivos de environment:

- `src/environments/environment.ts`: `http://localhost:8080/api/licitacoes` (desenvolvimento)
- `src/environments/environment.prod.ts`: `https://keko-licitacoes-api.onrender.com/api/licitacoes` (produção)

## Estrutura

```text
src/app/
├── app.ts / app.html / app.scss   Tela de busca: filtros, chips de palavras-chave, resultados e paginação
├── licitacoes.service.ts          Chamada HTTP para a API e tipos da resposta
└── *.spec.ts                      Testes do componente e do serviço
```
