import streamlit as st

# Inicializa o menu ativo se não existir
if "menu" not in st.session_state:
    st.session_state.menu = "Ferramenta 1"

# Botões de menu
if st.sidebar.button("Ferramenta 1"):
    st.session_state.menu = "Ferramenta 1"

if st.sidebar.button("Ferramenta 2"):
    st.session_state.menu = "Ferramenta 2"

if st.sidebar.button("Ferramenta 3"):
    st.session_state.menu = "Ferramenta 3"

# Conteúdo da página principal
st.title("Meu Web App")

if st.session_state.menu == "Ferramenta 1":
    st.header("Ferramenta 1")
    st.write("Conteúdo da ferramenta 1 aqui.")

elif st.session_state.menu == "Ferramenta 2":
    st.header("Ferramenta 2")
    st.write("Conteúdo da ferramenta 2 aqui.")

elif st.session_state.menu == "Ferramenta 3":
    st.header("Ferramenta 3")
    st.write("Conteúdo da ferramenta 3 aqui.")

