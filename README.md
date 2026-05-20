# GarimpaAI

Projeto de **web scraping** que coleta ofertas de produtos em marketplaces (atualmente **Amazon** e **Americanas**), aplica **filtragem automática de acessórios** (capas, películas, cabos, carregadores, fones, suportes etc.) para te entregar só o produto que você realmente buscou, compara preços e exporta resultados para CSV — com análise/gráficos por loja.

Este repositório contém:

- Um notebook final do projeto (original do Colab): `Entrega_final.ipynb`
- Uma estrutura Python para rodar **localmente**: `src/garimpaai/`

> Nota: scraping em marketplaces pode ser bloqueado (ex.: HTTP 503/antibot). O projeto já usa esperas aleatórias para reduzir bloqueios, mas não há garantia.

## Status (o que já está feito)

- Scraper via Selenium (headless) para:
	- Amazon (`scrape_amazon_selenium`)
	- Americanas (`scrape_americanas_selenium`)
- **Filtragem automática inteligente** (sem refinar blacklist na mão):
	- Blacklist embutida de acessórios (capa, capinha, película, cabo,
	  carregador, fone, suporte, tripé, kit reparo, peças de reposição etc.)
	- Detecção dinâmica de padrões `para X`, `compatível com X`, `p/ X`
	  no título — pega o caso em que o item é um acessório PARA o produto
	  buscado e não o produto em si.
	- Blacklist *consciente da busca*: se você procura "capa iphone",
	  "capa" deixa de ser filtrado automaticamente.
	- Similaridade mínima configurável (interseção de palavras).
	- Blacklist extra opcional via API (`extra_blacklist=[...]`).
- Normalização/limpeza:
	- Remoção de acentos via RegEx
	- Limpeza de título
	- Conversão de preço para `float`
- Relatório no terminal:
	- Estatísticas (min/max/média) e top 10 mais baratos
	- Contadores brutos vs. relevantes por página
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
- `garimpaai.analysis`: análise de CSVs e geração de gráficos (matplotlib)
- `garimpaai.app`: frontend web (Streamlit) — buscar + comparar lojas
- `garimpaai.launcher`: comando `garimpaai-ui` que inicia o frontend

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

### 3) Rodar o frontend web (recomendado)

```powershell
garimpaai-ui
```

Abre uma página local no navegador (`http://localhost:8501`) com duas abas:

- **🔍 Buscar produtos**: escolhe loja, termo, páginas e similaridade; mostra
  estatísticas, gráfico Top 10 e tabela completa com link clicável + botão
  para baixar CSV.
- **📊 Comparar lojas**: faz upload de 2+ CSVs gerados na primeira aba (ou
  pela CLI) e mostra qual loja tem o menor preço médio + gráfico Top 10 por
  loja.

### 4) Rodar o fluxo interativo no terminal (alternativa)

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

A filtragem de acessórios acontece **automaticamente** — você não precisa
mais ficar adicionando palavras na mão pra filtrar capinhas, películas etc.
Ao final, você pode salvar em CSV.

### Como funciona a filtragem automática

Para cada produto, três checagens decidem se ele é relevante:

1. **Blacklist embutida de acessórios** (`ACCESSORY_KEYWORDS` em
   `garimpaai.text_utils`): palavras/frases como `capa`, `película`,
   `cabo usb`, `carregador`, `fone de ouvido`, `suporte`, `tripé`, `kit
   reparo`, `tampa traseira` etc. são filtradas — exceto quando aparecem
   no próprio termo buscado.
2. **Detecção dinâmica de acessório**: padrões regex como
   `para iphone`, `compatível com xiaomi`, `p/ samsung` são gerados a
   partir das palavras significativas da busca e filtram itens
   descritos como acessório PARA aquele produto.
3. **Similaridade mínima**: percentual de palavras do termo buscado
   que precisam aparecer no título.

Exemplos rápidos buscando `iphone`:

| Título encontrado                        | Decisão | Motivo                             |
|------------------------------------------|---------|------------------------------------|
| iPhone 13 128GB                          | ✅ mantém | passou em todos os filtros          |
| Capa de Silicone para iPhone 13          | ❌ drop  | `capa` + padrão `para iphone`       |
| Película de Vidro Compatível com iPhone  | ❌ drop  | `película` + `compativel com iphone`|
| Carregador 20W p/ iPhone                 | ❌ drop  | `carregador` + `p/ iphone`          |

Para estender ou customizar, edite as listas em
[`src/garimpaai/text_utils.py`](src/garimpaai/text_utils.py) ou
passe `extra_blacklist=[...]` chamando o scraper diretamente:

```python
from garimpaai.interactive import buscar_produtos_selenium
df = buscar_produtos_selenium(
    produto="iphone 13",
    loja="amazon",
    paginas=3,
    similaridade=0.4,
    extra_blacklist=["recondicionado", "vitrine"],
    salvar_csv=True,
)
```

### 5) Análise de CSVs por script (sem UI)

Para gerar gráficos matplotlib direto do Python:

```powershell
python -c "from garimpaai.analysis import analise_precos_lojas; analise_precos_lojas(['amazon','americanas'], ['amazon_monitor.csv','americanas_monitor.csv'])"
```

> Para uso interativo a aba **Comparar lojas** do `garimpaai-ui` é mais conveniente.

## Notebook do Colab

O notebook original está em `Entrega_final.ipynb` e também pode ser aberto no VS Code/Jupyter.

## Próximos passos (quando você pedir melhorias)

- Tornar o scraper mais resiliente (tratamento de captcha/503, retries, timeouts)
- Criar CLI com argumentos (sem prompts)
- Melhorar qualidade da similaridade (ex.: stemming/tokenização ou embeddings)
- Expandir a blacklist embutida por categoria (eletrônicos, moda, livros etc.)
- Expandir lojas e padronizar schemas de resultados
