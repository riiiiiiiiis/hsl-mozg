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

# --- Referral System Configuration ---
REFERRAL_BOT_URL = os.getenv("REFERRAL_BOT_URL", "https://t.me/")
REFERRAL_START_PARAMETER = os.getenv("REFERRAL_START_PARAMETER", "ref_")
REFERRAL_CODE_LENGTH = int(os.getenv("REFERRAL_CODE_LENGTH", 8))
REFERRAL_CODE_CHARS = os.getenv("REFERRAL_CODE_CHARS", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

# Available discount percentages and their default activation limits
REFERRAL_DISCOUNTS = {
    10: {"default_activations": 50, "description": "10% скидка"},
    20: {"default_activations": 20, "description": "20% скидка"},
    30: {"default_activations": 10, "description": "30% скидка"},
    50: {"default_activations": 5, "description": "50% скидка"},
    100: {"default_activations": 1, "description": "100% скидка (бесплатно)"},
}

# Admin IDs who can create referral codes (empty = any admin)
REFERRAL_ADMIN_IDS = []
if os.getenv("REFERRAL_ADMIN_IDS"):
    REFERRAL_ADMIN_IDS = [int(id.strip()) for id in os.getenv("REFERRAL_ADMIN_IDS").split(",")]

# Database table names for referral system
REFERRAL_TABLE_NAME = "referral_coupons"
REFERRAL_USAGE_TABLE_NAME = "referral_usage"