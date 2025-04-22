import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
import io

def executar():
    st.title("📬 Envio de Vencimentos de Renda Fixa")

    vencimentos_file = st.file_uploader("1. Base de Renda Fixa (com vencimentos)", type=["xlsx"])
    btg_file = st.file_uploader("2. Base BTG (conta + assessor)", type=["xlsx"])

    if vencimentos_file and btg_file:
        df_venc = pd.read_excel(vencimentos_file, parse_dates=["Vencimento"])
        df_btg = pd.read_excel(btg_file)
        df_btg = df_btg.rename(columns={"Nome": "Nome Cliente"})

        df_merged = df_venc.merge(df_btg[["Conta", "Assessor"]], on="Conta", how="left")
        emails_assessores = st.secrets["emails_assessores"]
        df_merged["Email Assessor"] = df_merged["Assessor"].map(emails_assessores)

        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)

        df_semana = df_merged[
            (df_merged["Vencimento"] >= inicio_semana) &
            (df_merged["Vencimento"] <= fim_semana)
        ]

        df_semana = df_semana[[
            "Conta", "Nome", "Emissor", "Produto", "Vencimento",
            "Valor Líquido - Curva Cliente", "Assessor", "Email Assessor"
        ]].rename(columns={
            "Nome": "Cliente",
            "Valor Líquido - Curva Cliente": "Valor Líquido"
        })

        st.success(f"✅ {len(df_semana)} ativos com vencimento nesta semana foram identificados.")

        if st.button("📧 Enviar e-mails aos assessores"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            enviados = 0

            for assessor, grupo in df_semana.groupby("Assessor"):
                email_destino = grupo["Email Assessor"].iloc[0]
                if pd.isna(email_destino):
                    st.warning(f"Assessor {assessor} sem e-mail definido.")
                    continue

                primeiro_nome = assessor.strip().split()[0].capitalize()

                html_tabela = (
                    grupo.drop(columns=["Assessor", "Email Assessor"])
                    .reset_index(drop=True)
                    .style
                    .format({
                        "Valor Líquido": "R$ {:,.2f}",
                        "Vencimento": lambda x: x.strftime("%d/%m/%Y")
                    })
                    .to_html()
                )

                corpo_html = f"""
                <p>Olá, {primeiro_nome}!</p>
                <p>Seguem abaixo os ativos de renda fixa dos seus clientes com vencimento nesta semana:</p>
                {html_tabela}
                <p>Abraços,<br>Equipe Convexa</p>
                """

                output = io.BytesIO()
                grupo.drop(columns=["Email Assessor"]).to_excel(output, index=False)
                output.seek(0)

                msg = MIMEMultipart()
                msg["From"] = email_remetente
                msg["To"] = email_destino
                msg["Subject"] = "📩 Atenção Assessor: Ativos de Renda Fixa a vencer nesta semana"
                msg.attach(MIMEText(corpo_html, "html"))

                anexo = MIMEApplication(output.read(), Name="Vencimentos_da_Semana.xlsx")
                anexo["Content-Disposition"] = 'attachment; filename="Vencimentos_da_Semana.xlsx"'
                msg.attach(anexo)

                try:
                    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                        smtp.starttls()
                        smtp.login(email_remetente, senha_app)
                        smtp.send_message(msg)
                    enviados += 1
                except Exception as e:
                    st.error(f"Erro ao enviar para {assessor}: {e}")

            # Enviar relatório consolidado para Rafael
            df_envios = df_semana[["Assessor", "Valor Líquido"]].copy()
            df_envios = df_envios.dropna(subset=["Valor Líquido"])
            df_envios["Valor Líquido"] = pd.to_numeric(df_envios["Valor Líquido"], errors="coerce")

            df_resumo = df_envios.groupby("Assessor").sum().sort_values("Valor Líquido", ascending=False)
            valor_total = df_envios["Valor Líquido"].sum()
            quantidade_assessores = df_resumo.shape[0]

            linhas_html = "".join([
                f"<li>{assessor}: R$ {valor:,.2f}</li>"
                for assessor, valor in df_resumo["Valor Líquido"].items()
            ])

            corpo_resumo = f"""
            <p><strong>Relatório Consolidado – Vencimentos da Semana</strong></p>
            <p>💰 <strong>Valor total a vencer:</strong> R$ {valor_total:,.2f}<br>
            👤 <strong>Assessores notificados:</strong> {quantidade_assessores}<br>
            📧 <strong>E-mails enviados com sucesso:</strong> {enviados}</p>
            <p><strong>🧮 Valores por assessor:</strong></p>
            <ul>{linhas_html}</ul>
            <p>Abraços,<br>Ferramenta Automatizada</p>
            """

            msg_resumo = MIMEMultipart()
            msg_resumo["From"] = email_remetente
            msg_resumo["To"] = "rafael@convexainvestimentos.com"
            msg_resumo["Subject"] = "📊 Relatório Consolidado – Vencimentos da Semana"
            msg_resumo.attach(MIMEText(corpo_resumo, "html"))

            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_remetente, senha_app)
                    smtp.send_message(msg_resumo)
                st.info("📨 Relatório consolidado enviado para rafael@convexainvestimentos.com.")
            except Exception as e:
                st.error(f"Erro ao enviar o relatório consolidado: {e}")
