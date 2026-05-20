from .reporting import analyze_results, save_to_csv


def buscar_produtos_selenium(
    produto, loja="amazon", paginas=3, similaridade=0.3, extra_blacklist=None
):
    """Wrapper genérico que chama scrape_<loja>_selenium e opcionalmente salva CSV."""
    nome_funcao = f"scrape_{loja}_selenium"
    funcao_scrape = globals().get(nome_funcao)

    if funcao_scrape is None:
        try:
            from . import scrapers as _scrapers

            funcao_scrape = getattr(_scrapers, nome_funcao, None)
        except Exception:
            funcao_scrape = None

    if funcao_scrape is None:
        print(f"❌ Função de scraping não encontrada para a loja '{loja}'!")
        return None

    produtos = funcao_scrape(produto, paginas, similaridade, extra_blacklist)
    if produtos:
        df = analyze_results(produtos, produto)
        try:
            salvar = input("\n💾 Salvar em CSV? (s/n): ").strip().lower()
            if salvar in ["s", "sim", "y", "yes"]:
                save_to_csv(df, produto, loja)
        except Exception:
            pass
        return df

    print("\n❌ Nenhum produto encontrado. Tente termos mais específicos ou ajuste a similaridade.")
    return None


def interativo_scraper():
    """Fluxo interativo de scraping e refinamento por blacklist."""
    from . import scrapers as scrapers

    loja = input("🛍️ Digite a loja para busca (ex.: amazon, americanas): ").strip().lower()
    if not loja:
        print("❌ Você precisa digitar uma loja válida. Tente novamente.")
        return

    produto = input(f"🔎 Digite o termo de busca para {loja.capitalize()}: ").strip()
    if not produto:
        print("❌ Você precisa digitar um termo válido. Tente novamente.")
        return

    paginas = None
    while paginas is None:
        try:
            paginas = int(input("📄 Quantas páginas deseja varrer? (ex.: 3): ").strip())
            if paginas <= 0:
                print("❌ Informe um número inteiro positivo.")
                paginas = None
        except Exception:
            print("❌ Valor inválido. Por favor, digite um número inteiro.")
            paginas = None

    min_similarity = None
    while min_similarity is None:
        try:
            ms = float(
                input("🔢 Qual similaridade mínima (0.0 a 1.0)? (ex.: 0.3): ")
                .strip()
                .replace(",", ".")
            )
            if 0.0 <= ms <= 1.0:
                min_similarity = ms
            else:
                print("❌ Informe um valor entre 0.0 e 1.0.")
        except Exception:
            print("❌ Valor inválido. Digite algo como 0.3 ou 0.5.")
            min_similarity = None

    nome_funcao = f"scrape_{loja}_selenium"
    funcao_scrape = getattr(scrapers, nome_funcao, None)
    if funcao_scrape is None:
        print(f"❌ Função de scraping não encontrada para a loja '{loja}'!")
        return

    print("\n---- RESULTADOS INICIAIS (apenas com blacklist base) ----")
    resultados = funcao_scrape(produto, paginas, min_similarity, extra_blacklist=[])
    df = analyze_results(resultados, produto)

    combined_extra = []
    while True:
        resp = input(
            "\n🛑 Deseja adicionar palavras extras para filtrar resultados? (s/n): "
        ).strip().lower()

        if resp in ["n", "nao", "não", "no"]:
            break

        if resp in ["s", "sim", "yes", "y"]:
            extras_str = input(
                "✏️ Digite as palavras (separadas por vírgula) que deseja bloquear: "
            ).strip()
            if not extras_str:
                print("❌ Você não digitou nada. Tente novamente.")
                continue

            novas_palavras = [w.strip().lower() for w in extras_str.split(",") if w.strip()]
            combined_extra.extend(novas_palavras)
            combined_extra = list(set(combined_extra))

            print(f"\n---- RESULTADOS REFINADOS (blacklist extra: {combined_extra}) ----")
            resultados = funcao_scrape(
                produto, paginas, min_similarity, extra_blacklist=combined_extra
            )
            df = analyze_results(resultados, produto)
            continue

        print("❌ Resposta inválida. Digite 's' para sim ou 'n' para não.")

    try:
        salvar = input("\n💾 Deseja salvar o resultado final em CSV? (s/n): ").strip().lower()
        if salvar in ["s", "sim", "yes", "y"]:
            save_to_csv(df, produto, loja)
    except Exception:
        pass

    print("\n✅ Processo concluído. Obrigado por usar o Garimpa AI!")
