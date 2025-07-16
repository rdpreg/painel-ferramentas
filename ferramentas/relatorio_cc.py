import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formataddr
import io

def formatar_brasileiro(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

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

        # Calcular coluna Saldo Projetado
        df_merged["Saldo Projetado"] = (
            df_merged["Saldo CC"] +
            df_merged["D+1"] +
            df_merged["D+2"] +
            df_merged["D+3"]
        )

        # 🔥 Filtrar clientes com Saldo Projetado diferente de zero
        df_final = df_merged[
            df_merged["Saldo Projetado"] != 0
        ][[
            "Conta Cliente", "Nome Cliente", "Assessor",
            "Saldo CC", "D+1", "D+2", "D+3", "Saldo Projetado"
        ]]

        # Formatar valores para BR
        df_formatado = df_final.copy()
        for col in ["Saldo CC", "D+1", "D+2", "D+3", "Saldo Projetado"]:
            df_formatado[col] = df_formatado[col].apply(formatar_brasileiro)

        # Mostrar dados processados
        st.subheader("📊 Dados Processados (Saldo Projetado ≠ 0)")
        st.dataframe(df_formatado, use_container_width=True)

        st.success(f"✅ {df_final.shape[0]} clientes com Saldo Projetado ≠ 0 processados com sucesso.")

        if st.button("📧 Enviar e-mail de teste para Rafael"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            try:
                # Gerar HTML com a tabela final (formatada BR)
                html_tabela = (
                    df_final
                    .reset_index(drop=True)
                    .style
                    .format({
                        "Saldo CC": lambda x: formatar_brasileiro(x),
                        "D+1": lambda x: formatar_brasileiro(x),
                        "D+2": lambda x: formatar_brasileiro(x),
                        "D+3": lambda x: formatar_brasileiro(x),
                        "Saldo Projetado": lambda x: formatar_brasileiro(x)
                    })
                    .to_html()
                )

                corpo_html = f"""
                <p>Olá Rafael,</p>
                <p>Segue abaixo o fluxo financeiro consolidado (E-MAIL DE TESTE):</p>
                {html_tabela}
                <p>Abraços,<br>Ferramenta Automatizada</p>
                """

                # Gerar anexo Excel com valores numéricos (não formatados)
                output = io.BytesIO()
                df_final.to_excel(output, index=False)
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
