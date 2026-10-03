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
    app.run(host='0.0.0.0', port=port)

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

ST_RANGES = {
    0: "00:00-04:00 ST",
    4: "04:00-08:00 ST",
    8: "08:00-12:00 ST",
    12: "12:00-16:00 ST",
    16: "16:00-20:00 ST",
    20: "20:00-00:00 ST"
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
        "Use 1 Precision Parts in building upgrades: +300 pts",
        "Use any 1-min acceleration in construction: +5 pts",
        "Increase Structure CP by 100 Points: +10 pts",
        "Buy Packs to Get 1 Rubies: +40 pts"
    ],
    "Age of Science": [
        "Consume 1 Wisdom Medals: +5 pts",
        "Use any 1-min acceleration in research: +5 pts",
        "Increase Tech CP by 100 Points: +10 pts",
        "Buy Packs to Get 1 Rubies: +40 pts"
    ],
    "Hero Initiative": [
        "Every 1 Exclusive Equipment Fragments consumed: +600 pts",
        "Perform 1 Prime Recruits: +400 pts",
        "Every 1 Orange hero fragments spent in Star Rise: +600 pts",
        "Every 1 Purple hero fragments spent in Star Rise: +135 pts",
        "Every 1 Blue hero fragments spent in Star Rise: +65 pts",
        "Buy Packs to Get 1 Rubies: +40 pts"
    ],
    "Unit Training": [
        "Use any 1-min acceleration in unit training & promotion: +5 pts",
        "Train to get 1 Lv.1 Unit: +6 pts",
        "Train to get 1 Lv.2 Unit: +9 pts",
        "Train to get 1 Lv.3 Unit: +13 pts",
        "Train to get 1 Lv.4 Unit: +19 pts",
        "Train to get 1 Lv.5 Unit: +28 pts",
        "Train to get 1 Lv.6 Unit: +35 pts",
        "Train to get 1 Lv.7 Unit: +45 pts",
        "Train to get 1 Lv.8 Unit: +57 pts",
        "Train to get 1 Lv.9 Unit: +74 pts",
        "Train to get 1 Lv.10 Unit: +91 pts",
        "Promote Units: +Corresponding points",
        "Buy Packs to Get 1 Rubies: +40 pts"
    ],
    "Arms Expert": [
        "Use 1 Gears: +2 pts",
        "Consume 1 Titanium Alloy: +180 pts",
        "Consume 1 design blueprints: +360 pts",
        "Consume 1 Power Cores: +450 pts",
        "Open 1 Hero Equipment Lucky Chests: +1,000 pts",
        "Using Power Cores in D6 Red Equipment upgrade grants bonus points: +600 pts",
        "Consume 1 DX-Blueprint: +9,000 pts",
        "Buy Packs to Get 1 Rubies: +40 pts"
    ]
}


# ---------------------------------------------------------
# 4. HELPER FUNCTIONS & EMBED BUILDERS
# ---------------------------------------------------------
def get_event_at_time(dt_local: datetime.datetime):
    weekday = dt_local.weekday()
    hour = dt_local.hour
    theme = WEEKLY_SCHEDULE.get(weekday, {}).get(hour, "Survival Prep Phase")
    st_str = ST_RANGES.get(hour, "00:00-04:00 ST")
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
    color = PHASE_COLORS.get(theme, discord.Color.orange())
    
    start_fmt = f""
    end_fmt = f""
    countdown_fmt = f"" if not is_pre_alert else f""

    # 1. TOP EMBED: Active Task Box
    embed_top = discord.Embed(title="Active task", color=color)
    
    pre_alert_warning = ""
    if is_pre_alert:
        title_name = "SECRETARY OF CONSTRUCTION" if theme == "Shelter Expansion" else "SECRETARY OF SCIENCE"
        pre_alert_warning = f"```diff\n- 🔴 CAPITAL TITLE REQUIRED IN {mins_left} MINS!\n+ APPLY FOR {title_name} AT THE CAPITAL NOW!\n```\n"

    top_code_box = f"```yaml\n► ACTIVE TASK\n\n{theme}\n{st_range}\n```"
    status_line = f"Starts {start_fmt} · Ends {end_fmt}" if not is_pre_alert else f"Phase Starts {countdown_fmt} ({start_fmt})"
    time_line = f"Ends {countdown_fmt}" if not is_pre_alert else f"Ends at {end_fmt}"
    
    embed_top.description = f"{pre_alert_warning}{top_code_box}\n{status_line}\n{time_line}"
    embed_top.set_footer(text="Server Time (ST) · times also show in your local timezone")

    # 2. BOTTOM EMBED: Event Details Box
    embed_bottom = discord.Embed(title="Event details", color=color)
    tasks = TASK_DETAILS.get(theme, ["Complete tasks to gain points!"])
    
    details_text = f"```ansi\n\u001b[35m{theme} — event details\033[0m\n\n"
    for item in tasks:
        details_text += f"\u001b[35m• {item}\033[0m\n"
    details_text += "```"
    
    embed_bottom.description = details_text
    embed_bottom.set_footer(text="Scoring tasks for this slot")

    return [embed_top, embed_bottom]


