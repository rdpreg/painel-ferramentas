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
    """Formata número no padrão brasileiro com R$"""
    texto = f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    if valor < 0:
        return f"<span style='color: red;'>{texto}</span>"
    return texto

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

        # 🖥️ Formatar valores no padrão brasileiro e aplicar cores
        df_formatado = df_final.copy()
        for col in ["Saldo CC", "D+1", "D+2", "D+3", "Saldo Projetado"]:
            df_formatado[col] = df_formatado[col].apply(formatar_brasileiro)

        # Exibir tabela estilizada com barra de rolagem horizontal
        st.subheader("📊 Dados Processados (Saldo Projetado ≠ 0)")
        tabela_html = df_formatado.to_html(escape=False, index=False)
        tabela_com_scroll = f"""
        <div style="overflow-x:auto; border:1px solid #ddd; padding:8px">
            {tabela_html}
        </div>
        """
        st.markdown(tabela_com_scroll, unsafe_allow_html=True)

        st.success(f"✅ {df_final.shape[0]} clientes com Saldo Projetado ≠ 0 processados com sucesso.")

        if st.button("📧 Enviar e-mail de teste para Rafael"):
            email_remetente = st.secrets["email"]["remetente"]
            senha_app = st.secrets["email"]["senha_app"]

            try:
                # 🧮 Resumo consolidado
                saldo_cc_total = df_final["Saldo CC"].sum()
                saldo_d1_total = df_final["D+1"].sum()
                saldo_d2_total = df_final["D+2"].sum()
                saldo_d3_total = df_final["D+3"].sum()

                resumo_html = f"""
                <p>Olá Rafael,</p>
                <p>Aqui estão os dados de Saldo em Conta consolidados. O relatório detalhado está em anexo.</p>
                <ul>
                    <li><strong>Saldo em Conta:</strong> {formatar_brasileiro(saldo_cc_total)}</li>
                    <li><strong>Saldo em D+1:</strong> {formatar_brasileiro(saldo_d1_total)}</li>
                    <li><strong>Saldo em D+2:</strong> {formatar_brasileiro(saldo_d2_total)}</li>
                    <li><strong>Saldo em D+3:</strong> {formatar_brasileiro(saldo_d3_total)}</li>
                </ul>
                <p>Abraços,<br>Equipe Convexa</p>
                """

                # Gerar anexo Excel (números puros para cálculos)
                output = io.BytesIO()
                df_final.to_excel(output, index=False)
                output.seek(0)

                # Montar e-mail
                msg = MIMEMultipart()
                msg["From"] = formataddr(("Backoffice Convexa", email_remetente))
                msg["To"] = "rafael@convexainvestimentos.com"
                msg["Subject"] = "📩 [TESTE] Fluxo Financeiro – Consolidado"

                msg.attach(MIMEText(resumo_html, "html"))
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
