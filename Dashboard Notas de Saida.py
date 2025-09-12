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
    url1 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/f938a619d06a0edec92587db0b5bbc501b5c7d74/Resultados%20Notificacao.xlsx"
    df = pd.read_excel(url1, engine="openpyxl")

    # --- Padronizar nomes das colunas ---
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('ã','a').str.replace('ç','c')

    # --- Tratamento da coluna período ---
    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].astype(str)
        df_expl = df.assign(periodo=df['periodo'].str.split(';')).explode('periodo')
        df_expl['periodo'] = df_expl['periodo'].str.strip()
    else:
        st.warning("⚠️ Coluna 'periodo' não encontrada no arquivo.")
        df_expl = df.copy()

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    todas_razsocial = sorted(df_expl.get('razao_social', pd.Series()).dropna().unique())
    razao_social_sel = st.sidebar.multiselect(
        "Selecione Razão Social:",
        options=todas_razsocial,
        default=[]
    )
    todos_periodos = ["anotodo"] + sorted(df_expl.get('periodo', pd.Series()).dropna().unique())
    periodos_sel = st.sidebar.multiselect(
        "Selecione período(s):",
        options=todos_periodos,
        default=["anotodo"]
    )

    # --- Aplicar filtros ---
    df_filt = df_expl.copy()
    if razao_social_sel:
        df_filt = df_filt[df_filt.get('razao_social', pd.Series()).isin(razao_social_sel)]
    if "anotodo" not in periodos_sel:
        df_filt = df_filt[df_filt.get('periodo', pd.Series()).isin(periodos_sel)]

    # --- Garantir tipo numérico ---
    df_filt['valor_solicitado'] = pd.to_numeric(df_filt.get('valor_solicitado', pd.Series()), errors='coerce').fillna(0)

    # --- KPIs ---
    total_solicitado = df_filt['valor_solicitado'].sum()
    total_registros = df_filt.shape[0]

    col1, col2 = st.columns(2)
    col1.metric("💰 Valor Total Solicitado", f"R$ {total_solicitado:,.2f}")
    col2.metric("📄 Total de Registros", f"{total_registros:,}")

    st.markdown("---")

    # --- Gráficos ---
    if not df_filt.empty:
        # Gráfico 1: Quantidade de registros por situação
        if 'situacao' in df_filt.columns:
            fig1 = px.pie(df_filt, names='situacao', title="Proporção por Situação")
            st.plotly_chart(fig1, use_container_width=True)

        # Gráfico 2: Valor solicitado por categoria
        if 'categoria' in df_filt.columns:
            df_cat = df_filt.groupby('categoria', as_index=False)['valor_solicitado'].sum()
            fig2 = px.bar(df_cat.sort_values('valor_solicitado', ascending=False),
                          x='categoria', y='valor_solicitado', color='categoria', text_auto=".2s",
                          title="Valor Solicitado por Categoria")
            st.plotly_chart(fig2, use_container_width=True)

        # Gráfico 3: Top 10 Razões Sociais
        if 'razao_social' in df_filt.columns:
            df_rs = df_filt.groupby('razao_social', as_index=False)['valor_solicitado'].sum()
            df_rs = df_rs.sort_values('valor_solicitado', ascending=False).head(10)
            fig3 = px.bar(df_rs, x='razao_social', y='valor_solicitado', color='valor_solicitado',
                          title="Top 10 – Razão Social")
            st.plotly_chart(fig3, use_container_width=True)

        # Gráfico 4: Evolução Mensal
        if 'mes_de_repasse' in df_filt.columns:
            df_mes = df_filt.groupby('mes_de_repasse', as_index=False)['valor_solicitado'].sum()
            df_mes = df_mes.sort_values('mes_de_repasse')
            fig4 = px.line(df_mes, x='mes_de_repasse', y='valor_solicitado', markers=True,
                           title="Valor Solicitado por Mês de Repasse")
            st.plotly_chart(fig4, use_container_width=True)

        # Gráfico 5: Progresso de Repasses
        if 'situacao' in df_filt.columns:
            efetuado = df_filt.loc[df_filt['situacao'] == 'Repasse Efetuado', 'valor_solicitado'].sum()
            aguardando = df_filt.loc[df_filt['situacao'] == 'Aguardando repasse', 'valor_solicitado'].sum()
            total_possivel = efetuado + aguardando
            fig5 = go.Figure()
            fig5.add_trace(go.Bar(x=['Total Possível'], y=[total_possivel],
                                  name='Total Possível (Efetuado + Aguardando)', marker_color='lightgray'))
            fig5.add_trace(go.Bar(x=['Total Possível'], y=[efetuado],
                                  name='Efetuado', marker_color='green'))
            fig5.update_layout(barmode='overlay', title="Comparativo: Efetuado vs Total Possível",
                               yaxis_title="Valor (R$)")
            st.plotly_chart(fig5, use_container_width=True)

        # Gráfico 6: Quantidade e Valor por Origem
        if 'origem' in df_filt.columns:
            df_origem = df_filt.groupby('origem', as_index=False).agg(
                quantidade=('origem', 'count'), soma_valor=('valor_solicitado', 'sum'))
            if not df_origem.empty:
                fig6 = px.scatter(df_origem, x='origem', y='soma_valor', size='quantidade',
                                  color='origem', title="Origem: Quantidade e Valor Solicitado")
                st.plotly_chart(fig6, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")

# ======================================================
# ABA 2 - Notas de Saída Indevidas Scanc
# ======================================================
with tab2:
    st.title("📊 Notas de Saída Indevidas Scanc")
    st.markdown("Filtros: escolha um contribuinte e/ou período para analisar os dados.")

    url2 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/main/comparacao-saidas.xlsx"
    comparacao_df = pd.read_excel(url2, engine='openpyxl')

    # Padronizar colunas
    comparacao_df.columns = comparacao_df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('ã','a').str.replace('ç','c')

    # Filtros
    st.sidebar.header("🔎 Filtros")
    contribuintes = st.sidebar.multiselect(
        "Selecione o contribuinte (razsocial):",
        options=comparacao_df["razsocial"].dropna().unique(),
        default=[]
    )
    meses_options = ["anotodo"] + sorted(comparacao_df["mesano"].dropna().unique())
    meses_sel = st.sidebar.multiselect(
        "Selecione período (mesano):",
        options=meses_options,
        default=["anotodo"]
    )

    df_filtered = comparacao_df.copy()
    if contribuintes:
        df_filtered = df_filtered[df_filtered["razsocial"].isin(contribuintes)]
    if "anotodo" not in meses_sel:
        df_filtered = df_filtered[df_filtered["mesano"].isin(meses_sel)]

    # Garantir tipos numéricos
    df_filtered['vlricmsrep'] = pd.to_numeric(df_filtered.get('vlricmsrep', pd.Series()), errors='coerce').fillna(0)
    df_filtered['qtd'] = pd.to_numeric(df_filtered.get('qtd', pd.Series()), errors='coerce').fillna(0)

    # KPIs
    total_icms = df_filtered['vlricmsrep'].sum()
    total_qtd = df_filtered['qtd'].sum()
    col1, col2 = st.columns(2)
    col1.metric("💰 Total ICMS repassado indevidamente na Saída", f"R$ {total_icms:,.2f}")
    col2.metric("📦 Quantidade Total repassada indevidamente na Saída", f"{total_qtd:,.0f}")

    st.markdown("---")

    # Gráficos Aba 2
    if not df_filtered.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_qtd = px.pie(df_filtered, values="qtd", names="produto_classificado",
                             title="Proporção da Quantidade por Produto")
            st.plotly_chart(fig_qtd, use_container_width=True)
        with col2:
            df_prod = df_filtered.groupby("produto_classificado", as_index=False)["vlricmsrep"].sum()
            fig_icms = px.bar(df_prod, x="produto_classificado", y="vl
