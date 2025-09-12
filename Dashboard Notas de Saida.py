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

    # --- Leitura do Excel ---
    url1 = "https://raw.githubusercontent.com/brunorestum/dashboard-notas-de-saida/f77513753a72efc8a1a43e46f6a82db867f6181a/resultado_notificacao.xlsx"
    df = pd.read_excel(url1, engine="openpyxl")
    df.columns = [c.strip().lower() for c in df.columns]

    # --- Explodir períodos ---
    df['periodo'] = df['periodo'].astype(str)
    df_expl = df.assign(periodo=df['periodo'].str.split(';')).explode('periodo')
    df_expl['periodo'] = df_expl['periodo'].str.strip()

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    razao_social_opcoes = sorted(df_expl['raz_social'].dropna().unique())
    razao_social_sel = st.sidebar.multiselect(
        "Selecione Razão Social:", options=razao_social_opcoes, default=[]
    )

    periodos_opcoes = ["anotodo"] + sorted(df_expl['periodo'].dropna().unique())
    periodos_sel = st.sidebar.multiselect(
        "Selecione Período(s):", options=periodos_opcoes, default=["anotodo"]
    )

    # --- Aplicar filtros ---
    df_filt = df_expl.copy()
    if razao_social_sel:
        df_filt = df_filt[df_filt['raz_social'].isin(razao_social_sel)]
    if "anotodo" not in periodos_sel:
        df_filt = df_filt[df_filt['periodo'].isin(periodos_sel)]

    # --- Garantir valor numérico ---
    df_filt['valor_solicitado'] = pd.to_numeric(df_filt['valor_solicitado'], errors='coerce').fillna(0)

    # --- KPIs ---
    total_solicitado = df_filt['valor_solicitado'].sum()
    total_registros = df_filt.shape[0]

    col1, col2 = st.columns(2)
    col1.metric("💰 Valor Total Solicitado", f"R$ {total_solicitado:,.2f}")
    col2.metric("📄 Total de Registros", f"{total_registros:,}")

    st.markdown("---")

    if not df_filt.empty:
        # --- Gráficos lado a lado ---
        col1, col2 = st.columns([1, 2])
        with col1:
            if 'status' in df_filt.columns:
                fig_status = px.pie(df_filt, names='status', title="Proporção por Status")
                st.plotly_chart(fig_status, use_container_width=True)
        with col2:
            if 'situacao' in df_filt.columns:
                df_sit = df_filt.groupby('situacao', as_index=False)['valor_solicitado'].sum()
                fig_sit = px.bar(df_sit.sort_values('valor_solicitado', ascending=False),
                                 x='situacao', y='valor_solicitado',
                                 color='situacao', text_auto=".2s",
                                 title="Valor Solicitado por Situação")
                st.plotly_chart(fig_sit, use_container_width=True)

        # --- Top 10 Razões Sociais ---
        df_rs = df_filt.groupby('raz_social', as_index=False)['valor_solicitado'].sum()
        df_rs = df_rs.sort_values('valor_solicitado', ascending=False).head(10)
        fig_rs = px.bar(df_rs, x='raz_social', y='valor_solicitado', color='valor_solicitado',
                        title="Top 10 – Razão Social")
        st.plotly_chart(fig_rs, use_container_width=True)

        # --- Evolução Mensal ---
        if 'mês_repasse' in df_filt.columns:
            df_filt['mês_repasse_dt'] = pd.to_datetime(df_filt['mês_repasse'], format='%m/%Y', errors='coerce')
            df_mes = df_filt.groupby('mês_repasse_dt', as_index=False)['valor_solicitado'].sum()
            df_mes = df_mes.sort_values('mês_repasse_dt')
            df_mes['mes_ano'] = df_mes['mês_repasse_dt'].dt.strftime('%m/%Y')
            fig_mes = px.line(df_mes, x='mes_ano', y='valor_solicitado', markers=True,
                              title="Valor Solicitado por Mês de Repasse")
            st.plotly_chart(fig_mes, use_container_width=True)

        # --- Quantidade e Valor por Origem ---
        if 'origem' in df_filt.columns:
            df_origem = df_filt.groupby('origem', as_index=False).agg(
                quantidade=('origem', 'count'), soma_valor=('valor_solicitado', 'sum')
            )
            fig_origem = px.scatter(df_origem, x='origem', y='soma_valor', size='quantidade',
                                    color='origem', title="Origem: Quantidade e Valor Solicitado")
            st.plotly_chart(fig_origem, use_container_width=True)

        # --- Economia Total com Ampulheta Realista ---
        num_notificacoes = df_filt.shape[0]
        horas_por_notificacao = 8
        custo_hora = 173
        horas_total = num_notificacoes * horas_por_notificacao
        valor_economizado = horas_total * custo_hora

        st.subheader("💰 Economia Total Estimada com Notificações")
        st.markdown(f"- Total de Notificações Processadas: **{num_notificacoes}**")
        st.markdown(f"- Horas Totais Investidas: **{horas_total} h**")
        st.markdown(f"- Valor Economizado com a Ação: **R$ {valor_economizado:,.2f}** 💸")

        valor_total_str = f"R$ {valor_economizado:,.2f}"

        # --- Ampulheta com partículas de areia ---
        html_ampulheta_realista = f"""
        <div style="width:120px; height:250px; margin:auto; position:relative;">
          <!-- Ampulheta -->
          <div style="position:absolute; top:0; left:0; width:100%; height:100%; border-left:4px solid black; border-right:4px solid black; clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%); overflow:hidden;">
              <!-- Areia superior caindo -->
              <div style="position:absolute; top:0; left:50%; width:4px; height:100%; background:gold; animation: sandFall 8s infinite;"></div>
              <!-- Areia acumulada inferior -->
              <div style="position:absolute; bottom:0; left:0; width:100%; height:0%; background:gold; animation: sandFill 20s forwards;"></div>
          </div>
          <!-- Valor abaixo -->
          <h3 style="text-align:center; margin-top:260px; font-size:16px;">{valor_total_str}</h3>
        </div>

        <style>
        @keyframes sandFall {{
          0% {{ transform: translateY(-100%); opacity:0; }}
          50% {{ transform: translateY(50%); opacity:1; }}
          100% {{ transform: translateY(100%); opacity:0; }}
        }}
        @keyframes sandFill {{
          0% {{ height: 0%; }}
          100% {{ height: 100%; }}
        }}
        </style>
        """

        st.markdown(html_ampulheta_realista, unsafe_allow_html=True)

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
            fig_icms = px.bar(
                df_prod,
                x="produto_classificado",
                y="vlricmsrep",
                color="produto_classificado",
                text_auto=".2s",
                title="ICMS a Repassar por Produto"
            )
            st.plotly_chart(fig_icms, use_container_width=True)

        # Top 10 Contribuintes
        st.subheader("💸 Maiores Contribuições por Contribuinte (ICMS)")
        df_razsocial = df_filtered.groupby("razsocial", as_index=False)["vlricmsrep"].sum()
        df_razsocial = df_razsocial.sort_values(by="vlricmsrep", ascending=False).head(10)
        fig_razsocial = px.bar(
            df_razsocial,
            x="razsocial",
            y="vlricmsrep",
            color="vlricmsrep",
            hover_data={"razsocial": True, "vlricmsrep": ":,.2f"},
            title="Top 10 Contribuintes por ICMS Repassado",
            labels={"vlricmsrep": "ICMS a Repassar (R$)", "razsocial": "Contribuinte"}
        )
        st.plotly_chart(fig_razsocial, use_container_width=True)

        # Evolução Mensal
        st.subheader("📅 Evolução Mensal do ICMS repassado indevidamente")
        df_mes = df_filtered.groupby("mesano", as_index=False)["vlricmsrep"].sum()
        if not df_mes.empty:
            df_mes["mesano_str"] = df_mes["mesano"].astype(str)
            df_mes = df_mes.sort_values("mesano_str")
            fig_mes = px.line(
                df_mes,
                x="mesano_str",
                y="vlricmsrep",
                markers=True,
                title="Evolução Mensal do ICMS repassado indevidamente"
            )
            st.plotly_chart(fig_mes, use_container_width=True)
    else:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados na aba 2.")
