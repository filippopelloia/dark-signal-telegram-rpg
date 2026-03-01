import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///alien_dark_signal.db")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Game settings
TYPING_DELAY = 1.2        # seconds between messages for immersion
CHAPTER_UNLOCK_HOURS = 24 # hours between chapter unlocks
DAILY_MISSION_COOLDOWN = 86400  # 24h in seconds
STREAK_BONUS_DAYS = 7

# XP settings
XP_PER_LEVEL = 100
MAX_LEVEL = 20
STAT_POINTS_PER_LEVEL = 2

# Combat
BASE_XENOMORPH_HP = 30
PULSE_RIFLE_DAMAGE = "2d8"
MOTION_TRACKER_RANGE = 50  # meters (narrative)

SUPPORTED_LANGUAGES = ["it", "en", "es"]
DEFAULT_LANGUAGE = "en"
