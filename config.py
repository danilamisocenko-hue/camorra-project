import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TRONGRID_KEY = os.getenv("TRONGRID_KEY")
CHECK_INTERVAL = 60  # секунд
NOTIFICATION_THRESHOLD = 1500.0 #