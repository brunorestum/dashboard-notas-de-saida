# -*- coding: utf-8 -*-
"""
Created on Thu Sep  4 10:44:11 2025

@author: bruno.manzatto
"""

# importar pandas

import pandas as pd
from sqlalchemy import *
import sqlalchemy
import fdb
import geopandas as gpd
import plotly.express as px
import webbrowser
from unidecode import unidecode
import os
import unicodedata
import nltk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime


#Carregar dados do Excel
file_path = r'C:\Users\bruno.manzatto\Desktop\Phyton\Excel\Saídas_interestaduais_de_combustivel.csv'
notas_interestaduais_de_combustiveis_df = pd.read_csv(
    file_path,
    sep=',',                 # CSV separado por ponto e vírgula
    dtype=str,               # Garante que tudo será lido como texto (inclusive CNPJ)
    encoding='utf-8',        # Ou 'latin1' se der erro de acentuação
    decimal=','              # Indica que os números usam vírgula como separador decimal
)



notas_interestaduais_de_combustiveis_df['Quantidade Comercial'] = pd.to_numeric(
    notas_interestaduais_de_combustiveis_df['Quantidade Comercial']
    .astype(str)
    .str.replace(',', '.', regex=False), 
    errors='coerce'  # valores inválidos viram NaN
)

print(notas_interestaduais_de_combustiveis_df.columns)


# Função para remover acentos
def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                   if unicodedata.category(c) != 'Mn')

# Inicializar stemmer e stopwords
stemmer = RSLPStemmer()
stop_words = set(stopwords.words('portuguese'))

# Função para processar e classificar a descrição do produto
def processar_descricao(texto):
    if pd.isnull(texto):
        return None

    texto_sem_acentos = remover_acentos(texto.lower())
    palavras = texto_sem_acentos.split()
    palavras_filtradas = [stemmer.stem(p) for p in palavras if p not in stop_words]
    texto_stemmed = " ".join(palavras_filtradas)

    # Lógica de classificação com exceção para biodiesel
    if "gasolin" in texto_stemmed or "avgas" in texto_sem_acentos:
        return "gasolina"
    elif (
        "diesel" in texto_stemmed
        and all(b not in texto_sem_acentos for b in ["biodiesel", "bio diesel", "bio-diesel"])
    ):
        return "diesel"
    elif any(p in texto_sem_acentos for p in ["s500", "s-500", "s10", "s-10"]):
        return "diesel"
    else:
        return "outros"

notas_interestaduais_de_combustiveis_df["Categoria Produto (Analisada)"] = \
    notas_interestaduais_de_combustiveis_df["Descrição Produto"].apply(processar_descricao)
    
    # filtrar outros
notas_interestaduais_de_combustiveis_df = notas_interestaduais_de_combustiveis_df[notas_interestaduais_de_combustiveis_df["Categoria Produto (Analisada)"]!='outros']
notas_interestaduais_de_combustiveis_df['Unidade Comercialização Produto'] = (
    notas_interestaduais_de_combustiveis_df['Unidade Comercialização Produto']
    .astype(str)        # Garante que tudo é string
    .str.strip()        # Remove espaços antes/depois
    .str.upper()        # Coloca tudo em maiúsculas
)

#FILTRAR MÊS CORRENTE

notas_interestaduais_de_combustiveis_df = notas_interestaduais_de_combustiveis_df[
    notas_interestaduais_de_combustiveis_df['Ano/Mês Emissão'] != '202508']

# Passar usuário e senha para o conector de banco de dados
from getpass import getpass
login = "sysdba"
password = "masterkey"
fdb_path = r"C:\Users\bruno.manzatto\Desktop\Phyton\Dados"
fdb_file = "/SCANCUF_GO_2025.FDB"
fdb_file_absolut=fdb_path+fdb_file
print(fdb_file_absolut)

# String conexão #importação fdb
print(f'firebird+fdb://{login}:{password}@localhost:3050/{fdb_path}/{fdb_file}?charset=ISO8859_1')
engine = create_engine(f'firebird+fdb://{login}:{password}@localhost:3050/{fdb_path}/{fdb_file}?charset=ISO8859_1')

# criando banco de dados do scanc
conn = engine.connect()
open(fdb_file_absolut, encoding='ISO8859-1')

#TBA2MQ1D
query_TBA2MQ1D = """ SELECT DISTINCT TBA2MQ1D.*, 
    TBHEADER.razsocial
FROM TBA2MQ1D 
INNER JOIN TBHEADER ON (TBA2MQ1D.ID = TBHEADER.ID) 
                   AND (TBHEADER.MESANO = TBA2MQ1D.MESANO) 
                   AND (TBA2MQ1D.CNPJH = TBHEADER.CNPJ) 
WHERE  TBHEADER.ANEXO = '2M' 
AND TBA2MQ1D.UFH ='GO'
AND TBA2MQ1D.UF <> 'GO'
  """
TBA2MQ1D_df = pd.read_sql_query(query_TBA2MQ1D,con=conn)

# Definir condições e escolhas
condicoes = [
    TBA2MQ1D_df['produto'].isin(['DSL', 'S10']),
    TBA2MQ1D_df['produto'].isin(['GSV', 'GSL', 'GSP'])
]

escolhas = ['diesel', 'gasolina']

# Criar nova coluna
TBA2MQ1D_df['produto_classificado'] = np.select(condicoes, escolhas, default='outros')

print(TBA2MQ1D_df.head(5))

#transformar numero da nota em numero
TBA2MQ1D_df['numnf']=TBA2MQ1D_df['numnf'].astype(int)

# Criando as chaves primárias compostas
notas_interestaduais_de_combustiveis_df['chave_primaria'] = (
    notas_interestaduais_de_combustiveis_df['CNPJ - Remetente'].astype(str) + '_' +
    notas_interestaduais_de_combustiveis_df['Número NFe (D)'].astype(str) + '_' +
    notas_interestaduais_de_combustiveis_df['Categoria Produto (Analisada)'].astype(str)
)
TBA2MQ1D_df['chave_primaria'] = (
TBA2MQ1D_df['cnpjh'].astype(str) + '_' + 
TBA2MQ1D_df['numnf'].astype(str) + '_' +
TBA2MQ1D_df['produto_classificado'].astype(str) )

print(TBA2MQ1D_df)

# Unir os DataFrames com base na chave primária
notas_interestaduais_de_combustiveis_df['chave_primaria_notas'] =notas_interestaduais_de_combustiveis_df['chave_primaria']
comparacao_df = pd.merge(
    TBA2MQ1D_df,
    notas_interestaduais_de_combustiveis_df[['chave_primaria', 'chave_primaria_notas','Cód Chave Acesso NFe (D)']],
    on='chave_primaria',
    how='left'
)


# Filtrar para as notas não incluídas no SCANC
comparacao_df = comparacao_df[comparacao_df['chave_primaria_notas'].isna()]
comparacao_df = comparacao_df[comparacao_df['qtd'] > 1000]

# Corrigir a coluna 'cfop' para garantir que seja numérica
comparacao_df['cfop'] = pd.to_numeric(
    comparacao_df['cfop'].astype(str).str.replace(',', '.', regex=False),
    errors='coerce'
)

# Exibir resultado
print(comparacao_df)

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
