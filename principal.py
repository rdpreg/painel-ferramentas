import streamlit as st
from ferramentas import relatorio_diario
from ferramentas import aviso_rf
from ferramentas import nnm_diario, painel_rotinas, aviso_aniversariantes, relatorio_cc, check_exclusao_base

# Inicializa o menu padrão
if "menu" not in st.session_state:
    st.session_state.menu = "home"

st.sidebar.title("Menu")

if st.sidebar.button("Painel de Rotinas"):
    st.session_state.menu = "rotinas"

if st.sidebar.button("Relatório diário de AuC"):
    st.session_state.menu = "relatorio"

if st.sidebar.button("Aviso de Vencimentos RF"):
    st.session_state.menu = "vencimentos"

if st.sidebar.button("Relatório Diário NNM (D-1)"):
    st.session_state.menu = "nnm_diario"

if st.sidebar.button("Aviso de Aniversariantes"):
    st.session_state.menu = "aniversariantes"

if st.sidebar.button("Relatório de Conta-Corrente"):
    st.session_state.menu = "relatorio_cc"

if st.sidebar.button("Check Base de Clientes"):
    st.session_state.menu = "check_exclusao_base"


# TELA PRINCIPAL
if st.session_state.menu == "rotinas":
    painel_rotinas.executar()

elif st.session_state.menu == "relatorio":
    relatorio_diario.executar()

elif st.session_state.menu == "vencimentos":
    aviso_rf.executar()

elif st.session_state.menu == "nnm_diario":
    nnm_diario.executar()

elif st.session_state.menu == "aniversariantes":
    aviso_aniversariantes.executar()

elif st.session_state.menu == "relatorio_cc":
    relatorio_cc.executar()

elif st.session_state.menu == "check_exclusao_base":
    check_exclusao_base.executar()



else:
    st.title("Bem-vindo(a) à área de relatórios")
    st.write("Escolha uma ferramenta no menu lateral para começar.")