# ---------------------------------------------------------
# 5. AUTOMATED SCHEDULE LOOP
# ---------------------------------------------------------
@tasks.loop(minutes=1)
async def schedule_check_loop():
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        channel = bot.get_channel(PREP_CHANNEL_ID)
        if not channel:
            return

        # Check 10-min and 5-min pre-alerts (Construction & Science ONLY)
        for mins in [10, 5]:
            target_dt = now_local + datetime.timedelta(minutes=mins)
            if target_dt.minute == 0 and target_dt.hour in [0, 4, 8, 12, 16, 20]:
                theme, st_str, unix_start, unix_end = get_event_at_time(target_dt)
                if theme in ["Shelter Expansion", "Age of Science"]:
                    embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=True, mins_left=mins)
                    await channel.send(content=f"@everyone 🚨 **{mins}-MINUTE CAPITAL TITLE PRE-ALERT!**", embeds=embeds)

        # Check Live Phase Start (ALL Tasks)
        if now_local.minute == 0 and now_local.hour in [0, 4, 8, 12, 16, 20]:
            theme, st_str, unix_start, unix_end = get_event_at_time(now_local)
            embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=False)
            await channel.send(content=f"@everyone 🔥 **{theme.upper()} IS NOW LIVE!**", embeds=embeds)

    except Exception as e:
        print(f"❌ Error in schedule_check_loop: {e}")

@schedule_check_loop.before_loop
async def before_schedule_loop():
    await bot.wait_until_ready()


# ---------------------------------------------------------
# 6. DISCORD SLASH COMMANDS
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"📡 Synced {len(synced)} slash command(s) globally.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")
        
    if not schedule_check_loop.is_running():
        schedule_check_loop.start()

# Slash Command: /active_prep
@bot.tree.command(name="active_prep", description="View the currently active prep phase and event tasks")
async def active_prep_cmd(interaction: discord.Interaction):
    theme, st_str, unix_start, unix_end = get_current_active_event()
    embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=False)
    await interaction.response.send_message(content="🔥 **CURRENT ACTIVE PREP PHASE:**", embeds=embeds)

# Slash Command: /next
@bot.tree.command(name="next", description="Check the upcoming event phase and countdown")
async def next_cmd(interaction: discord.Interaction):
    now_local = datetime.datetime.now(UTC_MINUS_2)
    cycle_hours = [0, 4, 8, 12, 16, 20]
    current_hour = now_local.hour
    
    next_hour = next((h for h in cycle_hours if h > current_hour), cycle_hours[0])
    next_date = now_local + datetime.timedelta(days=1) if next_hour <= current_hour else now_local

    target_dt = datetime.datetime(next_date.year, next_date.month, next_date.day, next_hour, 0, tzinfo=UTC_MINUS_2)
    theme, st_str, unix_start, unix_end = get_event_at_time(target_dt)
    
    mins_until = int((target_dt - now_local).total_seconds() // 60)
    embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=True, mins_left=mins_until)
    
    await interaction.response.send_message(content="📅 **UPCOMING PREP PHASE DETAILS:**", embeds=embeds)

