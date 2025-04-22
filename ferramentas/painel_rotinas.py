import streamlit as st
from datetime import datetime

def executar():
    st.title("📋 Painel de Rotinas Diárias")
    st.markdown(f"Data: **{datetime.now().strftime('%d/%m/%Y')}**")

    # Inicializa session_state
    if "rotinas" not in st.session_state:
        st.session_state["rotinas"] = {
            "manhã": {
                "Relatório diário de AuC": {"feito": False, "hora": ""},
                "Aviso de Vencimentos RF": {"feito": False, "hora": ""}
            },
            "tarde": {
                "Relatório Diário NNM (D-1)": {"feito": False, "hora": ""}
            },
            "livre": {
                "Aviso de Aniversariantes": {"feito": False, "hora": ""}
            }
        }

    def exibir_bloco(nome_bloco, tarefas):
        st.subheader(f"🕒 {nome_bloco.capitalize()}")
        for tarefa, info in tarefas.items():
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                checked = st.checkbox("", value=info["feito"], key=tarefa)
            with col2:
                if checked and not info["feito"]:
                    st.session_state["rotinas"][nome_bloco][tarefa]["feito"] = True
                    st.session_state["rotinas"][nome_bloco][tarefa]["hora"] = datetime.now().strftime("%H:%M")
                elif not checked:
                    st.session_state["rotinas"][nome_bloco][tarefa]["feito"] = False
                    st.session_state["rotinas"][nome_bloco][tarefa]["hora"] = ""

                hora = st.session_state["rotinas"][nome_bloco][tarefa]["hora"]
                status = f"✅ Enviado às {hora}" if checked else "⏳ Pendente"
                st.markdown(f"**{tarefa}**  \n→ _Status_: {status}")

    # Exibe todos os blocos
    exibir_bloco("manhã", st.session_state["rotinas"]["manhã"])
    exibir_bloco("tarde", st.session_state["rotinas"]["tarde"])
    exibir_bloco("livre", st.session_state["rotinas"]["livre"])
