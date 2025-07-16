import streamlit as st
import pandas as pd

def executar():
    st.title("📊 Avaliar Clientes Novos e Excluídos")
    st.write("Compare a Base BTG de ontem e hoje para identificar clientes novos e excluídos.")

    coluna_chave = "Conta"  # ✅ Corrigido: usa a coluna "Conta"

    # Upload dos arquivos
    arquivo_ontem = st.file_uploader("📂 Base BTG - Ontem", type=["csv", "xlsx"], key="ontem")
    arquivo_hoje = st.file_uploader("📂 Base BTG - Hoje", type=["csv", "xlsx"], key="hoje")

    if arquivo_ontem and arquivo_hoje:
        try:
            # Ler os arquivos
            if arquivo_ontem.name.endswith("xlsx"):
                df_ontem = pd.read_excel(arquivo_ontem)
            else:
                df_ontem = pd.read_csv(arquivo_ontem)

            if arquivo_hoje.name.endswith("xlsx"):
                df_hoje = pd.read_excel(arquivo_hoje)
            else:
                df_hoje = pd.read_csv(arquivo_hoje)

            # Verificar se a coluna existe
            if coluna_chave not in df_ontem.columns or coluna_chave not in df_hoje.columns:
                st.error(f"❌ A coluna '{coluna_chave}' não foi encontrada nos arquivos.")
                return

            # Limpeza da coluna Conta
            def limpar_coluna(df):
                df = df.copy()
                df[coluna_chave] = (
                    df[coluna_chave]
                    .astype(str)  # transforma em string
                    .str.strip()  # remove espaços
                    .str.replace(".", "", regex=False)  # remove pontos
                    .str.replace(",", "", regex=False)  # remove vírgulas
                )
                # Remove linhas com valores nulos ou filtros
                df = df[df[coluna_chave].notna()]
                df = df[~df[coluna_chave].str.lower().str.contains("applied filter")]
                return df

            df_ontem = limpar_coluna(df_ontem)
            df_hoje = limpar_coluna(df_hoje)

            # Mostrar prévia para validação
            st.subheader("🔍 Prévia da coluna analisada")
            st.write("Base Ontem:")
            st.dataframe(df_ontem[[coluna_chave]].head(), use_container_width=True)
            st.write("Base Hoje:")
            st.dataframe(df_hoje[[coluna_chave]].head(), use_container_width=True)

            # Contas totais
            total_ontem = df_ontem[coluna_chave].nunique()
            total_hoje = df_hoje[coluna_chave].nunique()

            st.metric("👥 Total de Contas Ontem", total_ontem)
            st.metric("👥 Total de Contas Hoje", total_hoje)

            # Comparação
            clientes_ontem = set(df_ontem[coluna_chave])
            clientes_hoje = set(df_hoje[coluna_chave])

            novos = clientes_hoje - clientes_ontem
            excluidos = clientes_ontem - clientes_hoje

            # Mostrar resultados
            st.subheader(f"✅ Clientes Novos ({len(novos)})")
            df_novos = df_hoje[df_hoje[coluna_chave].isin(novos)]
            st.dataframe(df_novos, use_container_width=True)

            st.download_button(
                "📥 Baixar lista de novos (CSV)",
                df_novos.to_csv(index=False).encode("utf-8"),
                "clientes_novos.csv",
                "text/csv"
            )

            st.subheader(f"⚠️ Clientes Excluídos ({len(excluidos)})")
            df_excluidos = df_ontem[df_ontem[coluna_chave].isin(excluidos)]
            st.dataframe(df_excluidos, use_container_width=True)

            st.download_button(
                "📥 Baixar lista de excluídos (CSV)",
                df_excluidos.to_csv(index=False).encode("utf-8"),
                "clientes_excluidos.csv",
                "text/csv"
            )

        except Exception as e:
            st.error(f"Erro ao processar os arquivos: {e}")
