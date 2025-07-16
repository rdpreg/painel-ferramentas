import streamlit as st
import pandas as pd

def executar():
    st.title("📊 Avaliar Clientes Novos e Excluídos")
    st.write("Compare a Base BTG de ontem e hoje para identificar clientes novos e excluídos.")

    # Nome fixo da coluna para comparar
    coluna_chave = "Conta Corrente"

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

            # Verificar se a coluna existe nos dois arquivos
            if coluna_chave not in df_ontem.columns or coluna_chave not in df_hoje.columns:
                st.error(f"❌ A coluna '{coluna_chave}' não foi encontrada em um ou ambos os arquivos.")
                return

            # Contas totais
            total_ontem = df_ontem[coluna_chave].nunique()
            total_hoje = df_hoje[coluna_chave].nunique()

            st.metric("👥 Total de Contas Ontem", total_ontem)
            st.metric("👥 Total de Contas Hoje", total_hoje)

            # Identificar novos e excluídos
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
