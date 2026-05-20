import os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def analise_precos_lojas(nomes_lojas, csv_files):
    if len(nomes_lojas) != len(csv_files):
        raise ValueError(
            "O número de nomes de lojas deve ser igual ao número de arquivos CSV."
        )

    all_data = []

    print("Iniciando o processamento dos arquivos CSV...")
    for nome_loja, file_path in zip(nomes_lojas, csv_files):
        print(
            f"Processando arquivo da loja: {nome_loja} ({os.path.basename(file_path)})...",
            end=" ",
        )
        try:
            try:
                df_store = pd.read_csv(file_path, sep=",")
            except pd.errors.ParserError:
                try:
                    df_store = pd.read_csv(file_path, sep=";")
                except Exception as e:
                    print(
                        f"\nErro ao ler {file_path} com separadores ',' e ';': {e}"
                    )
                    continue

            if "titulo" not in df_store.columns or "preco" not in df_store.columns:
                nome_col = next((col for col in df_store.columns if col.lower() == "titulo"), None)
                preco_col = next((col for col in df_store.columns if col.lower() == "preco"), None)

                if not nome_col or not preco_col:
                    print(
                        f"\nErro: Colunas 'titulo' e/ou 'preco' não encontradas em {os.path.basename(file_path)}. "
                        f"Colunas disponíveis: {list(df_store.columns)}"
                    )
                    continue

                df_store.rename(
                    columns={nome_col: "titulo", preco_col: "preco"}, inplace=True
                )

            df_processed = df_store[["titulo", "preco"]].copy()
            df_processed["Loja"] = nome_loja

            if df_processed["preco"].dtype == "object":
                df_processed["preco"] = df_processed["preco"].astype(str)
                df_processed["preco"] = df_processed["preco"].str.replace(
                    r"[R$\s]", "", regex=True
                )
                df_processed["preco"] = df_processed["preco"].str.replace(",", ".", regex=False)
                df_processed["preco"] = pd.to_numeric(df_processed["preco"], errors="coerce")

            df_processed.dropna(subset=["preco"], inplace=True)

            all_data.append(df_processed)
            print("OK")

        except FileNotFoundError:
            print(f"\nErro: Arquivo não encontrado - {file_path}")
            continue
        except Exception as e:
            print(f"\nOcorreu um erro inesperado ao processar {file_path}: {e}")
            continue

    if not all_data:
        print("\nNenhum dado foi processado com sucesso. Verifique os arquivos CSV e seus formatos.")
        return

    df_combined = pd.concat(all_data, ignore_index=True)
    print("\nDados combinados com sucesso.")
    print(f"Total de registros processados: {len(df_combined)}")
    print(f"Lojas incluídas na análise: {df_combined['Loja'].unique().tolist()}")

    print("\nGerando gráficos Top 10 produtos mais baratos por loja...")
    plt.style.use("seaborn-v0_8-whitegrid")

    for nome_loja in df_combined["Loja"].unique():
        df_store_filtered = df_combined[df_combined["Loja"] == nome_loja].copy()
        top_10_cheapest = df_store_filtered.sort_values(by="preco", ascending=True).head(10)

        if top_10_cheapest.empty:
            print(f"Não há dados suficientes para gerar o gráfico da loja {nome_loja}.")
            continue

        plt.figure(figsize=(12, 7))
        barplot = sns.barplot(
            x="titulo", y="preco", data=top_10_cheapest, palette="viridis"
        )

        plt.title(f"Top 10 Produtos Mais Baratos - {nome_loja}", fontsize=16)
        plt.xlabel("Nome do Produto", fontsize=12)
        plt.ylabel("preco (R$)", fontsize=12)
        plt.xticks(rotation=45, ha="right", fontsize=10)
        plt.yticks(fontsize=10)

        for container in barplot.containers:
            barplot.bar_label(container, fmt="R$ %.2f", fontsize=9, padding=3)

        plt.tight_layout()
        plt.show()
        print(f"Gráfico da loja {nome_loja} gerado.")

    print("\nCalculando a loja mais barata em média...")
    media_por_loja = df_combined.groupby("Loja")["preco"].mean().reset_index()
    loja_mais_barata = media_por_loja.loc[media_por_loja["preco"].idxmin()]

    print("\n--- Loja Mais Barata em Média ---")
    print(
        f"A loja mais barata em média para os produtos analisados é: {loja_mais_barata['Loja']} "
        f"(Preço médio: R$ {loja_mais_barata['preco']:.2f})"
    )
    print("--------------------------------------------------")

    print("\nAnálise concluída.")
