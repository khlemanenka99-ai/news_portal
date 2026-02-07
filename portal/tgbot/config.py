import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

TELEGRAM_BOT_TOKEN = os.environ.get('tg_token')
ADMIN_CHAT_ID = os.environ.get('admin_id')

# Настройки
BOT_USERNAME = 'MyNewsPortal_bot'

# Состояния для FSM (Finite State Machine)
(
    WAITING_FOR_TITLE,
    WAITING_FOR_CONTENT,
    WAITING_FOR_CATEGORY,
    WAITING_FOR_PHOTO,
    WAITING_FOR_CONFIRMATION
) = range(5)