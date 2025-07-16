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
    st.title("💸 Envio de Fluxo Financeiro (Modo Teste)")

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

        # Mostrar dados processados
        st.subheader("📊 Dados Processados")
        st.dataframe(df_merged.round(2), use_container_width=True)

        st.success(f"✅ {df_merged.shape[0]} clientes processados com sucesso.")

        if st.button("📧 Enviar e-mail de teste para Rafael"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            try:
                # Gerar HTML com toda a tabela consolidada
                html_tabela = (
                    df_merged
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
                <p>Olá Rafael,</p>
                <p>Segue abaixo o fluxo financeiro consolidado (E-MAIL DE TESTE):</p>
                {html_tabela}
                <p>Abraços,<br>Ferramenta Automatizada</p>
                """

                # Gerar anexo Excel
                output = io.BytesIO()
                df_merged.to_excel(output, index=False)
                output.seek(0)

                # Montar e-mail
                msg = MIMEMultipart()
                msg["From"] = formataddr(("Backoffice Convexa", email_remetente))
                msg["To"] = "rafael@convexainvestimentos.com"
                msg["Subject"] = "📩 [TESTE] Fluxo Financeiro – Consolidado"

                msg.attach(MIMEText(corpo_html, "html"))
                anexo = MIMEApplication(output.read(), Name="Fluxo_Financeiro_Teste.xlsx")
                anexo["Content-Disposition"] = 'attachment; filename="Fluxo_Financeiro_Teste.xlsx"'
                msg.attach(anexo)

                # Enviar e-mail
                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_remetente, senha_app)
                    smtp.send_message(msg)

                st.success("📨 E-mail de teste enviado para rafael@convexainvestimentos.com.")
            except Exception as e:
                st.error(f"❌ Erro ao enviar o e-mail de teste: {e}")
