"""Frontend Streamlit do GarimpaAI.

Rode com:
    garimpaai-ui

Ou diretamente:
    streamlit run src/garimpaai/app.py
"""
import io
import re

import pandas as pd
import streamlit as st

from garimpaai import scrapers
from garimpaai.text_utils import ACCESSORY_GROUPS

LOJAS_DISPONIVEIS = ["amazon", "americanas"]


# ─── Aba 1: busca ──────────────────────────────────────────────────────────────

def render_busca():
    with st.sidebar:
        st.header("⚙️ Configurações")

        with st.form("form_busca"):
            loja = st.selectbox("Loja", LOJAS_DISPONIVEIS)
            produto = st.text_input("Termo de busca", placeholder="ex.: iphone 13")
            paginas = st.slider("Páginas a varrer", 1, 10, 3)
            min_sim = st.slider(
                "Similaridade mínima",
                0.0, 1.0, 0.3, 0.05,
                help="Fração mínima de palavras da busca que devem aparecer no título.",
            )
            extras_str = st.text_area(
                "Blacklist extra (opcional)",
                placeholder="palavras separadas por vírgula\nex.: recondicionado, vitrine",
                height=80,
            )
            submit = st.form_submit_button(
                "🔍 Buscar", type="primary", use_container_width=True
            )

        with st.expander("ℹ️ Como funciona o filtro automático"):
            st.write(
                "Acessórios são removidos automaticamente. Os grupos abaixo "
                "são desligados quando você busca por um deles (ex.: buscar "
                "`capa iphone` libera capa, case, cover, bumper, skin)."
            )
            for nome, kws in ACCESSORY_GROUPS.items():
                st.write(f"**{nome}** — {', '.join(kws)}")
            st.write(
                "Também são filtrados títulos com padrões `para X`, "
                "`compatível com X` e `p/ X` derivados do que você buscou."
            )

    # Conteúdo principal
    if not submit:
        st.info(
            "👈 Preencha o formulário ao lado e clique em **Buscar**.\n\n"
            "A filtragem de acessórios (capas, películas, cabos, carregadores, "
            "fones etc.) acontece automaticamente — você só recebe o produto "
            "que realmente buscou."
        )
        return

    if not produto.strip():
        st.error("❌ Digite um termo de busca antes de prosseguir.")
        return

    extra_blacklist = [
        w.strip().lower()
        for w in (extras_str or "").split(",")
        if w.strip()
    ]

    funcao_scrape = getattr(scrapers, f"scrape_{loja}_selenium", None)
    if funcao_scrape is None:
        st.error(f"❌ Loja '{loja}' não suportada.")
        return

    with st.spinner(
        f"Buscando '{produto}' em {loja.capitalize()} ({paginas} página(s))... "
        "pode levar alguns segundos."
    ):
        try:
            resultados = funcao_scrape(
                produto, paginas, min_sim, extra_blacklist or None
            )
        except Exception as e:
            st.error(f"❌ Erro durante a busca: {e}")
            st.exception(e)
            return

    if not resultados:
        st.warning(
            "Nenhum produto relevante encontrado. Tente termos mais "
            "específicos, reduza a similaridade ou aumente o número de páginas."
        )
        return

    df = (
        pd.DataFrame(resultados)
        .sort_values(["preco", "similaridade"], ascending=[True, False])
        .reset_index(drop=True)
    )

    st.success(f"✅ {len(df)} produtos relevantes encontrados em {loja.capitalize()}.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Menor preço", f"R$ {df['preco'].min():,.2f}")
    c2.metric("💸 Maior preço", f"R$ {df['preco'].max():,.2f}")
    c3.metric("📊 Preço médio", f"R$ {df['preco'].mean():,.2f}")
    c4.metric("📦 Total", len(df))

    st.subheader("🏆 Top 10 mais baratos")
    top = df.head(10).copy()
    top["label"] = top["titulo"].str.slice(0, 40) + "…"
    st.bar_chart(top.set_index("label")["preco"], height=320)

    st.subheader("📋 Resultados completos")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
            "avaliacao": st.column_config.NumberColumn("⭐", format="%.1f"),
            "num_avaliacoes": st.column_config.NumberColumn("# avaliações", format="%d"),
            "link": st.column_config.LinkColumn("Link", display_text="abrir"),
            "similaridade": st.column_config.NumberColumn(
                "Relevância", format="%.0f%%",
            ),
            "pagina": st.column_config.NumberColumn("Pág.", format="%d"),
        },
    )

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding="utf-8")
    safe_name = re.sub(r"[^a-z0-9_]+", "_", produto.lower().strip())
    st.download_button(
        label="📥 Baixar CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{loja}_{safe_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ─── Aba 2: comparação entre lojas ─────────────────────────────────────────────

def _ler_csv_uploaded(uploaded):
    """Lê um CSV enviado pelo usuário (com fallback de separador)."""
    raw = uploaded.read()
    for sep in (",", ";"):
        try:
            return pd.read_csv(io.BytesIO(raw), sep=sep)
        except Exception:
            continue
    raise ValueError(f"Não consegui ler {uploaded.name} como CSV.")


def _normalizar_preco(serie):
    if serie.dtype == "object":
        s = serie.astype(str).str.replace(r"[R$\s]", "", regex=True)
        s = s.str.replace(",", ".", regex=False)
        return pd.to_numeric(s, errors="coerce")
    return serie


def _nome_loja_do_arquivo(filename):
    """Deduz nome da loja a partir do nome do arquivo (convenção '{loja}_{produto}.csv')."""
    base = filename.rsplit(".", 1)[0]
    return base.split("_", 1)[0].capitalize() if "_" in base else base


def render_comparacao():
    st.subheader("📊 Comparar preços entre lojas")
    st.caption(
        "Envie 2 ou mais CSVs gerados na aba **Buscar** (ou usando "
        "`garimpaai`) e veja qual loja tem o menor preço médio."
    )

    arquivos = st.file_uploader(
        "CSVs para comparar",
        type=["csv"],
        accept_multiple_files=True,
    )

    if not arquivos:
        st.info("Selecione 2 ou mais arquivos CSV para comparar.")
        return

    all_data = []
    for f in arquivos:
        nome_loja = _nome_loja_do_arquivo(f.name)
        try:
            df_store = _ler_csv_uploaded(f)
        except Exception as e:
            st.error(f"❌ {f.name}: {e}")
            continue

        col_titulo = next(
            (c for c in df_store.columns if c.lower() == "titulo"), None
        )
        col_preco = next(
            (c for c in df_store.columns if c.lower() == "preco"), None
        )
        if not col_titulo or not col_preco:
            st.error(
                f"❌ {f.name}: faltam colunas 'titulo' e/ou 'preco'. "
                f"Colunas: {list(df_store.columns)}"
            )
            continue

        df_proc = df_store[[col_titulo, col_preco]].rename(
            columns={col_titulo: "titulo", col_preco: "preco"}
        ).copy()
        df_proc["preco"] = _normalizar_preco(df_proc["preco"])
        df_proc = df_proc.dropna(subset=["preco"])
        df_proc["Loja"] = nome_loja
        all_data.append(df_proc)

    if not all_data:
        st.warning("Nenhum CSV pôde ser processado.")
        return

    df = pd.concat(all_data, ignore_index=True)
    st.success(
        f"✅ {len(df)} registros lidos de {df['Loja'].nunique()} loja(s): "
        f"{', '.join(df['Loja'].unique())}"
    )

    media = (
        df.groupby("Loja")["preco"]
        .agg(["mean", "min", "max", "count"])
        .rename(columns={
            "mean": "Preço médio",
            "min": "Menor preço",
            "max": "Maior preço",
            "count": "# produtos",
        })
        .sort_values("Preço médio")
    )

    st.subheader("📈 Estatísticas por loja")
    st.dataframe(
        media,
        use_container_width=True,
        column_config={
            "Preço médio": st.column_config.NumberColumn(format="R$ %.2f"),
            "Menor preço": st.column_config.NumberColumn(format="R$ %.2f"),
            "Maior preço": st.column_config.NumberColumn(format="R$ %.2f"),
        },
    )

    vencedora = media.index[0]
    preco_med = media.iloc[0]["Preço médio"]
    st.success(
        f"🏆 **{vencedora}** tem o menor preço médio: **R$ {preco_med:,.2f}**"
    )

    st.subheader("💲 Top 10 mais baratos por loja")
    for loja in df["Loja"].unique():
        with st.expander(f"📦 {loja}", expanded=True):
            top = (
                df[df["Loja"] == loja]
                .sort_values("preco")
                .head(10)
                .copy()
            )
            top["label"] = top["titulo"].str.slice(0, 40) + "…"
            st.bar_chart(top.set_index("label")["preco"], height=300)


# ─── App principal ─────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="GarimpaAI",
        page_icon="🛒",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🛒 GarimpaAI")
    st.caption(
        "Garimpe os melhores preços em Amazon e Americanas, "
        "sem acessórios atrapalhando."
    )

    tab_busca, tab_compara = st.tabs(["🔍 Buscar produtos", "📊 Comparar lojas"])

    with tab_busca:
        render_busca()

    with tab_compara:
        render_comparacao()


main()
