import streamlit as st
import pandas as pd
import datetime
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Função para formatar como R$ 1.234,56 (sem usar locale) e destacar captação negativa
def formatar_tabela_html(df):
    def destacar_negativos(val):
        return ['background-color: #ffcccc; color: red' if v < 0 else '' for v in val]

    df_estilizado = df.style.format({
        "Captação": lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    }).apply(destacar_negativos, subset=['Captação'], axis=1)

    return df_estilizado.to_html(index=False)

def enviar_email(assunto, corpo_html, anexo, nome_arquivo):
    remetente = st.secrets["email"]["remetente"]
    senha = st.secrets["email"]["senha_app"]
    destinatarios = ["email"]["destinatarios"]

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = assunto

    msg.attach(MIMEText(corpo_html, 'html'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(anexo.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{nome_arquivo}"')
    msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as servidor:
        servidor.login(remetente, senha)
        servidor.send_message(msg)

def executar():
    st.title("Relatório Diário de NNM (D-1)")

    arquivo = st.file_uploader("Faça o upload da planilha .xlsx", type="xlsx")

    if arquivo:
        df = pd.read_excel(arquivo)
        df['Data'] = pd.to_datetime(df['Data'])

        ontem = datetime.datetime.now() - datetime.timedelta(days=1)
        df_filtrado = df[df['Data'].dt.date == ontem.date()]

        colunas_desejadas = ["Conta", "Nome", "Descrição", "Captação", "Data", "Assessor"]
        df_filtrado = df_filtrado[colunas_desejadas].copy()
        df_filtrado['Data'] = pd.to_datetime(df_filtrado['Data']).dt.strftime("%d/%m/%Y")

        st.subheader(f"Dados filtrados para: {ontem.strftime('%d/%m/%Y')}")
        df_display = df_filtrado.copy()
        df_display["Captação"] = df_display["Captação"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
        st.dataframe(df_display)

        if not df_filtrado.empty:
            total_captado = df_filtrado["Captação"].sum()
            valor_formatado = f"R$ {total_captado:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
            corpo_html = f"""
            <p>Segue abaixo o relatório diário de NNM com os dados de {ontem.strftime('%d/%m/%Y')}, o saldo total captado foi de <strong>{valor_formatado}</strong>:</p>
            {formatar_tabela_html(df_filtrado)}
            <p>Qualquer dúvida, fico à disposição.</p>
            """

            assunto = f"Relatório Diário de NNM – {ontem.strftime('%d/%m/%Y')}"

            if st.button("Enviar relatório por e-mail"):
                try:
                    enviar_email(assunto, corpo_html, arquivo, f"Relatorio_NNM_{ontem.strftime('%Y%m%d')}.xlsx")
                    st.success("E-mail enviado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao enviar e-mail: {e}")
        else:
            st.warning("Nenhum dado encontrado para o dia anterior.")
