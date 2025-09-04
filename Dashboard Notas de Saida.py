import pandas as pd
import streamlit as st
import plotly.express as px

# =========================================
# Configuração da página
# =========================================
st.set_page_config(page_title="Notas de Saída Fora Scanc", layout="wide")
st.title("📊 Dashboard Interativo - ICMS a Repassar")
st.markdown("Filtros: escolha um contribuinte e/ou período para analisar os dados.")

# =========================================
# Ler o Excel do GitHub
# =========================================
url = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/main/comparacao-saidas.xlsx"
comparacao_df = pd.read_excel(url, engine='openpyxl')

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
col1.metric("💰 Total ICMS repassado indevidamente na Saída", f"R$ {total_icms:,.2f}")
col2.metric("📦 Quantidade Total repassada indevidamente na Saída", f"{total_qtd:,.0f}")

st.markdown("---")

# =========================================
# Gráficos principais lado a lado
# =========================================
col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("💰 ICMS repassado indevidamente por Produto")
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
    st.subheader("💸 Maiores Contribuições por Contribuinte (ICMS)")
    df_razsocial = df_filtered.groupby("razsocial", as_index=False)["vlricmsrep"].sum()
    df_razsocial = df_razsocial.sort_values(by="vlricmsrep", ascending=False).head(10)  # Top 10
    if not df_razsocial.empty:
        fig_razsocial = px.bar(
            df_razsocial, x="razsocial", y="vlricmsrep",
            color="vlricmsrep",
            hover_data={
                "razsocial": True,
                "vlricmsrep": ":,.2f"
            },
            title="Top 10 Contribuintes por ICMS Repassado",
            labels={"vlricmsrep": "ICMS a Repassar (R$)", "razsocial": "Contribuinte"}
        )
        st.plotly_chart(fig_razsocial, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir neste gráfico.")

# =========================================
# Gráfico de quantidade por produto
# =========================================
st.subheader("📦 Quantidade repassada indevidamente por Produto")
if not df_filtered.empty:
    fig_pizza = px.pie(
        df_filtered, values="qtdb", names="produto_classificado",
        title="Proporção da Quantidade por Produto"
    )
    st.plotly_chart(fig_pizza, use_container_width=True)
else:
    st.warning("⚠️ Sem dados para exibir neste gráfico.")

# =========================================
# Evolução mensal com tooltip interativo
# =========================================
st.subheader("📅 Evolução Mensal do ICMS repassado indevidamente")
df_mes = df_filtered.groupby("mesano", as_index=False)["vlricmsrep"].sum()
if not df_mes.empty:
    fig_mes = px.line(
        df_mes,
        x="mesano",
        y="vlricmsrep",
        markers=True,
        title="ICMS a Repassar por Mês",
        hover_data={
            "mesano": True,
            "vlricmsrep": ":,.2f"
        },
        labels={
            "mesano": "Mês/Ano",
            "vlricmsrep": "ICMS a Repassar (R$)"
        }
    )
    st.plotly_chart(fig_mes, use_container_width=True)
else:
    st.warning("⚠️ Sem dados para exibir na evolução mensal.")

st.markdown("---")
st.info("💡 Para compartilhar: rode `streamlit run app.py` ou publique no [Streamlit Cloud](https://streamlit.io/cloud).")
