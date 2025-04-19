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
        # 1. Carregar os dados
        df_venc = pd.read_excel(vencimentos_file, parse_dates=["Vencimento"])
        df_btg = pd.read_excel(btg_file)
        df_btg = df_btg.rename(columns={"Nome": "Nome Cliente"})

        # 2. Cruzar com base BTG
        df_merged = df_venc.merge(df_btg[["Conta", "Assessor"]], on="Conta", how="left")

        # 3. Mapear e-mails dos assessores via secrets
        emails_assessores = st.secrets["emails_assessores"]
        df_merged["Email Assessor"] = df_merged["Assessor"].map(emails_assessores)

        # 4. Filtrar vencimentos da semana atual
        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=hoje.weekday())  # segunda
        fim_semana = inicio_semana + timedelta(days=6)         # domingo

        df_semana = df_merged[
            (df_merged["Vencimento"] >= inicio_semana) &
            (df_merged["Vencimento"] <= fim_semana)
        ]

        # 5. Selecionar e renomear colunas
        df_semana = df_semana[[
            "Conta", "Nome", "Emissor", "Produto", "Vencimento",
            "Valor Líquido - Curva Cliente", "Assessor", "Email Assessor"
        ]].rename(columns={
            "Nome": "Cliente",
            "Valor Líquido - Curva Cliente": "Valor Líquido"
        })

        st.success(f"✅ {len(df_semana)} ativos com vencimento nesta semana foram identificados.")

        # 6. Enviar os e-mails por assessor
        if st.button("📧 Enviar e-mails aos assessores"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            enviados = 0
            for assessor, grupo in df_semana.groupby("Assessor"):
                email_destino = grupo["Email Assessor"].iloc[0]
                if pd.isna(email_destino):
                    st.warning(f"Assessor {assessor} sem e-mail definido.")
                    continue

                # 7. Gerar tabela HTML formatada
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

                # 8. Montar corpo do e-mail
                primeiro_nome = assessor.strip().split()[0].capitalize()
                corpo_html = f"""
                <p>Olá, {primeiro_nome}!</p>
                <p>Seguem abaixo os ativos de renda fixa dos seus clientes com vencimento nesta semana:</p>
                {html_tabela}
                <p>Abraços,<br>Equipe Convexa Investimentos</p>
                """

                # 9. Criar anexo Excel em memória
                output = io.BytesIO()
                grupo.drop(columns=["Email Assessor"]).to_excel(output, index=False)
                output.seek(0)

                # 10. Montar e enviar o e-mail
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

            st.success(f"✅ E-mails enviados com sucesso para {enviados} assessores.")
