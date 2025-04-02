import mysql.connector
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from config import DB_CONFIG
from sqlalchemy.engine.url import URL

def atualizar_dados_ticker(ticker: str):
    logs = []
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(InfoDate) FROM historico_acoes WHERE Ticker = %s", (ticker,))
        row = cursor.fetchone()
        data_mais_recente = row[0]

        if data_mais_recente is None:
            data_inicio = (datetime.today() - timedelta(days=5*365)).strftime('%Y-%m-%d')
            logs.append(f"Ticker '{ticker}' sem dados. Baixando últimos 5 anos.")
        else:
            data_inicio = (data_mais_recente + timedelta(days=1)).strftime('%Y-%m-%d')
            logs.append(f"Ticker '{ticker}' com dados até {data_mais_recente}. Baixando desde {data_inicio}.")

        data_fim = datetime.today().strftime('%Y-%m-%d')
        if data_inicio > data_fim:
            logs.append(f"Nenhum novo dado para inserir em {ticker}.")
            return logs

        yf_ticker = ticker + ".SA"
        df = yf.download(yf_ticker, start=data_inicio, end=data_fim, interval="1d", progress=False)
        if df.empty:
            logs.append(f"Nenhum dado retornado do yfinance para {ticker}.")
            return logs

        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO historico_acoes 
                    (InfoDate, Ticker, OpenPrice, ClosePrice, HighPrice, LowPrice, Volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["Date"].date(), ticker,
                float(row["Open"]) if not pd.isna(row["Open"]) else None,
                float(row["Close"]) if not pd.isna(row["Close"]) else None,
                float(row["High"]) if not pd.isna(row["High"]) else None,
                float(row["Low"]) if not pd.isna(row["Low"]) else None,
                float(row["Volume"]) if not pd.isna(row["Volume"]) else None
            ))

        conn.commit()
        logs.append(f"Dados atualizados para {ticker} de {data_inicio} até {data_fim}.")
    except Exception as e:
        logs.append(f"Erro ao atualizar dados: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return logs

def carregar_dados(ticker: str):
    db_url = URL.create(
        drivername="mysql+mysqlconnector",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        database=DB_CONFIG["database"]
    )
    engine = create_engine(db_url)
    query = f"""
        SELECT InfoDate, Ticker, OpenPrice, ClosePrice, HighPrice, LowPrice, Volume
        FROM historico_acoes
        WHERE Ticker = '{ticker}'
        ORDER BY InfoDate
    """
    df = pd.read_sql(query, engine)
    df["InfoDate"] = pd.to_datetime(df["InfoDate"])
    for col in ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume"]:
        df[col] = df[col].astype(float)
    return df
