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
total_qtd = df_filtered["qtd"].sum()

col1, col2 = st.columns(2)
col1.metric("💰 Total ICMS repassado indevidamente na Saída", f"R$ {total_icms:,.2f}")
col2.metric("📦 Quantidade Total repassada indevidamente na Saída", f"{total_qtd:,.0f}")

st.markdown("---")

# =========================================
# Gráficos de Produto lado a lado
# =========================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Quantidade repassada indevidamente por Produto")
    if not df_filtered.empty:
        fig_qtd = px.pie(
            df_filtered, values="qtd", names="produto_classificado",
            title="Proporção da Quantidade por Produto"
        )
        st.plotly_chart(fig_qtd, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir neste gráfico.")

with col2:
    st.subheader("💰 ICMS repassado indevidamente por Produto")
    df_prod = df_filtered.groupby("produto_classificado", as_index=False)["vlricmsrep"].sum()
    if not df_prod.empty:
        fig_icms = px.bar(
            df_prod, x="produto_classificado", y="vlricmsrep", color="produto_classificado",
            text_auto=".2s", title="ICMS a Repassar por Produto"
        )
        st.plotly_chart(fig_icms, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir neste gráfico.")

# =========================================
# Gráfico de maiores contribuições por contribuinte (embaixo)
# =========================================
st.subheader("💸 Maiores Contribuições por Contribuinte (ICMS)")
df_razsocial = df_filtered.groupby("razsocial", as_index=False)["vlricmsrep"].sum()
df_razsocial = df_razsocial.sort_values(by="vlricmsrep", ascending=False).head(10)  # Top 10
if not df_razsocial.empty:
    fig_razsocial = px.bar(
        df_razsocial, x="razsocial", y="vlricmsrep",
        color="vlricmsrep",
        hover_data={"razsocial": True, "vlricmsrep": ":,.2f"},
        title="Top 10 Contribuintes por ICMS Repassado",
        labels={"vlricmsrep": "ICMS a Repassar (R$)", "razsocial": "Contribuinte"}
    )
    st.plotly_chart(fig_razsocial, use_container_width=True)
else:
    st.warning("⚠️ Sem dados para exibir neste gráfico.")

# =========================================
# Evolução mensal com eixo mesano como texto
# =========================================
st.subheader("📅 Evolução Mensal do ICMS repassado indevidamente")
df_mes = df_filtered.groupby("mesano", as_index=False)["vlricmsrep"].sum()
if not df_mes.empty:
    # Transformar mesano em string para garantir que apareça exatamente
    df_mes["mesano_str"] = df_mes["mesano"].astype(str)
    
    # Ordenar os valores para manter a sequência correta
    df_mes = df_mes.sort_values("mesano")
    
    fig_mes = px.line(
        df_mes,
        x="mesano_str",
        y="vlricmsrep",
        markers=True,
        title="ICMS a Repassar por Mês",
        hover_data={"mesano_str": True, "vlricmsrep": ":,.2f"},
        labels={"mesano_str": "Mês/Ano", "vlricmsrep": "ICMS a Repassar (R$)"},
        category_orders={"mesano_str": df_mes["mesano_str"].tolist()}  # garante a ordem e evita abreviações
    )
    
    # Forçar o eixo x a mostrar os valores completos sem abreviações
    fig_mes.update_xaxes(tickmode="array", tickvals=df_mes["mesano_str"], ticktext=df_mes["mesano_str"])
    
    st.plotly_chart(fig_mes, use_container_width=True)
else:
    st.warning("⚠️ Sem dados para exibir na evolução mensal.")

# =========================================
# Tabela detalhada das notas
# =========================================
st.subheader("📋 Tabela detalhada das Notas de Saída")

# Selecionar e reordenar as colunas
colunas_tabela = [
    "cnpjh",
    "razsocial",
    "uf",
    "numnf",
    "dtemissao",
    "cfop",
    "qtd",
    "vlricmsrep",
    "produto_classificado"
]

# Verificar se todas as colunas existem
colunas_existentes = [c for c in colunas_tabela if c in df_filtered.columns]

# Mostrar a tabela
if not df_filtered.empty and colunas_existentes:
    st.dataframe(df_filtered[colunas_existentes].sort_values("dtemissao"), use_container_width=True)
else:
    st.warning("⚠️ Não há dados suficientes para exibir a tabela.")

st.markdown("---")
st.info("💡 Para compartilhar: rode `streamlit run app.py` ou publique no [Streamlit Cloud](https://streamlit.io/cloud).")
