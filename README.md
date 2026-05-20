# GarimpaAI

Projeto de **web scraping** que coleta ofertas de produtos em marketplaces (atualmente **Amazon** e **Americanas**), aplica filtros de relevância (similaridade + blacklist) e ajuda a comparar preços, com opção de exportar resultados para CSV e fazer uma análise/gráficos em cima desses CSVs.

Este repositório contém:

- Um notebook final do projeto (original do Colab): `Entrega_final.ipynb`
- Uma estrutura Python para rodar **localmente**: `src/garimpaai/`

> Nota: scraping em marketplaces pode ser bloqueado (ex.: HTTP 503/antibot). O projeto já usa esperas aleatórias para reduzir bloqueios, mas não há garantia.

## Status (o que já está feito)

- Scraper via Selenium (headless) para:
	- Amazon (`scrape_amazon_selenium`)
	- Americanas (`scrape_americanas_selenium`)
- Normalização/limpeza:
	- Remoção de acentos via RegEx
	- Limpeza de título
	- Conversão de preço para `float`
	- Similaridade simples por interseção de palavras
	- Blacklist de palavras para filtrar itens irrelevantes
- Relatório no terminal:
	- Estatísticas (min/max/média) e top 10 mais baratos
- Exportação:
	- Salvar CSV com os resultados
- Análise pós-coleta:
	- Ler CSVs, gerar gráficos Top 10 por loja e calcular loja com menor preço médio

## Estrutura do projeto (local)

Arquivos principais:

- `requirements.txt` — dependências para rodar localmente
- `pyproject.toml` — permite instalar como pacote (`pip install -e .`)
- `src/garimpaai/` — código modularizado a partir do notebook

Módulos:

- `garimpaai.browser`: inicialização do ChromeDriver (webdriver-manager)
- `garimpaai.text_utils`: limpeza de texto/preço + similaridade + blacklist
- `garimpaai.scrapers`: scraping Amazon/Americanas
- `garimpaai.reporting`: análise/relatório + salvar CSV
- `garimpaai.interactive`: fluxo interativo (CLI no terminal)
- `garimpaai.analysis`: análise de CSVs e geração de gráficos

## Como rodar localmente (Windows)

### Pré-requisitos

- Python 3.10+
- Google Chrome instalado

O `webdriver-manager` baixa automaticamente um ChromeDriver compatível.

Se o Selenium não encontrar o Chrome, defina a variável de ambiente `GARIMPA_CHROME_BINARY` apontando para o executável do Chrome.

Exemplos comuns:

- `C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe`
- `C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe`

### 1) Criar e ativar ambiente virtual

No PowerShell, na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

### 2) Instalar dependências

Opção A (recomendada): instalar o pacote em modo editável

```powershell
pip install -e .
```

Opção B: instalar via `requirements.txt`

```powershell
pip install -r requirements.txt
```

### 3) Rodar o fluxo interativo (scraping)

```powershell
garimpaai
```

Ou equivalentemente:

```powershell
python -m garimpaai
```

O programa vai perguntar:

- loja (`amazon` ou `americanas`)
- termo de busca
- número de páginas
- similaridade mínima
- (opcional) blacklist extra

Ao final, você pode salvar em CSV.

### 4) Rodar a análise de CSVs (gráficos)

Você pode chamar a função diretamente no Python:

```powershell
python -c "from garimpaai.analysis import analise_precos_lojas; analise_precos_lojas(['amazon','americanas'], ['amazon_monitor.csv','americanas_monitor.csv'])"
```

## Notebook do Colab

O notebook original está em `Entrega_final.ipynb` e também pode ser aberto no VS Code/Jupyter.

## Próximos passos (quando você pedir melhorias)

- Tornar o scraper mais resiliente (tratamento de captcha/503, retries, timeouts)
- Criar CLI com argumentos (sem prompts)
- Melhorar qualidade da similaridade (ex.: stemming/tokenização)
- Expandir lojas e padronizar schemas de resultados
