import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import io

st.set_page_config(page_title="Vencimentos Semanais", layout="centered")
st.title("📬 Envio de Vencimentos de Renda Fixa")

# Upload dos arquivos
vencimentos_file = st.file_uploader("1. Base de Renda Fixa (com vencimentos)", type=["xlsx"])
btg_file = st.file_uploader("2. Base BTG (conta + assessor)", type=["xlsx"])

if vencimentos_file and btg_file:
    # Carregar dados
    df_venc = pd.read_excel(vencimentos_file, parse_dates=["Vencimento"])
    df_btg = pd.read_excel(btg_file)

    # Renomear colunas da base BTG para merge
    df_btg = df_btg.rename(columns={"Nome": "Nome Cliente"})

    # Merge com base BTG
    df_merged = df_venc.merge(df_btg[["Conta", "Assessor"]], on="Conta", how="left")

    # Mapeamento de e-mails via st.secrets
    emails_assessores = st.secrets["emails_assessores"]
    df_merged["Email Assessor"] = df_merged["Assessor"].map(emails_assessores)

    # Filtro por vencimentos da semana atual
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())  # segunda-feira
    fim_semana = inicio_semana + timedelta(days=6)         # domingo

    df_semana = df_merged[
        (df_merged["Vencimento"] >= inicio_semana) &
        (df_merged["Vencimento"] <= fim_semana)
    ]

    # Seleção e renomeação de colunas
    df_semana = df_semana[[
        "Conta", "Nome", "Emissor", "Produto", "Vencimento",
        "Valor Líquido - Curva Cliente", "Assessor", "Email Assessor"
    ]].rename(columns={
        "Nome": "Cliente",
        "Valor Líquido - Curva Cliente": "Valor Líquido"
    })

    st.success(f"✅ {len(df_semana)} ativos com vencimento nesta semana foram identificados.")

    if st.button("📧 Enviar e-mails aos assessores"):
        email_remetente = st.secrets["EMAIL_REMETENTE"]
        senha_app = st.secrets["SENHA_APP"]

        enviados = 0
        for assessor, grupo in df_semana.groupby("Assessor"):
            email_destino = grupo["Email Assessor"].iloc[0]
            if pd.isna(email_destino):
                st.warning(f"Assessor {assessor} sem e-mail definido.")
                continue

            corpo_html = f"""
            <p>Olá, {assessor}!</p>
            <p>Seguem abaixo os ativos de renda fixa dos seus clientes com vencimento nesta semana:</p>
            {grupo.drop(columns=['Assessor', 'Email Assessor']).to_html(index=False)}
            <p>Abraços,<br>Equipe Convexa</p>
            """

            output = io.BytesIO()
            grupo.drop(columns=["Email Assessor"]).to_excel(output, index=False)
            output.seek()

