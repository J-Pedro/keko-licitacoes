# Keko Licitacoes

Coletor inicial de licitacoes publicas, comecando pelo PNCP.

Esta versao usa a busca do proprio portal do PNCP, a mesma base usada em
`https://pncp.gov.br/app/editais`, e normaliza os dados para um formato unico.
A arquitetura foi separada por fontes para facilitar a
entrada futura de Compras.gov.br, Banrisul, LicitaCon, BLL, Licitanet e outros
portais.

## Requisitos

- Python 3.11+

## Instalacao

### Com ambiente virtual

Este e o modo recomendado para desenvolvimento, porque as dependencias ficam
isoladas dentro da pasta `.venv` do projeto.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

O comando acima cria o ambiente virtual, ativa esse ambiente no PowerShell e
instala o projeto em modo editavel. Depois da instalacao, o terminal passa a
reconhecer o comando `keko-licitacoes`.

Se voce sair do ambiente virtual e quiser entrar de novo:

```powershell
cd D:\workspace\trabalho\keko
.\.venv\Scripts\Activate.ps1
```

Para sair do ambiente virtual:

```powershell
deactivate
```

### Sem ambiente virtual

Tambem e possivel instalar direto no Python do sistema:

```powershell
python -m pip install -e ".[dev]"
```

Depois disso, o comando `keko-licitacoes` fica disponivel no ambiente em que o
Python instalou o pacote. Esse modo e mais simples, mas mistura as dependencias
do projeto com as outras bibliotecas instaladas nesse Python.

## Como executar

A CLI pode ser executada de duas formas. As duas chamam a mesma funcao interna
do projeto, `keko_licitacoes.cli:main`.

### Usando `python -m`

```powershell
python -m keko_licitacoes.cli pncp `
  --palavra-chave calha `
  --pagina 1 `
  --saida resultados\pncp-calha.json
```

Esse modo executa diretamente o modulo Python `keko_licitacoes.cli` usando o
interpretador Python ativo no momento. Ele e util quando voce quer garantir que
esta usando o Python do ambiente virtual certo.

### Usando `keko-licitacoes`

```powershell
keko-licitacoes pncp `
  --palavra-chave calha `
  --pagina 1 `
  --saida resultados\pncp-calha.json
```

Esse modo usa o script instalado pelo pacote. Ele e mais curto para uso diario,
mas depende do ambiente virtual estar ativado ou do script estar disponivel no
`PATH`.

Hoje, o unico subcomando disponivel e `pncp`, usado para buscar licitacoes na
API publica do PNCP.

## Exemplos de uso

Buscar a primeira pagina de editais abertos no PNCP contendo `calha`, como no
site `https://pncp.gov.br/app/editais?pagina=1`:

```powershell
keko-licitacoes pncp `
  --palavra-chave calha `
  --pagina 1 `
  --saida resultados\pncp-calha.json
```

Por padrao, o comando chama `https://pncp.gov.br/api/search/` com
`tipos_documento=edital`, `status=recebendo_proposta`, `ordenacao=-data`,
`pagina` e `tam_pagina`. Ele nao percorre todas as paginas automaticamente.

Para navegar pelas proximas paginas, altere apenas `--pagina`:

```powershell
keko-licitacoes pncp `
  --palavra-chave calha `
  --pagina 2 `
  --saida resultados\pncp-calha-pagina-2.json
```

Tambem e possivel exportar CSV:

```powershell
keko-licitacoes pncp `
  --uf RS `
  --modalidade pregao,dispensa `
  --pagina 1 `
  --formato csv `
  --saida resultados\pncp.csv
```

Use `--tamanho-pagina` para mudar quantos registros cada pagina traz. O padrao
e `10`, igual a uma pagina pequena de validacao.

O JSON de saida inclui os metadados de pagina:

```json
{
  "pagina": 1,
  "tamanho_pagina": 10,
  "total_registros": 100,
  "total_paginas": 10,
  "paginas_restantes": 9,
  "resultados": []
}
```

As consultas legadas da API de consulta continuam disponiveis quando voce
precisar delas:

```powershell
keko-licitacoes pncp `
  --consulta proposta `
  --data-inicial 2026-08-01 `
  --data-final 2026-08-28 `
  --uf RS `
  --modalidade pregao `
  --palavra-chave calha `
  --saida resultados\pncp-propostas-calha.json
