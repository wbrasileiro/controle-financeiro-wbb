import streamlit as st
import pandas as pd

with st.container():
    st.title("Analise de contratos")
    st.write("Conheça meu portfólio [Clique aqui](https://sites.google.com/view/portfolio-de-evidencias-wbb?usp=sharing)")
    st.write("---")

@st.cache_data()
def carregar_dados():
    tabela = pd.read_csv("resultados.csv")
    return tabela

with st.container():
    qtd_dias = st.selectbox("Escolha o período desejado",["5 dias", "10 dias", "20 dias", "30 dias"])
    num_dias = int(qtd_dias.replace(" dias",""))
    dados = carregar_dados()
    dados = dados[-num_dias:]

    st.line_chart(dados, x="Data", y="Contratos")

