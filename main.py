import os
import json
import datetime
import math
import asyncio
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands, tasks

# ---------------------------------------------------------
# 1. FLASK KEEP-ALIVE SERVER (24/7 Hosting Support)
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Dark War Prep Bot is Online & Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()


# ---------------------------------------------------------
# 2. PERSISTENT STORAGE & TIMEZONE HELPERS
# ---------------------------------------------------------
CONFIG_FILE = "config.json"
MESSAGES_FILE = "active_messages.json"
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))
KOFI_URL = "https://ko-fi.com/abenwilfredojr"

def load_config() -> dict:
    default_id = int(os.environ.get("CHANNEL_ID", "1554020108878217247"))
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load config.json: {e}")
    return {"PREP_CHANNEL_ID": default_id}

def save_config(config_data: dict):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save config.json: {e}")

def load_active_messages() -> list:
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_active_messages(msg_list: list):
    try:
        with open(MESSAGES_FILE, "w") as f:
            json.dump(msg_list, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save active messages: {e}")

config = load_config()
PREP_CHANNEL_ID = config.get("PREP_CHANNEL_ID")


# ---------------------------------------------------------
# 3. GAME DATA & CONSTANTS
# ---------------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

PHASE_COLORS = {
    "Shelter Expansion": discord.Color.from_str("#F1C40F"),  # Gold
    "Age of Science":    discord.Color.from_str("#3498DB"),  # Blue
    "Hero Initiative":   discord.Color.from_str("#9B59B6"),  # Purple
    "Unit Training":     discord.Color.from_str("#2ECC71"),  # Green
    "Arms Expert":       discord.Color.from_str("#E74C3C")   # Red
}

PHASE_ICONS = {
    "Shelter Expansion": "🏰",
    "Age of Science":    "🔬",
    "Hero Initiative":   "🦸‍♂️",
    "Unit Training":     "🪖",
    "Arms Expert":       "⚔️"
}

ST_RANGES = {
    0: "00:00 – 04:00 ST",
    4: "04:00 – 08:00 ST",
    8: "08:00 – 12:00 ST",
    12: "12:00 – 16:00 ST",
    16: "16:00 – 20:00 ST",
    20: "20:00 – 00:00 ST"
}

WEEKLY_SCHEDULE = {
    0: {0: "Shelter Expansion", 4: "Hero Initiative", 8: "Unit Training", 12: "Age of Science", 16: "Arms Expert", 20: "Shelter Expansion"},
    1: {0: "Hero Initiative", 4: "Unit Training", 8: "Age of Science", 12: "Arms Expert", 16: "Shelter Expansion", 20: "Hero Initiative"},
    2: {0: "Unit Training", 4: "Age of Science", 8: "Arms Expert", 12: "Shelter Expansion", 16: "Hero Initiative", 20: "Unit Training"},
    3: {0: "Age of Science", 4: "Arms Expert", 8: "Shelter Expansion", 12: "Hero Initiative", 16: "Unit Training", 20: "Age of Science"},
    4: {0: "Arms Expert", 4: "Shelter Expansion", 8: "Hero Initiative", 12: "Unit Training", 16: "Age of Science", 20: "Arms Expert"},
    5: {0: "Shelter Expansion", 4: "Hero Initiative", 8: "Unit Training", 12: "Age of Science", 16: "Arms Expert", 20: "Shelter Expansion"},
    6: {0: "Hero Initiative", 4: "Unit Training", 8: "Age of Science", 12: "Arms Expert", 16: "Shelter Expansion", 20: "Hero Initiative"}
}

DAYS_MAP = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}

TASK_DETAILS = {
    "Shelter Expansion": [
        "**Precision Parts** — Use 1 unit in building upgrades (`+300 pts`)",
        "**Construction Speedups** — Use 1-min acceleration (`+5 pts`)",
        "**Structure Power** — Increase Structure CP by 100 pts (`+10 pts`)",
        "**Ruby Store** — Buy Packs to obtain 1 Ruby (`+40 pts`)"
    ],
    "Age of Science": [
        "**Wisdom Medals** — Consume 1 Medal (`+5 pts`)",
        "**Research Speedups** — Use 1-min acceleration (`+5 pts`)",
        "**Tech Power** — Increase Tech CP by 100 pts (`+10 pts`)",
