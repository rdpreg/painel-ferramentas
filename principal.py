import streamlit as st
from ferramentas import relatorio_diario
from ferramentas import aviso_rf

# Inicializa o menu padrão
if "menu" not in st.session_state:
    st.session_state.menu = "home"

st.sidebar.title("Menu")

if st.sidebar.button("Relatório diário de AuC"):
    st.session_state.menu = "relatorio"

if st.sidebar.button("Aviso de Vencimentos RF"):
    st.session_state.menu = "vencimentos"

if st.sidebar.button("Ferramenta 3"):
    st.session_state.menu = "ferramenta3"

# TELA PRINCIPAL
if st.session_state.menu == "relatorio":
    relatorio_diario.executar()

elif st.session_state.menu == "vencimentos":
    aviso_rf.executar()

elif st.session_state.menu == "ferramenta3":
    st.title("Ferramenta 3")
    # conteúdo da ferramenta

else:
    st.title("Bem-vindo(a) à área de relatórios")
    st.write("Escolha uma ferramenta no menu lateral para começar.")
