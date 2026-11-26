"""הגדרות הפרויקט במקום אחד. כל מודול אחר מייבא מכאן, ולא קורא ל-os.getenv בעצמו."""
import os
from pathlib import Path

import truststore
from dotenv import load_dotenv

# חיבורי HTTPS מהמחשב המארח (OpenAI, LangSmith, GitHub) ישתמשו במאגר התעודות של Windows,
# שבו מותקנת התעודה של NetFree. בלי השורה הזו – שגיאת CERTIFICATE_VERIFY_FAILED.
truststore.inject_into_ssl()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- מודל השפה ---
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

# --- הקונטיינר ---
DEFAULT_PYTHON_VERSION = "3.12"
SUPPORTED_PYTHON = ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")  # הגרסאות שהסוכן רשאי לעבור אליהן
RUN_CHECK_TIMEOUT = 60                     # כמה שניות מחכים שהפרויקט יסתיים או יענה ב-HTTP
CONTAINER_USER = "runner"                  # פקודות רצות כמשתמש רגיל, לא root
WORKSPACE = "/workspace"
REPO_DIR = f"{WORKSPACE}/repo"             # כאן נמצא הפרויקט בתוך הקונטיינר
VENV_DIR = f"{WORKSPACE}/.venv"            # הסביבה הווירטואלית שאליה מותקנות החבילות
SECRETS_DIR = f"{WORKSPACE}/.secrets.d"    # סודות שהמשתמש סיפק: קובץ לכל משתנה, מחוץ לפרויקט ומחוץ ל-State
PIP_CACHE_VOLUME = "reporunner-pip-cache"  # volume משותף לכל הקונטיינרים – חבילה יורדת פעם אחת
MEMORY_LIMIT = "2g"
CPU_LIMIT = 2

# --- הרצת פקודות ---
COMMAND_TIMEOUT_SEC = 300
OUTPUT_LIMIT_CHARS = 4000                  # כמה מהפלט נשמר – פלט ארוך מדי מבזבז טוקנים של המודל

# --- הלולאה ---
MAX_ATTEMPTS = 8          # כמה פעמים מנסים לתקן לפני שעוצרים
ATTEMPTS_GRANT = 4        # כמה ניסיונות נוספים אדם יכול להוסיף כשהמגבלה נגמרת
CHECKPOINT_DB = PROJECT_ROOT / ".reporunner" / "checkpoints.sqlite"  # כאן נשמר מצב הריצה בין הפעלות
RUNS_DIR = PROJECT_ROOT / ".reporunner" / "runs"                      # כאן נשמרים התוצרים (Dockerfile, דוח) לכל ריצה
RECURSION_LIMIT = 250     # ברירת המחדל של LangGraph היא 25 צעדים, וריצה עם כמה תיקונים חורגת ממנה בקלות
MAX_TOOL_CALLS = 5      # כמה קריאות לכלי חקירה מותרות באבחון אחד
ERROR_EXCERPT_CHARS = 600 # כמה מהשגיאה נשמר בהיסטוריית הניסיונות

# --- בדיקת פקודות ותצוגה ---
SMOKE_TIMEOUT_SEC = 8                      # כמה שניות מריצים כל פקודת משנה בבדיקה קצרה
DISPLAY = ":99"                            # המסך הווירטואלי (Xvfb) בקונטיינר
SCREEN_SIZE = "1024x768x24"
PREVIEW_WEB_PORT = 7000                    # פורט בקונטיינר שמועבר מהמארח: שרת של הפרויקט (דרך מעביר פנימי)
VNC_WEB_PORT = 6080                        # פורט בקונטיינר שמועבר מהמארח: noVNC, תצוגת החלון בדפדפן
PREVIEW_TTL_MIN = 30                       # אחרי כמה דקות קונטיינר עם תצוגה חיה נסגר לבד
RECORD_SECONDS = 10                        # אורך ההקלטה
GUI_CHECK_TIMEOUT_SEC = 12                 # כמה שניות מחכים שפרויקט עם חלון יסתיים לפני שבודקים אם הוא פתח חלון
REPEAT_RETRIES = 2                         # v2: כמה פעמים מבקשים מהמודל הצעה אחרת כשהוא חוזר על תיקון שנכשל
WINDOW_WAIT_SEC = 4                        # כמה שניות ממתינים לחלון להיפתח לפני שבודקים אם הוא קיים
