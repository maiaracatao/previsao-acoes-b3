def criar_features(df, n_lags=3):
    df = df.sort_values("InfoDate").copy()
    df["OpenPriceTarget"] = df["OpenPrice"].shift(-1)
    cols_para_lag = ["OpenPrice", "ClosePrice", "HighPrice", "LowPrice", "Volume"]
    for col in cols_para_lag:
        for lag in range(1, n_lags+1):
            df[f"{col}_lag_{lag}"] = df[col].shift(lag)
    df.dropna(inplace=True)
    return df
