import streamlit as st
import pandas as pd
import dataframe_image as dfi
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import tempfile

def executar():
    st.title("Relatório Diário de AuC por Assessor")

    uploaded_file = st.file_uploader("Faça upload do Excel com os dados", type=["xlsx"])

    # Valor padrão de e-mails dos destinatários vindo do secrets
    destinatarios_padrao = st.secrets["email"]["destinatarios"]
    input_email = st.text_input(
        "E-mail de destino (separar com vírgula para múltiplos)",
        value=", ".join(destinatarios_padrao)
    )

    enviar = st.button("Gerar e Enviar Relatório")

    if uploaded_file and enviar:
        # 1. Ler o arquivo
        df = pd.read_excel(uploaded_file)

        # 2. Agrupar por assessor
        relatorio = df.groupby("Assessor")["PL Total"].sum().reset_index()
        relatorio = relatorio.sort_values(by="PL Total", ascending=False)

        # 3. Adicionar linha TOTAL
        total_geral = relatorio["PL Total"].sum()
        linha_total = pd.DataFrame([{"Assessor": "TOTAL", "PL Total": total_geral}])
        relatorio_com_total = pd.concat([relatorio, linha_total], ignore_index=True)

        # 4. Formatar como moeda
        relatorio_com_total["PL Total"] = relatorio_com_total["PL Total"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

        # 5. Estilo para destacar TOTAL
        def destaque_total(row):
            if row.name == len(relatorio_com_total) - 1:
                return ['font-weight: bold; background-color: #f0f0f0'] * len(row)
            else:
                return [''] * len(row)

        styled = relatorio_com_total.style.apply(destaque_total, axis=1).hide(axis='index')

        # 6. Salvar temporariamente a imagem e a planilha
        data_hoje = datetime.now().strftime('%d-%m-%Y')

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
            dfi.export(styled, img_file.name)
            imagem_path = img_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as excel_file:
            df.to_excel(excel_file.name, index=False)
            planilha_path = excel_file.name

        # 7. Exibir imagem no app
        st.image(imagem_path, caption="Relatório Gerado", use_column_width=True)

        # 8. Botões de download
        with open(imagem_path, "rb") as img_bytes:
            st.download_button("📥 Baixar Imagem", img_bytes, file_name=f"relatorio_auc_{data_hoje}.png")

        with open(planilha_path, "rb") as excel_bytes:
            st.download_button("📥 Baixar Planilha Original", excel_bytes, file_name="planilha_original.xlsx")

        # 9. Envio de e-mail
        destinatarios = [email.strip() for email in input_email.split(",")] if input_email else destinatarios_padrao

        msg = MIMEMultipart()
        msg['Subject'] = f"📊 Relatório Diário de AuC - {data_hoje}"
        msg['From'] = st.secrets["email"]["remetente"]
        msg['To'] = ", ".join(destinatarios)

        corpo_html = f"""
        <h3>Segue abaixo o consolidado diário de AuC por assessor:</h3>
        <p>Data: {data_hoje}</p>
        <img src="cid:relatorio_img">
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        with open(imagem_path, 'rb') as img:
            img_mime = MIMEImage(img.read())
            img_mime.add_header('Content-ID', '<relatorio_img>')
            msg.attach(img_mime)

        with open(planilha_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name="planilha_original.xlsx")
            part['Content-Disposition'] = 'attachment; filename="planilha_original.xlsx"'
            msg.attach(part)

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(
                    st.secrets["email"]["remetente"],
                    st.secrets["email"]["senha_app"]
                )
                server.sendmail(msg['From'], destinatarios, msg.as_string())
            st.success("✅ Relatório enviado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao enviar o e-mail: {e}")
