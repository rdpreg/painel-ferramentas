import streamlit as st
import pandas as pd
import datetime as dt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def enviar_email(destinatario, assunto, corpo_html):
    email_remetente = st.secrets["email"]["remetente"]
    senha_app = st.secrets["email"]["senha_app"]

    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_html, 'html'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(email_remetente, senha_app)
        server.send_message(msg)

def montar_corpo_email(df, data_formatada):
    if df.empty:
        return f"<p>Não há aniversariantes em {data_formatada}.</p>"

    html = f"<p>Segue abaixo a lista de aniversariantes do dia {data_formatada}:</p><ul>"
    for _, row in df.iterrows():
        html += f"<li><strong>{row['Nome']}</strong> – Conta: {row['Conta']} (Assessor: {row['Assessor']})</li>"
    html += "</ul><p>Aproveite a oportunidade para reforçar o relacionamento! 🎉</p>"
    return html

def executar():
    st.header("🎉 Aviso de Aniversariantes")

    arquivo = st.file_uploader("Faça upload da Base BTG (Excel ou CSV)", type=["xlsx", "csv"])

    if arquivo:
        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)

        df['Aniversário'] = pd.to_datetime(df['Aniversário'], format="%d/%m/%Y", errors='coerce')
        hoje = dt.datetime.today()
        df_hoje = df[(df['Aniversário'].dt.day == hoje.day) & (df['Aniversário'].dt.month == hoje.month)]

        if df_hoje.empty:
            st.info("Nenhum aniversariante encontrado para hoje.")
            return

        st.success(f"{len(df_hoje)} aniversariante(s) encontrado(s) para hoje!")

        if st.button("📧 Enviar e-mail de teste"):
            data_formatada = hoje.strftime("%d/%m/%Y")
            corpo_html = montar_corpo_email(df_hoje, data_formatada)
            enviar_email("rafael@convexainvestimentos.com", f"Aniversariantes do dia {data_formatada}", corpo_html)
            st.success("E-mail de teste enviado para rafael@convexainvestimentos.com!")