# Slash Command: /schedule
@bot.tree.command(name="schedule", description="Display the full weekly prep phase schedule in your local time")
async def schedule_cmd(interaction: discord.Interaction):
    now_local = datetime.datetime.now(UTC_MINUS_2)
    embed = discord.Embed(
        title="🗓️ MASTER WEEKLY EVENT SCHEDULE",
        description="Every 4-hour prep slot dynamically converted to your local device timezone.",
        color=discord.Color.from_str("#2C3E50")
    )

    for day_offset in range(7):
        target_day_dt = now_local + datetime.timedelta(days=day_offset)
        weekday_idx = target_day_dt.weekday()
        day_name = DAYS_MAP[weekday_idx]
        
        day_str = ""
        for hour in [0, 4, 8, 12, 16, 20]:
            slot_dt = datetime.datetime(target_day_dt.year, target_day_dt.month, target_day_dt.day, hour, 0, tzinfo=UTC_MINUS_2)
            ts = int(slot_dt.astimezone(datetime.timezone.utc).timestamp())
            theme = WEEKLY_SCHEDULE[weekday_idx][hour]
            day_str += f"•  (): **{theme}**\n"

        header = f"📅 {day_name}" if day_offset != 0 else f"📅 Today ({day_name})"
        embed.add_field(name=header, value=day_str, inline=False)

    embed.set_footer(text="Dark War Survival • Verified Data System")
    await interaction.response.send_message(embed=embed)

# Slash Command: /chest_calculator
@bot.tree.command(name="chest_calculator", description="Calculate required speedups or item uses to unlock event chests")
@app_commands.describe(
    target_points="Target Chest (8000, 16000, 40000)",
    action_type="Select action (Speedups, Wisdom Medals, Prime Recruits, Gears, Power Cores)"
)
@app_commands.choices(
    target_points=[
        app_commands.Choice(name="Chest 1 (8,000 pts - 590 Rubies)", value=8000),
        app_commands.Choice(name="Chest 2 (16,000 pts - 1,200 Rubies)", value=16000),
        app_commands.Choice(name="Chest 3 (40,000 pts - 2,950 Rubies)", value=40000)
    ],
    action_type=[
        app_commands.Choice(name="1-Min Speedups (+5 pts)", value=5),
        app_commands.Choice(name="Wisdom Medals (+5 pts)", value=5),
        app_commands.Choice(name="Precision Parts (+300 pts)", value=300),
        app_commands.Choice(name="Prime Recruits (+400 pts)", value=400),
        app_commands.Choice(name="Exclusive Equip Fragments (+600 pts)", value=600),
        app_commands.Choice(name="Orange Hero Fragments (+600 pts)", value=600),
        app_commands.Choice(name="Power Cores (+450 pts)", value=450),
        app_commands.Choice(name="Titanium Alloy (+180 pts)", value=180)
    ]
)
async def chest_calc_cmd(interaction: discord.Interaction, target_points: app_commands.Choice[int], action_type: app_commands.Choice[int]):
    required_count = math.ceil(target_points.value / action_type.value)
    
    embed = discord.Embed(
        title="🧮 EVENT CHEST CALCULATOR",
        color=discord.Color.brand_green()
    )
    embed.add_field(name="🎯 Target Goal", value=f"**{target_points.value:,} Points** ({target_points.name})", inline=False)
    embed.add_field(name="⚡ Required Action", value=f"**{required_count:,}x** {action_type.name}", inline=False)
    embed.set_footer(text="Dark War Survival • Quick Calculator")
    
    await interaction.response.send_message(embed=embed)

# Slash Command: /set_prep_channel
@bot.tree.command(name="set_prep_channel", description="Set the target text channel for automated event notifications")
@app_commands.describe(channel="Select the text channel where event alerts should be sent.")
@app_commands.default_permissions(administrator=True)
async def set_prep_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global PREP_CHANNEL_ID
    
    if not interaction.user.guild_permissions.manage_channels and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need **Manage Channels** or **Administrator** permissions to use this command.", ephemeral=True)
        return

    PREP_CHANNEL_ID = channel.id
    save_channel_id(channel.id)
    
    embed = discord.Embed(
        title="⚙️ Notification Channel Updated",
        description=f"Automated prep alerts will now be sent to {channel.mention}.\nSetting saved permanently to `config.json`.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Slash Command: /test
@bot.tree.command(name="test", description="Test bot connectivity and latency")
async def test_cmd(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🤖 Bot Status: Operational",
        description=f"**Ping Latency:** `{latency} ms`\n**Active Target Channel:** <#{PREP_CHANNEL_ID}>",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------------------------------------------------
# 7. BOT RUNNER
# ---------------------------------------------------------
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set.")
