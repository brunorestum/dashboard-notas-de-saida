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

    # --- Tratamento da coluna período ---
    df['período'] = df['período'].astype(str)
    df_expl = df.assign(período=df['período'].str.split(';')).explode('período')
    df_expl['período'] = df_expl['período'].str.strip()

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    cnpjs = st.sidebar.multiselect("Selecione CNPJ:", options=sorted(df_expl['cnpj'].dropna().unique()))
    periodos = st.sidebar.multiselect("Selecione período(s):", options=sorted(df_expl['período'].dropna().unique()))

    df_filt = df_expl.copy()
    if cnpjs:
        df_filt = df_filt[df_filt['cnpj'].isin(cnpjs)]
    if periodos:
        df_filt = df_filt[df_filt['período'].isin(periodos)]

    # --- KPIs ---
    total_solicitado = df_filt['valor_solicitado'].sum()
    total_registros = df_filt.shape[0]

    col1, col2 = st.columns(2)
    col1.metric("💰 Valor Total Solicitado", f"R$ {total_solicitado:,.2f}")
    col2.metric("📄 Total de Registros", f"{total_registros:,}")

    st.markdown("---")

    # --- Gráfico 1 ---
    st.subheader("📌 Quantidade de Registros por Situação")
    if not df_filt.empty:
        fig1 = px.pie(df_filt, names='situação', title="Proporção por Situação")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir no Gráfico 1.")

    # --- Gráfico 2 ---
    st.subheader("📦 Valor Solicitado por Categoria")
    df_cat = df_filt.groupby('categoria', as_index=False)['valor_solicitado'].sum()
    if not df_cat.empty:
        fig2 = px.bar(
            df_cat.sort_values('valor_solicitado', ascending=False),
            x='categoria', y='valor_solicitado', color='categoria', text_auto=".2s",
            title="Valor Solicitado por Categoria"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir no Gráfico 2.")

    # --- Gráfico 3 ---
    st.subheader("💸 Top 10 Razões Sociais por Valor Solicitado")
    df_rs = df_filt.groupby('razão social', as_index=False)['valor_solicitado'].sum()
    df_rs = df_rs.sort_values('valor_solicitado', ascending=False).head(10)
    if not df_rs.empty:
        fig3 = px.bar(df_rs, x='razão social', y='valor_solicitado', color='valor_solicitado',
                      title="Top 10 – Razão Social")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir no Gráfico 3.")

    # --- Gráfico 4 ---
    st.subheader("📅 Evolução Mensal do Valor Solicitado")
    if 'mês de repasse' in df_filt.columns:
        df_mes = df_filt.groupby('mês de repasse', as_index=False)['valor_solicitado'].sum()
        if not df_mes.empty:
            df_mes = df_mes.sort_values('mês de repasse')
            fig4 = px.line(df_mes, x='mês de repasse', y='valor_solicitado', markers=True,
                           title="Valor Solicitado por Mês de Repasse")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("⚠️ Sem dados para exibir no Gráfico 4.")
    else:
        st.warning("⚠️ Coluna 'mês de repasse' não encontrada.")

    # --- Gráfico 5 ---
    st.subheader("💰 Progresso de Repasses (Efetuado vs Aguardando)")
    efetuado = df_filt.loc[df_filt['situação'] == 'Repasse Efetuado', 'valor_solicitado'].sum()
    aguardando = df_filt.loc[df_filt['situação'] == 'Aguardando repasse', 'valor_solicitado'].sum()
    total_possivel = efetuado + aguardando
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(x=['Total Possível'], y=[total_possivel],
                          name='Total Possível (Efetuado + Aguardando)', marker_color='lightgray'))
    fig5.add_trace(go.Bar(x=['Total Possível'], y=[efetuado],
                          name='Efetuado', marker_color='green'))
    fig5.update_layout(barmode='overlay', title="Comparativo: Efetuado vs Total Possível",
                       yaxis_title="Valor (R$)")
    st.plotly_chart(fig5, use_container_width=True)

    # --- Gráfico 6 ---
    st.subheader("📍 Quantidade e Valor por Origem")
    if 'origem' in df_filt.columns:
        df_origem = df_filt.groupby('origem', as_index=False).agg(
            quantidade=('origem', 'count'), soma_valor=('valor_solicitado', 'sum'))
        if not df_origem.empty:
            fig6 = px.scatter(df_origem, x='origem', y='soma_valor', size='quantidade',
                              color='origem', title="Origem: Quantidade e Valor Solicitado")
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.warning("⚠️ Sem dados para exibir no Gráfico 6.")
    else:
        st.warning("⚠️ Coluna 'origem' não encontrada.")

# ======================================================
# ABA 2 - Notas de Saída Indevidas Scanc
# ======================================================
with tab2:
    st.title("📊 Notas de Saída Indevidas Scanc")
    st.markdown("Filtros: escolha um contribuinte e/ou período para analisar os dados.")

    # --- Ler o Excel do GitHub ---
    url2 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/main/comparacao-saidas.xlsx"
    comparacao_df = pd.read_excel(url2, engine='openpyxl')

    # --- Filtros na sidebar ---
    st.sidebar.header("🔎 Filtros")
    contribuintes = st.sidebar.multiselect(
        "Selecione o contribuinte (razsocial):",
        options=comparacao_df["razsocial"].dropna().unique(),
        default=None
    )

    meses_options = ["anotodo"] + sorted(comparacao_df["mesano"].dropna().unique().tolist())
    meses = st.sidebar.multiselect(
        "Selecione o período (mesano):",
        options=meses_options,
        default=["anotodo"]
    )

    # --- Aplicar filtros ---
    df_filtered = comparacao_df.copy()
    if contribuintes:
        df_filtered = df_filtered[df_filtered["razsocial"].isin(contribuintes)]
    if "anotodo" not in meses:
        df_filtered = df_filtered[df_filtered["mesano"].isin(meses)]

    # --- KPIs ---
    total_icms = df_filtered["vlricmsrep"].sum()
    total_qtd = df_filtered["qtd"].sum()

    col1, col2 = st.columns(2)
    col1.metric("💰 Total ICMS repassado indevidamente na Saída", f"R$ {total_icms:,.2f}")
    col2.metric("📦 Quantidade Total repassada indevidamente na Saída", f"{total_qtd:,.0f}")

    st.markdown("---")

    # --- Gráficos de Produto lado a lado ---
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

    # --- Gráfico Top 10 Contribuintes ---
    st.subheader("💸 Maiores Contribuições por Contribuinte (ICMS)")
    df_razsocial = df_filtered.groupby("razsocial", as_index=False)["vlricmsrep"].sum()
    df_razsocial = df_razsocial.sort_values(by="vlricmsrep", ascending=False).head(10)
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

    # --- Evolução mensal ---
    st.subheader("📅 Evolução Mensal do ICMS repassado indevidamente")
    df_mes = df_filtered.groupby("mesano", as_index=False)["vlricmsrep"].sum()
    if not df_mes.empty:
        df_mes["mesano_str"] = df_mes["mesano"].astype(str)
        df_mes = df_mes.sort_values("mesano_str")
        fig_mes = px.line(
            df_mes, x="mesano_str", y="vlricmsrep", markers=True,
            title="Evolução Mensal do ICMS repassado indevidamente"
        )
        st.plotly_chart(fig_mes, use_container_width=True)
    else:
        st.warning("⚠️ Sem dados para exibir no gráfico mensal.")


