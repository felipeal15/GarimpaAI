import math
import pandas as pd


def analyze_results(produtos, produto_buscado):
    """Imprime estatísticas e retorna DataFrame ordenado."""
    if not produtos:
        print("❌ Nenhum produto encontrado!")
        return None

    df = pd.DataFrame(produtos)
    df_sorted = df.sort_values(["preco", "similaridade"], ascending=[True, False])

    print("\n" + "=" * 60)
    print(f"🎯 RESULTADOS PARA: '{produto_buscado.upper()}'")
    print("=" * 60)
    print(f"📦 Total de produtos (após filtro): {len(produtos)}")
    print(f"💰 Menor preço: R$ {df['preco'].min():.2f}")
    print(f"💸 Maior preço: R$ {df['preco'].max():.2f}")
    print(f"📊 Preço médio: R$ {df['preco'].mean():.2f}")

    if "avaliacao" in df.columns and df["avaliacao"].notna().any():
        print(f"⭐ Avaliação média: {df['avaliacao'].mean():.1f}")

    print("\n🏆 TOP 10 MAIS BARATOS:")
    print("-" * 60)

    for i, (_, produto) in enumerate(df_sorted.head(10).iterrows(), start=1):
        print(f"\n{i}. 💰 R$ {produto['preco']:.2f}")
        print(f"   📦 {produto['titulo']}")

        avaliacao = produto.get("avaliacao")
        if avaliacao is not None and not (
            isinstance(avaliacao, float) and math.isnan(avaliacao)
        ):
            stars = "⭐" * min(int(avaliacao), 5)
            num_avals = produto.get("num_avaliacoes")
            if num_avals is None or (
                isinstance(num_avals, float) and math.isnan(num_avals)
            ):
                num_avals = 0
            print(f"   {stars} {avaliacao:.1f} ({int(num_avals)} avaliações)")

        print(f"   🔗 {produto.get('link')}")
        print(f"   📊 Relevância: {produto['similaridade']:.1%}")

    return df_sorted


def save_to_csv(df, produto_buscado, loja):
    """Salva o DataFrame em CSV com nome baseado na loja e no produto."""
    if df is not None and not df.empty:
        filename = f"{loja}_{produto_buscado.replace(' ', '_')}.csv"
        df.to_csv(filename, index=False, encoding="utf-8")
        print(f"\n💾 Arquivo salvo: {filename}")
