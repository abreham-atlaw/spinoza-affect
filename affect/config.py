from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = True
LOGGING_PID = True
LOGGING_CONSOLE = True
LOGGING_FILE_PATH = BASE_DIR / "out.log"

NETWORK_TRIES = 5

IS_LIVE = True

DEFAULT_OANDA_TOKEN = "9884f61662a4b94155571c244248a3ea-91f677817ffafc015a86414326c1e263"
DEFAULT_OANDA_TRADING_URL = "https://api-fxpractice.oanda.com/v3" if IS_LIVE else "http://127.0.0.1:8000/api"
DEFAULT_OANDA_TRADING_ACCOUNT_ID = "101-004-38460921-001"
