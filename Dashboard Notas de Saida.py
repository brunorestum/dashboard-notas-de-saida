import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ======================================================
# Configuração da página
# ======================================================
st.set_page_config(page_title="Dashboard Geral", layout="wide")

# ======================================================
# Criação das abas
# ======================================================
tab1, tab2 = st.tabs(["📊 Dashboard de Notificação", "📈 Notas de Saída Indevidas Scanc"])

# ======================================================
# ABA 1 - Dashboard de Notificação
# ======================================================
with tab1:
    st.title("📊 Dashboard de Notificação")
    st.markdown("Use os filtros abaixo para segmentar os dados.")

    # --- Leitura do Excel direto do GitHub ---
    url1 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/f938a619d06a0edec92587db0b5bbc501b5c7d74/Resultados%20Notifica%C3%A7%C3%A3o.xlsx"
    df = pd.read_excel(url1, engine="openpyxl")

    # --- Padronizar nomes das colunas ---
    df.columns = df.columns.str.strip()  # remove espaços extras
    df.columns = df.columns.str.lower()  # coloca todas em minúsculas
    df.rename(columns={"período": "periodo"}, inplace=True)  # garante nome correto

    # --- Tratamento da coluna período ---
    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].astype(str)
        df_expl = df.assign(periodo=df['periodo'].str.split(';')).explode('periodo')
        df_expl['periodo'] = df_expl['periodo'].str.strip()
    else:
        st.error("⚠️ Coluna 'período' não encontrada no arquivo.")
        df_expl = df.copy()

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    cnpjs = st.sidebar.multiselect("Selecione CNPJ:", options=sorted(df_expl.get('cnpj', pd.Series()).dropna().unique()))
    periodos = st.sidebar.multiselect("Selecione período(s):", options=sorted(df_expl.get('periodo', pd.Series()).dropna().unique()))

    df_filt = df_expl.copy()
    if cnpjs:
        df_filt = df_filt[df_filt.get('cnpj', pd.Series()).isin(cnpjs)]
    if periodos:
        df_filt = df_filt[df_filt.get('periodo', pd.Series()).isin(periodos)]

    # --- KPIs ---
    total_solicitado = df_filt.get('valor_solicitado', pd.Series()).sum()
    total_registros = df_filt.shape[0]

    col1, col2 = st.columns(2)
    col1.metric("💰 Valor Total Solicitado", f"R$ {total_solicitado:,.2f}")
    col2.metric("📄 Total de Registros", f"{total_registros:,}")

    st.markdown("---")

    # --- Gráficos ---
    # (Aqui você pode manter os gráficos iguais, mas sempre usando df_filt.get('coluna', pd.Series())
    # para evitar KeyError se alguma coluna não existir)

# ======================================================
# ABA 2 - Notas de Saída Indevidas Scanc
# ======================================================
with tab2:
    st.title("📊 Notas de Saída Indevidas Scanc")
    st.markdown("Filtros: escolha um contribuinte e/ou período para analisar os dados.")

    # --- Ler o Excel do GitHub ---
    url2 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/main/comparacao-saidas.xlsx"
    comparacao_df = pd.read_excel(url2, engine='openpyxl')

    # --- Padronizar nomes das colunas ---
    comparacao_df.columns = comparacao_df.columns.str.strip().str.lower()
    comparacao_df.rename(columns={
        "razsocial": "razsocial",
        "mesano": "mesano",
        "produto_classificado": "produto_classificado",
        "vlricmsrep": "vlricmsrep",
        "qtd": "qtd"
    }, inplace=True)

    # --- Filtros na sidebar ---
    st.sidebar.header("🔎 Filtros")
    contribuintes = st.sidebar.multiselect(
        "Selecione o contribuinte (razsocial):",
        options=comparacao_df.get("razsocial", pd.Series()).dropna().unique(),
        default=None
    )

    meses_options = ["anotodo"] + sorted(comparacao_df.get("mesano", pd.Series()).dropna().unique().tolist())
    meses = st.sidebar.multiselect(
        "Selecione o período (mesano):",
        options=meses_options,
        default=["anotodo"]
    )

    # --- Aplicar filtros ---
    df_filtered = comparacao_df.copy()
    if contribuintes:
        df_filtered = df_filtered[df_filtered.get("razsocial", pd.Series()).isin(contribuintes)]
    if "anotodo" not in meses:
        df_filtered = df_filtered[df_filtered.get("mesano", pd.Series()).isin(meses)]

    # --- KPIs ---
    total_icms = df_filtered.get("vlricmsrep", pd.Series()).sum()
    total_qtd = df_filtered.get("qtd", pd.Series()).sum()

    col1, col2 = st.columns(2)
    col1.metric("💰 Total ICMS repassado indevidamente na Saída", f"R$ {total_icms:,.2f}")
    col2.metric("📦 Quantidade Total repassada indevidamente na Saída", f"{total_qtd:,.0f}")

    st.markdown("---")

    # --- Gráficos ---
    # (Mantém os gráficos existentes, usando df_filtered.get('coluna', pd.Series()))
