from pyrogram import Client
from config import Config
from datetime import datetime
import logging
import time
import pytz
from database import init_db

print("Hora atual UTC:", datetime.now(pytz.utc))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Sincronização de tempo
time.sleep(3)

app = Client(
    "bot_divulgacao",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="handlers")
)

logging.info("Iniciando o bot...")

# Inicializa o banco de dados aqui
init_db()
logging.info("Banco de dados inicializado com sucesso!")

app.run()