import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.utils import formataddr
import io

# 🔥 Flag para alternar entre teste e produção
modo_teste = False  # True = envia só para Rafael; False = envia para os assessores

def formatar_brasileiro(valor):
    """Formata número no padrão brasileiro com R$"""
    texto = f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    if valor < 0:
        return f"<span style='color: red;'>{texto}</span>"
    return texto

def executar():
    st.title("💸 Envio de Fluxo Financeiro (Produção)")

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

        # Mapear e-mails dos assessores
        emails_assessores = st.secrets["emails_assessores"]
        df_final["Email Assessor"] = df_final["Assessor"].map(emails_assessores)

        # 🖥️ Formatar valores no padrão brasileiro e aplicar cores (para exibir no app)
        df_formatado = df_final.copy()
        for col in ["Saldo CC", "D+1", "D+2", "D+3", "Saldo Projetado"]:
            df_formatado[col] = df_formatado[col].apply(formatar_brasileiro)

        # Exibir tabela com scroll e formatação
        st.subheader("📊 Dados Processados (Saldo Projetado ≠ 0)")
        tabela_html = df_formatado.drop(columns=["Email Assessor"]).to_html(escape=False, index=False)
        tabela_com_scroll = f"""
        <div style="overflow:auto; max-height:500px; border:1px solid #ddd; padding:8px">
            {tabela_html}
        </div>
        """
        st.markdown(tabela_com_scroll, unsafe_allow_html=True)

        st.success(f"✅ {df_final.shape[0]} clientes com Saldo Projetado ≠ 0 processados com sucesso.")

        if st.button("📧 Enviar e-mails aos assessores"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]
            data_hoje = datetime.now().strftime("%d-%m-%Y")

            enviados = 0

            # 🔄 Loop pelos assessores
            for assessor, grupo in df_final.groupby("Assessor"):
                # 🔥 Se modo_teste=True, envia tudo para Rafael
                if modo_teste:
                    email_destino = "rafael@convexainvestimentos.com"
                    primeiro_nome = "Rafael"
                else:
                    email_destino = grupo["Email Assessor"].iloc[0]
                    primeiro_nome = assessor.strip().split()[0].capitalize()

                if pd.isna(email_destino):
                    st.warning(f"⚠️ Assessor {assessor} sem e-mail definido. Pulando envio.")
                    continue

                # 🧮 Resumo consolidado do assessor
                saldo_cc_total = grupo["Saldo CC"].sum()
                saldo_d1_total = grupo["D+1"].sum()
                saldo_d2_total = grupo["D+2"].sum()
                saldo_d3_total = grupo["D+3"].sum()

                resumo_html = f"""
                <p>Olá {primeiro_nome},</p>
                <p>Aqui estão os dados de Saldo em Conta consolidados. O relatório detalhado está em anexo.</p>
                <ul>
                    <li><strong>Saldo em Conta:</strong> {formatar_brasileiro(saldo_cc_total)}</li>
                    <li><strong>Saldo a entrar em D+1:</strong> {formatar_brasileiro(saldo_d1_total)}</li>
                    <li><strong>Saldo a entrar em D+2:</strong> {formatar_brasileiro(saldo_d2_total)}</li>
                    <li><strong>Saldo a entrar em D+3:</strong> {formatar_brasileiro(saldo_d3_total)}</li>
                </ul>
                <p>Abraços,<br>Equipe Convexa</p>
                """

                # Gerar anexo Excel com números puros
                output = io.BytesIO()
                grupo.drop(columns=["Email Assessor"]).to_excel(output, index=False)
                output.seek(0)

                # 📎 Nome do arquivo com data
                nome_arquivo = f"Saldo_em_Conta_{data_hoje}.xlsx"

                # Montar e-mail
                msg = MIMEMultipart()
                msg["From"] = formataddr(("Backoffice Convexa", email_remetente))
                msg["To"] = email_destino
                msg["Subject"] = f"📩 Fluxo Financeiro – {data_hoje}"

                msg.attach(MIMEText(resumo_html, "html"))
                anexo = MIMEApplication(output.read(), Name=nome_arquivo)
                anexo["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
                msg.attach(anexo)

                try:
                    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                        smtp.starttls()
                        smtp.login(email_remetente, senha_app)
                        smtp.send_message(msg)
                    enviados += 1
                    st.success(f"📨 E-mail enviado para {assessor} ({email_destino})")
                except Exception as e:
                    st.error(f"❌ Erro ao enviar para {assessor}: {e}")

            # ✅ Enviar relatório consolidado para Rafael
            try:
                # 🧮 Resumo consolidado geral
                saldo_cc_total = df_final["Saldo CC"].sum()
                saldo_d1_total = df_final["D+1"].sum()
                saldo_d2_total = df_final["D+2"].sum()
                saldo_d3_total = df_final["D+3"].sum()

                resumo_geral_html = f"""
                <p>Olá Rafael,</p>
                <p>Segue o relatório consolidado com todos os dados enviados aos assessores:</p>
                <ul>
                    <li><strong>Saldo em Conta:</strong> {formatar_brasileiro(saldo_cc_total)}</li>
                    <li><strong>Saldo em D+1:</strong> {formatar_brasileiro(saldo_d1_total)}</li>
                    <li><strong>Saldo em D+2:</strong> {formatar_brasileiro(saldo_d2_total)}</li>
                    <li><strong>Saldo em D+3:</strong> {formatar_brasileiro(saldo_d3_total)}</li>
                </ul>
                <p>Relatório detalhado em anexo.</p>
                """

                output_consolidado = io.BytesIO()
                df_final.drop(columns=["Email Assessor"]).to_excel(output_consolidado, index=False)
                output_consolidado.seek(0)

                # 📎 Nome do arquivo consolidado com data
                nome_arquivo_consolidado = f"Saldo_em_Conta_{data_hoje}.xlsx"

                msg_resumo = MIMEMultipart()
                msg_resumo["From"] = email_remetente
                msg_resumo["To"] = "rafael@convexainvestimentos.com"
                msg_resumo["Subject"] = f"📊 Relatório Consolidado – {data_hoje}"

                msg_resumo.attach(MIMEText(resumo_geral_html, "html"))
                anexo_resumo = MIMEApplication(output_consolidado.read(), Name=nome_arquivo_consolidado)
                anexo_resumo["Content-Disposition"] = f'attachment; filename="{nome_arquivo_consolidado}"'
                msg_resumo.attach(anexo_resumo)

                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(email_remetente, senha_app)
                    smtp.send_message(msg_resumo)

                st.success("📨 Relatório consolidado enviado para rafael@convexainvestimentos.com.")

            except Exception as e:
                st.error(f"❌ Erro ao enviar relatório consolidado: {e}")

            st.info(f"✅ {enviados} e-mails enviados com sucesso.")
