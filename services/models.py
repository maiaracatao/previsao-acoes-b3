import os
import joblib
import pandas as pd
from datetime import datetime
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sqlalchemy import create_engine

from .data import atualizar_dados_ticker, carregar_dados
from .features import criar_features
from config import DB_CONFIG
from sqlalchemy.engine.url import URL

def train_model(ticker, n_lags=3):
    models_dir = "models"

    os.makedirs(models_dir, exist_ok=True)

    logs = atualizar_dados_ticker(ticker)

    df = carregar_dados(ticker)
    if df.empty:
        raise Exception(f"Nenhum dado para {ticker}")
    
    df_lags = criar_features(df, n_lags)
    if df_lags.empty:
        raise Exception(f"Dados insuficientes para {ticker} após criação de lags")

    df_modelo = df_lags.drop(["InfoDate", "Ticker"], axis=1)
    X = df_modelo.drop("OpenPriceTarget", axis=1)
    y = df_modelo["OpenPriceTarget"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)
    
    modelos = {
        "LinearRegression": LinearRegression(),
        "DecisionTree": DecisionTreeRegressor(random_state=42),
        "RandomForest": RandomForestRegressor(random_state=42),
        "GradientBoosting": GradientBoostingRegressor(random_state=42),
    }

    melhor_mse = float("inf")
    melhor_pipeline = None
    melhor_nome = ""

    for nome, modelo in modelos.items():
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", modelo)
        ])
        pipe.fit(X_train, y_train)
        pred = pipe.predict(X_test)
        mse = mean_squared_error(y_test, pred)
        r2 = r2_score(y_test, pred)
        logs.append(f"{nome}: MSE={mse:.4f}, R²={r2:.4f}")
        if mse < melhor_mse:
            melhor_mse = mse
            melhor_pipeline = pipe
            melhor_nome = nome

    # Salva modelo
    model_path = f"models/{ticker}_model.pkl"
    joblib.dump(melhor_pipeline, model_path)
    logs.append(f"Melhor modelo: {melhor_nome} - salvo em {model_path}")

    # Atualiza no banco
    import mysql.connector
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    sql = """
    INSERT INTO ticker_model (ticker, model_path, updated_at)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE model_path=VALUES(model_path), updated_at=VALUES(updated_at)
    """
    cursor.execute(sql, (ticker, model_path, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()

    return logs

def destreinar_modelo(ticker: str) -> str:
    import mysql.connector

    ticker = ticker.upper()
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Buscar o caminho do modelo
    cursor.execute("SELECT model_path FROM ticker_model WHERE ticker = %s", (ticker,))
    row = cursor.fetchone()

    if not row:
        cursor.close()
        conn.close()
        raise Exception(f"Modelo para {ticker} não encontrado no banco.")

    model_path = row["model_path"]

    # Remover arquivo do modelo
    if os.path.exists(model_path):
        os.remove(model_path)
    else:
        cursor.close()
        conn.close()
        raise Exception(f"Arquivo {model_path} não encontrado.")

    # Remover o modelo do banco
    cursor.execute("DELETE FROM ticker_model WHERE ticker = %s", (ticker,))
    
    # Remover os dados históricos
    cursor.execute("DELETE FROM historico_acoes WHERE ticker = %s", (ticker,))
    
    conn.commit()
    cursor.close()
    conn.close()

    return f"Modelo e dados históricos para {ticker} removidos com sucesso."

def ticker_future_price(ticker, n_lags=3):
    print("Iniciando ticker_future_price")
    logs = atualizar_dados_ticker(ticker)
    import mysql.connector
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT model_path FROM ticker_model WHERE ticker = %s", (ticker,))
    row = cursor.fetchone()
    if not row:
        logs.append(f"Modelo não encontrado. Treinando modelo...")
        train_model(ticker, n_lags)
        cursor.execute("SELECT model_path FROM ticker_model WHERE ticker = %s", (ticker,))
        row = cursor.fetchone()
        if not row:
            raise Exception(f"Aviso: Modelo ainda não disponível. Tente novamente em 1 min.")

    model_path = row["model_path"]
    cursor.close()
    conn.close()

    if not os.path.exists(model_path):
        raise Exception(f"Arquivo de modelo {model_path} não encontrado.")

    model = joblib.load(model_path)

    db_url = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"]
    )
    engine = create_engine(db_url)

    query = f"""
        SELECT InfoDate, OpenPrice, ClosePrice, HighPrice, LowPrice, Volume
        FROM historico_acoes
        WHERE Ticker = '{ticker}'
        ORDER BY InfoDate DESC
        LIMIT {n_lags + 1}
    """
    df = pd.read_sql(query, engine).sort_values("InfoDate").reset_index(drop=True)
    if df.shape[0] <= n_lags:
        raise Exception("Dados insuficientes para previsão.")

    for col in ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume"]:
        for lag in range(1, n_lags+1):
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)

    df.dropna(inplace=True)
    df = df.drop(columns=["InfoDate"])

    required_cols = model["scaler"].feature_names_in_
    df = df[required_cols]

    pred = model.predict(df)
    return float(pred[0])