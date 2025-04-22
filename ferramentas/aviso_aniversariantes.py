import streamlit as st
import pandas as pd
import datetime as dt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Função para enviar e-mail
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

# Função para extrair e formatar o primeiro nome do assessor
def primeiro_nome_formatado(nome_completo):
    if pd.isna(nome_completo):
        return "Assessor"
    primeiro_nome = nome_completo.strip().split()[0]
    return primeiro_nome.capitalize()

# Função para montar o corpo do e-mail individual por assessor
def montar_corpo_email(df_assessor, data_formatada, nome_assessor):
    nome_formatado = primeiro_nome_formatado(nome_assessor)

    if df_assessor.empty:
        return f"<p>Olá {nome_formatado},<br><br>Não há aniversariantes na sua base em {data_formatada}.</p>"

    html = f"<p>Olá {nome_formatado},<br><br>Segue abaixo a lista de aniversariantes do dia {data_formatada}:</p><ul>"
    for _, row in df_assessor.iterrows():
        html += f"<li>{row['Nome']} – Conta: {row['Conta']}</li>"
    html += "</ul><p>Aproveite a oportunidade para reforçar o relacionamento! 🎉</p>"
    return html

# Função principal da ferramenta
def executar():
    st.title("🎉 Aviso de Aniversariantes")
    st.write("Essa ferramenta envia diariamente a lista de aniversariantes para cada assessor.")

    arquivo = st.file_uploader("📁 Faça upload da Base BTG (Excel ou CSV)", type=["xlsx", "csv"])

    if arquivo:
        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)

        # Converter a coluna 'Aniversário'
        df['Aniversário'] = pd.to_datetime(df['Aniversário'], format="%d/%m/%Y", errors='coerce')

        # Filtrar aniversariantes do dia
        hoje = dt.datetime.today()
        df_hoje = df[(df['Aniversário'].dt.day == hoje.day) & (df['Aniversário'].dt.month == hoje.month)]

        if df_hoje.empty:
            st.info("Nenhum aniversariante encontrado para hoje.")
            return

        st.success(f"{len(df_hoje)} aniversariante(s) encontrado(s) para hoje!")
        st.dataframe(df_hoje)

        if st.button("📧 Enviar e-mails de teste para Rafael"):
            data_formatada = hoje.strftime("%d/%m/%Y")
            assessores = df_hoje['Assessor'].unique()
            total_aniversariantes = len(df_hoje)

            # Envio por assessor (simulado para Rafael)
            for assessor in assessores:
                df_assessor = df_hoje[df_hoje['Assessor'] == assessor]
                corpo_html = montar_corpo_email(df_assessor, data_formatada, assessor)
                enviar_email("rafael@convexainvestimentos.com",
                             f"Aniversariantes do dia {data_formatada} – {assessor}",
                             corpo_html)

            # Relatório final consolidado
            tabela_html = df_hoje[['Nome', 'Conta', 'Assessor']].sort_values(by='Assessor').to_html(index=False)

            corpo_relatorio = f"""
            <p>📊 <strong>Relatório Consolidado – Aniversariantes {data_formatada}</strong></p>
            <ul>
                <li><strong>Total de aniversariantes:</strong> {total_aniversariantes}</li>
                <li><strong>Total de assessores envolvidos:</strong> {len(assessores)}</li>
            </ul>
            <p><strong>Lista completa:</strong></p>
            {tabela_html}
            """

            enviar_email("rafael@convexainvestimentos.com",
                         f"📊 Relatório Consolidado – Aniversariantes {data_formatada}",
                         corpo_relatorio)

            st.success(f"✅ E-mails individuais + relatório consolidado enviados para Rafael!")
