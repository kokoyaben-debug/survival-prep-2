import os
import json
import datetime
import math
import threading
from flask import Flask
import discord
from discord import app_commands
from discord.ext import commands, tasks

# ---------------------------------------------------------
# 1. FLASK KEEP-ALIVE SERVER (For Render 24/7 Hosting)
# ---------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Dark War Prep Bot is Alive & Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    # Disabled reloader to prevent thread collision with asyncio
    app.run(host='0.0.0.0', port=port, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()


# ---------------------------------------------------------
# 2. CONFIGURATION & STORAGE HELPERS
# ---------------------------------------------------------
CONFIG_FILE = "config.json"

def load_channel_id() -> int:
    default_id = int(os.environ.get("CHANNEL_ID", "1554020108878217247"))
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("PREP_CHANNEL_ID", default_id)
    except Exception as e:
        print(f"⚠️ Failed to load config.json: {e}")
    return default_id

def save_channel_id(channel_id: int):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"PREP_CHANNEL_ID": channel_id}, f)
    except Exception as e:
        print(f"❌ Failed to save config.json: {e}")

PREP_CHANNEL_ID = load_channel_id()
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))


# ---------------------------------------------------------
# 3. DISCORD BOT & CONSTANTS SETUP
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
    0: "00:00 - 04:00 ST",
    4: "04:00 - 08:00 ST",
    8: "08:00 - 12:00 ST",
    12: "12:00 - 16:00 ST",
    16: "16:00 - 20:00 ST",
    20: "20:00 - 00:00 ST"
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
        "**Ruby Store** — Buy Packs to obtain 1 Ruby (`+40 pts`)"
    ],
    "Hero Initiative": [
        "**Exclusive Equipment** — Consume 1 Fragment (`+600 pts`)",
        "**Prime Recruits** — Perform 1 Prime Recruitment (`+400 pts`)",
        "**Orange Hero Fragments** — Spend 1 in Star Rise (`+600 pts`)",
        "**Purple Hero Fragments** — Spend 1 in Star Rise (`+135 pts`)",
        "**Blue Hero Fragments** — Spend 1 in Star Rise (`+65 pts`)",
        "**Ruby Store** — Buy Packs to obtain 1 Ruby (`+40 pts`)"
    ],
    "Unit Training": [
        "**Training Speedups** — Use 1-min acceleration (`+5 pts`)",
        "**Unit Recruitment** — Train to get troops:",
        "  • Lv.1: `+6` | Lv.2: `+9` | Lv.3: `+13` | Lv.4: `+19` | Lv.5: `+28`",
        "  • Lv.6: `+35` | Lv.7: `+45` | Lv.8: `+57` | Lv.9: `+74` | Lv.10: `+91`",
        "**Promote Units** — Grants corresponding tier points",
        "**Ruby Store** — Buy Packs to obtain 1 Ruby (`+40 pts`)"
    ],
    "Arms Expert": [
        "**Gears** — Consume 1 Gear (`+2 pts`)",
        "**Titanium Alloy** — Consume 1 Alloy (`+180 pts`)",
        "**Design Blueprints** — Consume 1 Blueprint (`+360 pts`)",
        "**Power Cores** — Consume 1 Core (`+450 pts`)",
        "**Lucky Chests** — Open 1 Hero Equipment Chest (`+1,000 pts`)",
        "**D6 Red Equipment** — Upgrade bonus with Cores (`+600 pts`)",
        "**DX-Blueprint** — Consume 1 DX-Blueprint (`+9,000 pts`)",
        "**Ruby Store** — Buy Packs to obtain 1 Ruby (`+40 pts`)"
    ]
}


# ---------------------------------------------------------
# 4. HELPER FUNCTIONS & EMBED BUILDERS
# ---------------------------------------------------------
def get_event_at_time(dt_local: datetime.datetime):
    weekday = dt_local.weekday()
    # Floor to nearest 4-hour window
    hour_slot = (dt_local.hour // 4) * 4
    
    theme = WEEKLY_SCHEDULE.get(weekday, {}).get(hour_slot, "Survival Prep Phase")
    st_str = ST_RANGES.get(hour_slot, "00:00 - 04:00 ST")
    unix_start = int(dt_local.astimezone(datetime.timezone.utc).timestamp())
    unix_end = unix_start + 14400  # 4 hours
    return theme, st_str, unix_start, unix_end

def get_current_active_event():
    now_local = datetime.datetime.now(UTC_MINUS_2)
    current_hour_slot = (now_local.hour // 4) * 4
    slot_dt = datetime.datetime(now_local.year, now_local.month, now_local.day, current_hour_slot, 0, tzinfo=UTC_MINUS_2)
    theme, st_str, unix_start, unix_end = get_event_at_time(slot_dt)
    return theme, st_str, unix_start, unix_end

def build_two_embed_stack(theme: str, st_range: str, unix_start: int, unix_end: int, is_pre_alert: bool = False, mins_left: int = 0) -> list:
    color = PHASE_COLORS.get(theme, discord.Color.gold())
    icon = PHASE_ICONS.get(theme, "🎯")
    
    start_fmt = f""
    end_fmt = f""
    countdown_fmt = f"" if not is_pre_alert else f""

    # 1. TOP EMBED: Active Status & Time Frame
    embed_top = discord.Embed(color=color)
    
    if is_pre_alert:
        title_name = "SECRETARY OF CONSTRUCTION" if theme == "Shelter Expansion" else "SECRETARY OF SCIENCE"
        pre_alert_warning = (
            f"```diff\n"
            f"- 🔴 CAPITAL TITLE REQUIRED IN {mins_left} MINUTES!\n"
            f"+ APPLY FOR [{title_name}] AT THE CAPITAL NOW!\n"
            f"```\n"
        )
        embed_top.title = f"🚨 UPCOMING PREP: {icon} {theme.upper()}"
        embed_top.description = (
            f"{pre_alert_warning}"
            f"> **Server Time Slot:** `{st_range}`\n"
            f"> **Phase Starts:** {start_fmt} ({countdown_fmt})\n"
            f"> **Phase Ends:** {end_fmt}"
        )
    else:
        embed_top.title = f"{icon} ACTIVE PREP PHASE: {theme.upper()}"
        embed_top.description = (
            f"```yaml\n"
            f"STATUS: ACTIVE EVENT IN PROGRESS\n"
            f"SLOT  : {st_range}\n"
            f"
