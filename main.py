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
# 2. MULTI-SERVER PERSISTENT STORAGE
# ---------------------------------------------------------
CONFIG_FILE = "config.json"
MESSAGES_FILE = "active_messages.json"
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))
KOFI_URL = "https://ko-fi.com/abenwilfredojr"

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                if "guild_channels" in data:
                    return data
        except Exception as e:
            print(f"⚠️ Failed to load config.json: {e}")
    return {"guild_channels": {}}

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
        "**Unit Recruitment** — Train troops:",
        "  └ `Lv.1: +6` | `Lv.2: +9` | `Lv.3: +13` | `Lv.4: +19` | `Lv.5: +28`",
        "  └ `Lv.6: +35` | `Lv.7: +45` | `Lv.8: +57` | `Lv.9: +74` | `Lv.10: +91`",
        "**Promote Units** — Grants tier difference points",
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
# 4. DISCORD UI BUTTON VIEW
# ---------------------------------------------------------
def get_support_view(bot_id: int) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    invite_url = f"https://discord.com/oauth2/authorize?client_id={bot_id}&permissions=274878024704&scope=bot%20applications.commands"
    
    view.add_item(discord.ui.Button(label="Add to Server", url=invite_url, style=discord.ButtonStyle.link, emoji="➕"))
    view.add_item(discord.ui.Button(label="Support on Ko-fi", url=KOFI_URL, style=discord.ButtonStyle.link, emoji="☕"))
    return view

async def fetch_channel_safe(channel_id: int) -> discord.TextChannel | None:
    channel = bot.get_channel(channel_id)
    if not channel:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            return None
    return channel


# ---------------------------------------------------------
# 5. EVENT CALCULATION & EMBED BUILDERS
# ---------------------------------------------------------
def get_event_at_time(dt_local: datetime.datetime):
    weekday = dt_local.weekday()
    hour_slot = (dt_local.hour // 4) * 4
    theme = WEEKLY_SCHEDULE.get(weekday, {}).get(hour_slot, "Survival Prep Phase")
    st_str = ST_RANGES.get(hour_slot, "00:00 – 04:00 ST")
    
    start_dt = datetime.datetime(dt_local.year, dt_local.month, dt_local.day, hour_slot, 0, tzinfo=UTC_MINUS_2)
    unix_start = int(start_dt.astimezone(datetime.timezone.utc).timestamp())
    unix_end = unix_start + 14400
    return theme, st_str, unix_start, unix_end

def get_current_active_event():
    now_local = datetime.datetime.now(UTC_MINUS_2)
    return get_event_at_time(now_local)

def build_two_embed_stack(theme: str, st_range: str, unix_start: int, unix_end: int, is_pre_alert: bool = False, mins_left: int = 0) -> list:
    color = PHASE_COLORS.get(theme, discord.Color.gold())
    icon = PHASE_ICONS.get(theme, "🎯")
    
    start_fmt = f"<t:{unix_start}:t>"
    end_fmt = f"<t:{unix_end}:t>"
    countdown_fmt = f"<t:{unix_start}:R>" if is_pre_alert else f"<t:{unix_end}:R>"

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
            f"> 🕒 **Slot:** `{st_range}`\n"
            f"> ⏱️ **Starts:** {start_fmt} ({countdown_fmt})\n"
            f"> 🏁 **Ends:** {end_fmt}"
        )
    else:
        embed_top.title = f"{icon} ACTIVE PREP PHASE: {theme.upper()}"
        embed_top.description = (
            f"```yaml\n"
            f"STATUS : LIVE IN PROGRESS\n"
            f"SLOT   : {st_range}\n"
            f"```\n"
            f"> ⏱️ **Time Window:** {start_fmt} ➔ {end_fmt}\n"
            f"> ⏳ **Phase Ends:** {countdown_fmt}"
        )
        
    embed_top.set_footer(text="🌐 Dark War Survival • Timestamps auto-convert to your local device time")

    embed_bottom = discord.Embed(
        title=f"📋 SCORING OBJECTIVES — {theme}",
        color=color
    )
    
    tasks = TASK_DETAILS.get(theme, ["Complete event tasks to gain points!"])
    task_list_str = "\n".join([f"• {item}" if not item.startswith("  ") else item for item in tasks])
    embed_bottom.description = f"Maximized point sources for this 4-hour window:\n\n{task_list_str}"
    embed_bottom.set_footer(text="💡 Tip: Apply capital titles before claiming completed achievements.")

    return [embed_top, embed_bottom]


# ---------------------------------------------------------
# 6. MULTI-SERVER AUTOMATED LOOPS & CLEANUP
# ---------------------------------------------------------
async def auto_clean_expired_alerts():
    active_msgs = load_active_messages()
    if not active_msgs:
        return

    now_ts = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    updated_list = []

    for msg_data in active_msgs:
        if now_ts >= msg_data["expiry_ts"]:
            channel = await fetch_channel_safe(msg_data["channel_id"])
            if channel:
                try:
                    msg = await channel.fetch_message(msg_data["message_id"])
                    await msg.delete()
                    print(f"🧹 Cleaned up expired alert {msg_data['message_id']} in channel {msg_data['channel_id']}")
                except Exception as e:
                    print(f"⚠️ Could not delete alert {msg_data['message_id']}: {e}")
        else:
            updated_list.append(msg_data)

    save_active_messages(updated_list)

