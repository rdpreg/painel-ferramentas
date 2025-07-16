import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formataddr
import io

def executar():
    st.title("💸 Envio de Fluxo Financeiro por Assessor")

    st.write("📂 Faça o upload dos arquivos necessários:")
    btg_file = st.file_uploader("1️⃣ Base BTG (conta + assessor)", type=["xlsx"])
    saldo_file = st.file_uploader("2️⃣ Saldo D0 + Valores a Receber Projetados (RF + VT)", type=["xlsx"])

    if btg_file and saldo_file:
        # Carregar bases
        df_btg = pd.read_excel(btg_file)
        df_saldo = pd.read_excel(saldo_file)

        # Padronizar colunas
        df_btg = df_btg.rename(columns={"Conta": "Conta Cliente", "Nome": "Nome Cliente"})
        df_saldo = df_saldo.rename(columns={"Conta": "Conta Cliente", "Saldo": "Saldo CC"})

        # Mesclar dados
        df_merged = df_btg.merge(df_saldo, on="Conta Cliente", how="left")

        # Preencher valores nulos com 0
        df_merged.fillna(0, inplace=True)

        # Calcular colunas de saldo total por dia
        df_merged["Saldo + D+1"] = df_merged["Saldo CC"] + df_merged["D+1"]
        df_merged["Saldo + D+2"] = df_merged["Saldo + D+1"] + df_merged["D+2"]
        df_merged["Saldo + D+3"] = df_merged["Saldo + D+2"] + df_merged["D+3"]

        # Mapear e-mails dos assessores
        emails_assessores = st.secrets["emails_assessores"]
        df_merged["Email Assessor"] = df_merged["Assessor"].map(emails_assessores)

        st.success(f"✅ {df_merged.shape[0]} clientes processados com sucesso.")

        if st.button("📧 Enviar e-mails aos assessores"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            enviados = 0

            for assessor, grupo in df_merged.groupby("Assessor"):
                email_destino = grupo["Email Assessor"].iloc[0]
                primeiro_nome = assessor.strip().split()[0].capitalize()

                if pd.isna(email_destino):
                    st.warning(f"Assessor {assessor} sem e-mail definido.")
                    continue

                # Montar HTML com a tabela
                html_tabela = (
                    grupo.drop(columns=["Assessor", "Email Assessor"])
                    .reset_index(drop=True)
                    .style
                    .format({
                        "Saldo CC": "R$ {:,.2f}",
                        "D+1": "R$ {:,.2f}",
                        "D+2": "R$ {:,.2f}",
                        "D+3": "R$ {:,.2f}",
                        "Saldo + D+1": "R$ {:,.2f}",
                        "Saldo + D+2": "R$ {:,.2f}",
                        "Saldo + D+3": "R$ {:,.2f}"
                    })
                    .to_html()
                )

                corpo_html = f"""
                <p>Olá, {primeiro_nome}!</p>
                <p>Segue abaixo o fluxo financeiro consolidado dos seus clientes:</p>
                {html_tabela}
                <p>Abraços,<br>Equipe Convexa</p>
                """

                # Gerar anexo Excel
                output = io.BytesIO()
                grupo.drop(columns=["Email Assessor"]).to_excel(output, index=False)
                output.seek(0)

                # Montar e-mail
                msg = MIMEMultipart()
                msg["From"] = formataddr(("Backoffice Convexa", email_remetente))
                msg["To"] = email_destino
                msg["Subject"] = "📩 Fluxo Financeiro – Clientes"

                msg.attach(MIMEText(corpo_html, "html"))
                anexo = MIMEApplication(output.read(), Name="Fluxo_Financeiro.xlsx")
                anexo["Content-Disposition"] = 'attachment; filename="Fluxo_Financeiro.xlsx"'
                msg.attach(anexo)

                try:
                    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                        smtp.starttls()
                        smtp.login(email_remetente, senha_app)
                        smtp.send_message(msg)
                    enviados += 1
                except Exception as e:
                    st.error(f"Erro ao enviar para {assessor}: {e}")

            # Resumo consolidado para Rafael
            total_saldo = df_merged["Saldo CC"].sum()
            total_fluxo = df_merged[["D+1", "D+2", "D+3"]].sum().sum()

            corpo_resumo = f"""
            <p><strong>📊 Relatório Consolidado – Fluxo Financeiro</strong></p>
            <p>💰 <strong>Saldo Total em Conta:</strong> R$ {total_saldo:,.2f}<br>
            🔄 <strong>Total de Fluxos D+1, D+2, D+3:</strong> R$ {total_fluxo:,.2f}<br>
            📧 <strong>E-mails enviados com sucesso:</strong> {enviados}</p>
            <p>Abraços,<br>Ferramenta Automatizada</p>
            """

            msg_resumo = MIMEMultipart()
            msg_resumo["From"] = email_remetente
            msg_resumo["To"] = "rafael@convexainvestimentos.com"
            msg_resumo["Subject"] = "📊 Relatório Consolidado – Fluxo Financeiro"
            msg_resumo.attach(MIMEText(corpo_resumo, "html"))

            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_remetente, senha_app)
                    smtp.send_message(msg_resumo)
                st.info("📨 Relatório consolidado enviado para rafael@convexainvestimentos.com.")
            except Exception as e:
                st.error(f"Erro ao enviar o relatório consolidado: {e}")
