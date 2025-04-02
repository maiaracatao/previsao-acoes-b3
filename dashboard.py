import streamlit as st
import requests
import pandas as pd

# URL base da sua API
API_URL = "http://127.0.0.1:8000/prever"

# Tickers para exibir
tickers = ['MGLU3', 'PETR4', 'ABEV3', 'ITUB4']

st.set_page_config(page_title="Dashboard de Previsão de Ações", layout="centered")
st.title("Dashboard de Previsão de Abertura das Ações")
st.markdown("Consulta em tempo real à API para prever o preço de abertura do próximo dia para cada ativo.")

# Função para consultar a API
def consultar_previsao(ticker):
    try:
        response = requests.get(f"{API_URL}/{ticker}")
        if response.status_code == 200:
            return response.json()
        else:
            return {"ticker": ticker, "erro": response.json().get("erro", "Erro desconhecido")}
    except Exception as e:
        return {"ticker": ticker, "erro": str(e)}

# Consulta os dados
dados = [consultar_previsao(ticker) for ticker in tickers]

# Converte em DataFrame
df = pd.DataFrame(dados)

# Exibe erros se houver
if "erro" in df.columns:
    for _, row in df[df["erro"].notnull()].iterrows():
        st.error(f"Erro ao consultar {row['ticker']}: {row['erro']}")

# Exibe tabela com resultados válidos
df_validos = df.dropna(subset=["open_price_previsto"])
if not df_validos.empty:
    # Renomeia colunas e formata o valor
    df_formatado = df_validos.rename(columns={
        "ticker": "Ação",
        "open_price_previsto": "Valor Previsto(R$)"
    })
    df_formatado["Valor Previsto(R$)"] = df_formatado["Valor Previsto(R$)"].map(lambda x: f"{x:,.2f}".replace(".", ","))
    df_formatado = df_formatado.set_index("Ação")

    st.subheader("Tabela de Previsões")
    st.dataframe(df_formatado)

    st.subheader("Gráfico de Previsões")
    # Para o gráfico, precisamos dos valores em float novamente
    df_grafico = df_validos.set_index("ticker")
    st.bar_chart(df_grafico["open_price_previsto"])
else:
    st.warning("Nenhum dado de previsão disponível no momento.")