@tasks.loop(minutes=1)
async def schedule_check_loop():
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        await auto_clean_expired_alerts()

        guild_channels = config.get("guild_channels", {})
        if not guild_channels:
            return

        bot_id = bot.user.id if bot.user else 0

        for guild_id_str, channel_id in guild_channels.items():
            channel = await fetch_channel_safe(channel_id)
            if not channel:
                continue

            for mins in [10, 5]:
                target_dt = now_local + datetime.timedelta(minutes=mins)
                if target_dt.minute == 0 and target_dt.hour in [0, 4, 8, 12, 16, 20]:
                    theme, st_str, unix_start, unix_end = get_event_at_time(target_dt)
                    if theme in ["Shelter Expansion", "Age of Science"]:
                        embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=True, mins_left=mins)
                        view = get_support_view(bot_id)
                        await channel.send(content=f"@everyone 👑 **{mins}-MINUTE CAPITAL TITLE ALERT!**", embeds=embeds, view=view)

            if now_local.minute == 0 and now_local.hour in [0, 4, 8, 12, 16, 20]:
                theme, st_str, unix_start, unix_end = get_event_at_time(now_local)
                embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=False)
                view = get_support_view(bot_id)
                sent_msg = await channel.send(content=f"@everyone 🔥 **PREP PHASE LIVE: {theme.upper()} IS NOW ACTIVE!**", embeds=embeds, view=view)
                
                active_list = load_active_messages()
                active_list.append({
                    "message_id": sent_msg.id,
                    "channel_id": channel.id,
                    "expiry_ts": unix_end
                })
                save_active_messages(active_list)

    except Exception as e:
        print(f"❌ Error in schedule_check_loop: {e}")

@schedule_check_loop.before_loop
async def before_schedule_loop():
    await bot.wait_until_ready()


# ---------------------------------------------------------
# 7. DISCORD SLASH COMMANDS
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"📡 Synced {len(synced)} slash command(s) globally across {len(bot.guilds)} server(s).")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")
        
    if not schedule_check_loop.is_running():
        schedule_check_loop.start()

# Slash Command: /active_prep
@bot.tree.command(name="active_prep", description="View the currently active prep phase, remaining time, and tasks")
async def active_prep_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    theme, st_str, unix_start, unix_end = get_current_active_event()
    embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=False)
    view = get_support_view(bot.user.id)
    await interaction.followup.send(content="⚡ **CURRENT ACTIVE EVENT STATUS:**", embeds=embeds, view=view)

# Slash Command: /next
@bot.tree.command(name="next", description="Show full day schedule with arrow pointing to upcoming/active phase")
async def next_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    now_local = datetime.datetime.now(UTC_MINUS_2)
    cycle_hours = [0, 4, 8, 12, 16, 20]
    current_hour = now_local.hour
    
    next_hour = next((h for h in cycle_hours if h > current_hour), cycle_hours[0])
    target_date = now_local + datetime.timedelta(days=1) if next_hour <= current_hour else now_local

    weekday_idx = target_date.weekday()
    day_name = DAYS_MAP[weekday_idx]
    
    next_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, next_hour, 0, tzinfo=UTC_MINUS_2)
    next_theme, _, next_start_ts, _ = get_event_at_time(next_dt)

    schedule_lines = []
    for h in cycle_hours:
        slot_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, h, 0, tzinfo=UTC_MINUS_2)
        start_ts = int(slot_dt.astimezone(datetime.timezone.utc).timestamp())
        end_ts = start_ts + 14400
        theme = WEEKLY_SCHEDULE[weekday_idx][h]
        icon = PHASE_ICONS.get(theme, "🎯")
        
        time_str = f"<t:{start_ts}:t>–<t:{end_ts}:t>"
        
        if h == next_hour and target_date.date() == next_dt.date():
            schedule_lines.append(f"▶ **{time_str}** — **{icon} {theme}** *(UPCOMING)*")
        elif h <= current_hour and target_date.date() == now_local.date() and (current_hour - h) < 4:
            schedule_lines.append(f"⚡ **{time_str}** — **{icon} {theme}** *(ACTIVE NOW)*")
        else:
            schedule_lines.append(f"• `{time_str}` — {icon} {theme}")

    schedule_block = "\n".join(schedule_lines)
    
    embed = discord.Embed(
        title=f"📅 UPCOMING SCHEDULE — {day_name.upper()}",
        description=(
            f"**Next Phase:** {PHASE_ICONS.get(next_theme, '🎯')} **{next_theme}**\n"
            f"**Countdown:** Phase starts <t:{next_start_ts}:R>\n\n"
            f"### 🗓️ Day Schedule Overview:\n{schedule_block}"
        ),
        color=PHASE_COLORS.get(next_theme, discord.Color.blue())
    )
    embed.set_footer(text="🌐 Dark War Survival
