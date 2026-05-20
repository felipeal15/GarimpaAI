from .reporting import analyze_results, save_to_csv


def buscar_produtos_selenium(
    produto,
    loja="amazon",
    paginas=3,
    similaridade=0.3,
    extra_blacklist=None,
    salvar_csv=False,
):
    """API programática: busca produtos com filtragem automática de acessórios.

    Args:
        produto: termo de busca (ex.: "iphone 13").
        loja: 'amazon' ou 'americanas'.
        paginas: número de páginas a varrer.
        similaridade: similaridade mínima (0.0 a 1.0).
        extra_blacklist: lista opcional de palavras extras a filtrar
            (além das já filtradas automaticamente).
        salvar_csv: se True, salva o resultado em CSV.

    Returns:
        DataFrame ordenado dos resultados ou None se nada foi encontrado.
    """
    from . import scrapers as _scrapers

    funcao_scrape = getattr(_scrapers, f"scrape_{loja}_selenium", None)
    if funcao_scrape is None:
        print(f"❌ Loja '{loja}' não suportada. Disponíveis: amazon, americanas.")
        return None

    produtos = funcao_scrape(produto, paginas, similaridade, extra_blacklist)
    if not produtos:
        print(
            "\n❌ Nenhum produto relevante encontrado. "
            "Tente termos mais específicos ou reduza a similaridade mínima."
        )
        return None

    df = analyze_results(produtos, produto)
    if salvar_csv:
        save_to_csv(df, produto, loja)
    return df


def _perguntar_loja():
    loja = input("🛍️  Loja para busca (amazon ou americanas): ").strip().lower()
    if loja not in ("amazon", "americanas"):
        print("❌ Loja inválida. Use 'amazon' ou 'americanas'.")
        return None
    return loja


def _perguntar_int_positivo(prompt):
    while True:
        try:
            valor = int(input(prompt).strip())
            if valor > 0:
                return valor
            print("❌ Informe um número inteiro positivo.")
        except Exception:
            print("❌ Valor inválido. Digite um número inteiro.")


def _perguntar_similaridade():
    while True:
        try:
            ms = float(
                input("🔢 Similaridade mínima (0.0 a 1.0, ex.: 0.3): ")
                .strip()
                .replace(",", ".")
            )
            if 0.0 <= ms <= 1.0:
                return ms
            print("❌ Informe um valor entre 0.0 e 1.0.")
        except Exception:
            print("❌ Valor inválido. Digite algo como 0.3 ou 0.5.")


def interativo_scraper():
    """Fluxo interativo de scraping com filtragem automática de acessórios.

    O usuário fornece loja, termo de busca, número de páginas e similaridade
    mínima. A filtragem de acessórios (capas, películas, cabos, carregadores,
    fones, suportes, padrões 'para X' / 'compatível com X' etc.) é aplicada
    automaticamente — sem precisar refinar manualmente uma blacklist.
    """
    print("=" * 60)
    print("🤖 GarimpaAI — busca com filtragem automática de acessórios")
    print("=" * 60)

    loja = _perguntar_loja()
    if not loja:
        return

    produto = input(f"🔎 Termo de busca em {loja.capitalize()}: ").strip()
    if not produto:
        print("❌ Você precisa digitar um termo válido.")
        return

    paginas = _perguntar_int_positivo("📄 Quantas páginas varrer? (ex.: 3): ")
    min_similarity = _perguntar_similaridade()

    print(
        "\n🛡️  Filtros automáticos ativos: acessórios (capa, película, cabo, "
        "carregador, fone, suporte etc.) e itens descritos como 'para X' / "
        "'compatível com X' serão removidos."
    )

    df = buscar_produtos_selenium(
        produto=produto,
        loja=loja,
        paginas=paginas,
        similaridade=min_similarity,
        extra_blacklist=None,
        salvar_csv=False,
    )

    if df is None:
        return

    try:
        salvar = input("\n💾 Salvar resultado em CSV? (s/n): ").strip().lower()
        if salvar in ("s", "sim", "yes", "y"):
            save_to_csv(df, produto, loja)
    except Exception:
        pass

    print("\n✅ Processo concluído. Obrigado por usar o GarimpaAI!")