```

Opcoes de `--consulta`:

- `site`: usa a busca do portal em `/api/search/`. E o padrao.
- `publicacao`: busca por data de publicacao. Esse endpoint tem apresentado
  timeout quando o PNCP esta degradado.
- `atualizacao`: busca por data de atualizacao global.
- `proposta`: busca contratacoes com recebimento de propostas aberto ate a
  data final. Nesse modo, `--data-inicial` e mantido apenas por compatibilidade
  com o comando, pois o PNCP exige somente `dataFinal` nesse endpoint.

No modo `site`, sem `--modalidade`, o comando consulta todas as modalidades,
igual ao portal. Nas consultas legadas, sem `--modalidade`, o coletor usa as
modalidades principais do projeto: pregao eletronico, concorrencia eletronica e
dispensa.

## Argumentos do comando `pncp`

Uso geral:

```powershell
keko-licitacoes pncp [opcoes]
```

Ou, de forma equivalente:

```powershell
python -m keko_licitacoes.cli pncp [opcoes]
```

Argumentos disponiveis:

- `-h`, `--help`: mostra a ajuda do comando.
- `--data-inicial DATA`: data inicial. Aceita `YYYY-MM-DD` ou `YYYYMMDD`. No
  modo `site`, e mantida apenas por compatibilidade. Nas consultas legadas, e
  obrigatoria.
- `--data-final DATA`: data final. Aceita `YYYY-MM-DD` ou `YYYYMMDD`. No modo
  `site`, e mantida apenas por compatibilidade. Nas consultas legadas, e
  obrigatoria.
- `--uf UF`: filtra por UF. Aceita repeticao ou lista separada por virgula,
  como `--uf RS,SC` ou `--uf RS --uf SC`.
- `--modalidade MODALIDADE`: filtra por modalidade usando codigo PNCP ou alias.
  Aceita repeticao ou lista separada por virgula, como
  `--modalidade pregao,dispensa`.
- `--todas-modalidades`: usa todas as modalidades conhecidas pelo projeto.
- `--palavra-chave TEXTO`: termo de busca. No modo `site`, e enviado como `q`
  para o portal. Aceita repeticao ou lista separada por virgula.
- `--consulta {site,publicacao,atualizacao,proposta}`: escolhe o tipo de
  consulta. O padrao e `site`.
- `--pagina NUMERO`: pagina da busca do site. O padrao e `1`.
- `--status STATUS`: status usado pela busca do site. O padrao e
  `recebendo_proposta`.
- `--tipos-documento TIPO`: tipo de documento usado pela busca do site. O
  padrao e `edital`.
- `--ordenacao ORDEM`: ordenacao usada pela busca do site. O padrao e `-data`.
- `--limite NUMERO`: limita a quantidade de resultados retornados.
- `--paginas-por-consulta NUMERO`: nas consultas legadas, limita quantas
  paginas serao lidas por cada combinacao de data, modalidade e UF.
- `--tamanho-pagina NUMERO`: tamanho da pagina enviada ao PNCP. Aceita valores
  de `1` a `500`. O padrao e `10`.
- `--dias-por-consulta NUMERO`: nas consultas legadas, divide o periodo em
  janelas menores para reduzir timeouts do PNCP.
- `--timeout SEGUNDOS`: timeout por requisicao ao PNCP. O padrao e `30.0`.
- `--tentativas NUMERO`: numero de novas tentativas por pagina apos falhas. O
  padrao e `2`; aceita `0` ou mais.
- `--intervalo-retry SEGUNDOS`: espera inicial entre tentativas. O valor cresce
  a cada tentativa. O padrao e `1.0`; aceita `0` ou mais.
- `--continuar-com-erros`: pula consultas que falharem depois das tentativas e
  salva os resultados parciais.
- `--formato {json,csv}`: formato de saida. O padrao e `json`.
- `--saida CAMINHO`: caminho do arquivo de saida. Se nao for informado, o
  resultado e impresso no terminal.
- `--incluir-bruto`: inclui o payload original do PNCP no JSON de saida.

## Modalidades aceitas

Voce pode informar o codigo numerico do PNCP ou um alias:

- `leilao-eletronico` ou `leilao` = 1
- `dialogo-competitivo` ou `dialogo` = 2
- `concurso` = 3
- `concorrencia` ou `concorrencia-eletronica` = 4
- `concorrencia-presencial` = 5
- `pregao` ou `pregao-eletronico` = 6
- `pregao-presencial` = 7
- `dispensa` = 8
- `inexigibilidade` = 9
- `manifestacao-interesse` = 10
- `pre-qualificacao` = 11
- `credenciamento` = 12
- `leilao-presencial` = 13
- `inaplicabilidade` = 14
- `chamada-publica` = 15

Para usar todas as modalidades ativas conhecidas:

```powershell
keko-licitacoes pncp --data-inicial 2026-08-01 --data-final 2026-08-27 --todas-modalidades
```

## Status aceitos no modo `site`

O argumento `--status` e repassado para a busca do portal do PNCP. A CLI nao
restringe esse campo com `choices`, mas estes sao os valores usados pelo portal
em `https://pncp.gov.br/app/editais`:

- `recebendo_proposta`: A Receber/Recebendo Proposta. E o padrao da CLI.
- `propostas_encerradas`: Em Julgamento/Propostas Encerradas.
- `encerradas`: Encerradas.
- `todos`: Todos.

Exemplo:

```powershell
keko-licitacoes pncp `
  --palavra-chave calha `
  --status encerradas `
  --pagina 1 `
  --saida resultados\pncp-calha-encerradas.json
```

## Estrutura

- `src/keko_licitacoes/sources/pncp.py`: cliente e conector PNCP.
- `src/keko_licitacoes/models.py`: modelo normalizado de oportunidade.
- `src/keko_licitacoes/filters.py`: filtros locais, como palavra-chave.
- `src/keko_licitacoes/cli.py`: interface de linha de comando.

## Observacao sobre filtros

O PNCP nao possui filtro nativo por palavra-chave neste endpoint. Por isso o
coletor busca por periodo, modalidade e UF, depois aplica o filtro localmente.
Essa estrategia tambem sera usada nos portais futuros quando algum filtro nao
existir na fonte original.
