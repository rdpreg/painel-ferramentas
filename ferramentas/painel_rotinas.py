import streamlit as st
from datetime import datetime
import pytz

def executar():
    st.title("📋 Painel de Rotinas Diárias")

    # Hora atual com fuso de Brasília
    fuso_brasilia = pytz.timezone("America/Sao_Paulo")
    agora = datetime.now(fuso_brasilia)
    dia_semana = agora.strftime("%A").lower()  # segunda, terça, etc
    st.markdown(f"Data: **{agora.strftime('%d/%m/%Y')} ({dia_semana.capitalize()})**")

    # Tarefas fixas de segunda a sexta
    dias_da_semana = ["segunda", "terça", "quarta", "quinta", "sexta"]
    tarefas_manha = {
        "Relatório Conta Corrente": {"feito": False, "hora": ""},
        "Relatório Base de Clientes": {"feito": False, "hora": ""},
        "Relatório Diário Geral": {"feito": False, "hora": ""},
        "Aviso de Aniversariantes": {"feito": False, "hora": ""}
    }
    tarefas_tarde = {
        "Relatório Diário de AuC": {"feito": False, "hora": ""}
    }

    # Inicializa session_state com rotina da semana
    if "rotinas" not in st.session_state:
        st.session_state["rotinas"] = {}
        for dia in dias_da_semana:
            st.session_state["rotinas"][dia] = {
                "manhã": tarefas_manha.copy(),
                "tarde": tarefas_tarde.copy(),
                "livre": {}
            }

    # Se for fim de semana, mostrar mensagem
    if dia_semana not in dias_da_semana:
        st.warning("Hoje não há rotina definida (fim de semana).")
        return

    tarefas_do_dia = st.session_state["rotinas"][dia_semana]

    def exibir_bloco(nome_bloco, tarefas):
        st.subheader(f"🕒 {nome_bloco.capitalize()}")
        for tarefa, info in tarefas.items():
            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                checked = st.checkbox("", value=info["feito"], key=f"{dia_semana}-{nome_bloco}-{tarefa}")
            with col2:
                if checked and not info["feito"]:
                    st.session_state["rotinas"][dia_semana][nome_bloco][tarefa]["feito"] = True
                    st.session_state["rotinas"][dia_semana][nome_bloco][tarefa]["hora"] = datetime.now(
                        pytz.timezone("America/Sao_Paulo")
                    ).strftime("%H:%M")
                elif not checked:
                    st.session_state["rotinas"][dia_semana][nome_bloco][tarefa]["feito"] = False
                    st.session_state["rotinas"][dia_semana][nome_bloco][tarefa]["hora"] = ""

                hora = st.session_state["rotinas"][dia_semana][nome_bloco][tarefa]["hora"]
                status = f"✅ Concluído às {hora}" if checked else "⏳ Pendente"
                st.markdown(f"**{tarefa}**  \n→ _Status_: {status}")

    # Exibe os blocos do dia atual
    for bloco in ["manhã", "tarde", "livre"]:
        if tarefas_do_dia[bloco]:
            exibir_bloco(bloco, tarefas_do_dia[bloco])
