import os
from dotenv import load_dotenv

# Load .env file for local development if it exists
load_dotenv()

# --- Core Bot Settings ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables")

TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID", 0))
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "@your_admin_contact")
PERSISTENCE_FILEPATH = "./bot_context_persistence"

# --- Database ---
# Railway provides this automatically. For local dev, you'd set it in a .env file.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables")

# --- Payment Details & Rates (Can be set in Railway's environment variables) ---
TBANK_CARD_NUMBER = os.getenv("TBANK_CARD_NUMBER", "1234 5678 9012 3456")
TBANK_CARD_HOLDER = os.getenv("TBANK_CARD_HOLDER", "Имя Фамилия")
KASPI_CARD_NUMBER = os.getenv("KASPI_CARD_NUMBER", "1234 5678 9012 3456")
ARS_ALIAS = os.getenv("ARS_ALIAS", "your.alias.here")
USDT_TRC20_ADDRESS = os.getenv("USDT_TRC20_ADDRESS", "YOUR_USDT_ADDRESS")
CRYPTO_NETWORK = os.getenv("CRYPTO_NETWORK", "TRC-20")
BINANCE_ID = os.getenv("BINANCE_ID", "123456789")

USD_TO_RUB_RATE = float(os.getenv("USD_TO_RUB_RATE", 90.0))
USD_TO_KZT_RATE = float(os.getenv("USD_TO_KZT_RATE", 450.0))
USD_TO_ARS_RATE = float(os.getenv("USD_TO_ARS_RATE", 1000.0))