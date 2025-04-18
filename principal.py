import streamlit as st
# Sidebar de navegação
st.sidebar.title("Menu")
menu = st.sidebar.radio("Escolha uma ferramenta:", ["Ferramenta 1", "Ferramenta 2", "Ferramenta 3"])

# Conteúdo da página principal
st.title("Meu Web App")

if menu == "Ferramenta 1":
    st.header("Ferramenta 1")
    # lógica e interações da ferramenta 1 aqui

elif menu == "Ferramenta 2":
    st.header("Ferramenta 2")
    # lógica da ferramenta 2

elif menu == "Ferramenta 3":
    st.header("Ferramenta 3")
    # lógica da ferramenta 3
