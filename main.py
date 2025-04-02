import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from services.models import train_model, ticker_future_price, destreinar_modelo

app = FastAPI(
    title="API de Previsão de Ações B3",
    description="Esta API permite prever o preço de abertura do próximo dia para ações da B3 com base em dados históricos.",
    version="1.0.0",
    contact={"name": "Maiara Catão"}
)

@app.get("/")
def root():
    return {"status": "API de Previsão de Ações Online"}

@app.get("/prever/{ticker}")
def prever_acao(ticker: str):
    try:
        resultado = ticker_future_price(ticker.upper())
        if resultado is None:
            return JSONResponse(status_code=400, content={"erro": f"Não foi possível prever {ticker}."})
        return {"ticker": ticker.upper(), "open_price_previsto": round(resultado, 4)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/treinar/{ticker}")
def treinar_modelo(ticker: str):
    try:
        logs = train_model(ticker.upper())
        return {"ticker": ticker.upper(), "mensagem": "Modelo treinado com sucesso", "logs": logs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})

@app.get("/destreinar/{ticker}")
def deletar_modelo(ticker: str):
    try:
        mensagem = destreinar_modelo(ticker.upper())
        return {"ticker": ticker.upper(), "mensagem": mensagem}
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})
