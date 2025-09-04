# -*- coding: utf-8 -*-
"""
Created on Thu Sep  4 10:44:11 2025

@author: bruno.manzatto
"""

# importar pandas

import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# =========================================
# Configuração da página
# =========================================
st.set_page_config(page_title="Dashboard ICMS", layout="wide")
st.title("📊 Dashboard Interativo - ICMS a Repassar")
st.markdown("Filtros: escolha um contribuinte e/ou período para analisar os dados.")

# =========================================
# Ler o Excel
# =========================================
# Certifique-se de que o arquivo "comparacao-saidas.xlsx" está na mesma pasta do app
comparacao_df = pd.read_excel("comparacao-saidas.xlsx")

# =========================================
# Filtros na sidebar
# =========================================
st.sidebar.header("🔎 Filtros")

# Filtro de contribuintes
contribuintes = st.sidebar.multiselect(
    "Selecione o contribuinte (razsocial):",
    options=comparacao_df["razsocial"].dropna().unique(),
    default=None
)

# Filtro de meses com opção "anotodo"
meses_options = ["anotodo"] + sorted(comparacao_df["mesano"].dropna().unique().tolist())
meses = st.sidebar.multiselect(
    "Selecione o período (mesano):",
    options=meses_options,
    default=["anotodo"]
)

# =========================================
# Aplicar filtros
# =========================================
df_filtered = comparacao_df.copy()

if contribuintes:
    df_filtered = df_filtered[df_filtered["razsocial"].isin(contribuintes)]

if "anotodo" not in meses:
    df_filtered = df_filtered[df_filtered["mesano"].isin(meses)]

# =========================================
# KPIs
# =========================================
total_icms = df_filtered["vlricmsrep"].sum()
total_qtd = df_filtered["qtdb"].sum()

col1, col2 = st.columns(2)
col1.metric("💰 Total ICMS a Repassar", f"R$ {total_icms:,.2f}")
col2.metric("📦 Quantidade Total", f"{total_qtd:,.0f}")

st.markdown("---")

# =========================================
# Gráficos
# =========================================

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📦 ICMS a Repassar por Produto")
    df_prod = df_filtered.groupby("produto_classificado", as_index=False)["vlricmsrep"].sum()
    if not df_prod.empty:
        fig_prod = px.bar(
            df_prod, x="produto_classificado", y="vlricmsrep", color="produto_classificado",
            text_auto=".2s", title="ICMS a Repassar por Produto"
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir neste gráfico.")

with col2:
    st.subheader("🥧 Distribuição de Quantidade por Produto")
    if not df_filtered.empty:
        fig_pizza = px.pie(
            df_filtered, values="qtdb", names="produto_classificado",
            title="Proporção da Quantidade por Produto"
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir neste gráfico.")

# Evolução mensal
st.subheader("📅 Evolução Mensal - ICMS a Repassar")
df_mes = df_filtered.groupby("mesano", as_index=False)["vlricmsrep"].sum()
if not df_mes.empty:
    fig_mes = px.line(
        df_mes, x="mesano", y="vlricmsrep", markers=True, title="ICMS a Repassar por Mês"
    )
    st.plotly_chart(fig_mes, use_container_width=True)
else:
    st.warning("⚠️ Sem dados para exibir na evolução mensal.")

# Heatmap
st.subheader("🔥 Correlação entre Quantidade e ICMS a Repassar")
corr = df_filtered[["qtdb", "vlricmsrep"]].corr()

if corr.isna().all().all():
    st.warning("⚠️ Não há dados suficientes para calcular a correlação neste filtro.")
else:
    fig, ax = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="YlOrRd", ax=ax, vmin=-1, vmax=1)
    st.pyplot(fig)

st.markdown("---")
st.info("💡 Para compartilhar: rode `streamlit run app.py` ou publique no [Streamlit Cloud](https://streamlit.io/cloud).")
