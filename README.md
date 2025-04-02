# 📈 API de Previsão de Abertura de Ações da B3

Este projeto fornece uma **API com FastAPI** e um **Dashboard em Streamlit** para prever o **preço de abertura do próximo dia** de ações da B3, utilizando modelos de machine learning treinados com dados históricos via **Yahoo Finance (yFinance)**.  
Os dados são armazenados em **MySQL**, os modelos são versionados e salvos como arquivos `.pkl`.

---

## 🚀 Funcionalidades

- 📊 Coleta automática de dados históricos via `yfinance`
- 🛠️ Engenharia de features com lags
- 🧠 Treinamento de múltiplos modelos (Regressão Linear, Árvore, Random Forest, Gradient Boosting)
- 🏆 Escolha automática do melhor modelo baseado em MSE
- 📁 Armazenamento e versionamento dos modelos em `.pkl`
- 🗃️ Registro de metadados em banco de dados
- 🔮 API REST para prever, treinar ou remover modelos
- 📺 Dashboard visual em Streamlit para consulta em tempo real

---

## 🧱 Estrutura do Projeto

```
📁 projeto_raiz/
├── services/              # Lógica do sistema
│   ├── data.py            # Coleta e ingestão de dados (MySQL + yFinance)
│   ├── features.py        # Engenharia de features (lags)
│   └── models.py          # Treinamento, previsão, salvamento e exclusão de modelos
│
├── models/                # Modelos .pkl salvos por ticker
│   └── PETR4_model.pkl
│
├── main.py                # FastAPI com endpoints /prever, /treinar, /destreinar
├── dashboard.py           # Interface Streamlit para usuários finais
├── config.py              # Carrega variáveis do .env
├── .env                   # Configurações sensíveis (.gitignore)
├── requirements.txt       # Dependências do projeto
└── .gitignore
```

---

## ⚙️ Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/maiaracatao/previsao-acoes-b3.git
cd previsao-acoes-b3
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate   # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o `.env`

Crie um arquivo `.env` na raiz com o seguinte conteúdo:

```env
DB_HOST=XXX.XXX.XXX.XXX
DB_USER=usuário
DB_PASSWORD=sua_senha_aqui
DB_NAME=b3_acoes
```

---

## ▶️ Execução

### 🧠 Iniciar a API (FastAPI)

```bash
uvicorn main:app --reload
```

Acesse a documentação interativa em: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 📊 Iniciar o Dashboard (Streamlit)

```bash
streamlit run dashboard.py
```

---

## 🔗 Endpoints da API

| Método | Rota                | Descrição                                      |
|--------|---------------------|-----------------------------------------------|
| GET    | `/`                 | Verifica se a API está online                 |
| GET    | `/prever/{ticker}`  | Retorna a previsão de abertura para o ticker  |
| GET    | `/treinar/{ticker}` | Treina e salva o melhor modelo para o ticker  |
| GET    | `/destreinar/{ticker}` | Remove modelo e dados do ticker           |

---

## 🛢️ Estrutura do Banco de Dados (MySQL)

### 📄 `historico_acoes`

Armazena os dados históricos coletados para cada ação.

| Campo       | Tipo         | Descrição                        |
|-------------|--------------|----------------------------------|
| `id`        | `int`        | Chave primária (auto incremento)|
| `InfoDate`  | `date`       | Data da informação               |
| `Ticker`    | `varchar(20)`| Código da ação (ex: PETR4)       |
| `OpenPrice` | `float`      | Preço de abertura                |
| `ClosePrice`| `float`      | Preço de fechamento              |
| `HighPrice` | `float`      | Maior valor do dia               |
| `LowPrice`  | `float`      | Menor valor do dia               |
| `Volume`    | `float`      | Volume negociado                 |

```sql
CREATE TABLE historico_acoes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  InfoDate DATE,
  Ticker VARCHAR(20),
  OpenPrice FLOAT,
  ClosePrice FLOAT,
  HighPrice FLOAT,
  LowPrice FLOAT,
  Volume FLOAT
);
```

---

### 📄 `ticker_model`

Armazena o caminho do modelo treinado e sua última atualização para cada ação.

| Campo        | Tipo           | Descrição                          |
|--------------|----------------|------------------------------------|
| `ticker`     | `varchar(20)`  | Código da ação (chave primária)    |
| `model_path` | `varchar(255)` | Caminho do arquivo `.pkl` do modelo|
| `updated_at` | `datetime`     | Data da última atualização         |

```sql
CREATE TABLE ticker_model (
  ticker VARCHAR(20) PRIMARY KEY,
  model_path VARCHAR(255),
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 📌 Exemplo de uso com `requests` em Python

```python
import requests

resp = requests.get("http://localhost:8000/prever/PETR4")
print(resp.json())
```

---

## 📚 Requisitos

- Python 3.8+
- MySQL Server
- Conexão com a internet (para coletar dados do Yahoo Finance)

---

## 👨‍💻 Autor

**Maiara Catão**  
📧 Contato: [LinkedIn](https://www.linkedin.com/in/maiara-lopes-cat%C3%A3o-24315471) ou via GitHub

---

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
