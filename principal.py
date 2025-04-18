import streamlit as st

# Inicializa o menu ativo se não existir
if "menu" not in st.session_state:
    st.session_state.menu = "Relatório diário de PL"

# Botões de menu
if st.sidebar.button("Relatório diário de PL"):
    st.session_state.menu = "Relatório diário de PL"

if st.sidebar.button("Ferramenta 2"):
    st.session_state.menu = "Ferramenta 2"

if st.sidebar.button("Ferramenta 3"):
    st.session_state.menu = "Ferramenta 3"

# Conteúdo da página principal
st.title("Bem-vindo(a) a área de relatórios")

if st.session_state.menu == "Ferramenta 1":
    st.header("Ferramenta 1")
    st.write("Conteúdo da ferramenta 1 aqui.")

elif st.session_state.menu == "Ferramenta 2":
    st.header("Ferramenta 2")
    st.write("Conteúdo da ferramenta 2 aqui.")

elif st.session_state.menu == "Ferramenta 3":
    st.header("Ferramenta 3")
    st.write("Conteúdo da ferramenta 3 aqui.")

