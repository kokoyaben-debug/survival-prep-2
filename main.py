import os
import datetime
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
# 2. DISCORD BOT & SLASH COMMAND SETUP
# ---------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dynamic or Environment Channel ID storage
PREP_CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "1554020108878217247"))
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))

# Color Palette
PHASE_COLORS = {
    "Shelter Expansion": discord.Color.from_str("#F1C40F"),  # Gold
    "Age of Science":    discord.Color.from_str("#3498DB"),  # Blue
    "Hero Initiative":   discord.Color.from_str("#9B59B6"),  # Purple
    "Unit Training":     discord.Color.from_str("#2ECC71"),  # Green
    "Arms Expert":       discord.Color.from_str("#E74C3C")   # Red
}

# Server Time (ST) strings matching game cycles
ST_RANGES = {
    0: "00:00-04:00 ST",
    4: "04:00-08:00 ST",
    8: "08:00-12:00 ST",
    12: "12:00-16:00 ST",
    16: "16:00-20:00 ST",
    20: "20:00-00:00 ST"
}

# Weekly Cycle Schedule
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

# Task Scoring Details
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
# 3. HELPER FUNCTIONS & EMBED BUILDERS
# ---------------------------------------------------------
def get_event_at_time(dt_local: datetime.datetime):
    weekday = dt_local.weekday()
    hour = dt_local.hour
    theme = WEEKLY_SCHEDULE.get(weekday, {}).get(hour, "Survival Prep Phase")
    st_str = ST_RANGES.get(hour, "00:00-04:00 ST")
    unix_start = int(dt_local.astimezone(datetime.timezone.utc).timestamp())
    unix_end = unix_start + 14400  # 4 hours later
    return theme, st_str, unix_start, unix_end

def build_two_embed_stack(theme: str, st_range: str, unix_start: int, unix_end: int, is_pre_alert: bool = False, mins_left: int = 0) -> list:
    color = PHASE_COLORS.get(theme, discord.Color.orange())
    
    # Dynamic Timestamps
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
# 4. AUTOMATED LOOPS (PRE-ALERTS & LIVE ALERTS)
# ---------------------------------------------------------
@tasks.loop(minutes=1)
async def schedule_check_loop():
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        channel = bot.get_channel(PREP_CHANNEL_ID)
        if not channel:
            return

        # Check 10-min and 5-min pre-alerts for Construction & Science ONLY
        for mins in [10, 5]:
            target_dt = now_local + datetime.timedelta(minutes=mins)
            if target_dt.minute == 0 and target_dt.hour in [0, 4, 8, 12, 16, 20]:
                theme, st_str, unix_start, unix_end = get_event_at_time(target_dt)
                if theme in ["Shelter Expansion", "Age of Science"]:
                    embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=True, mins_left=mins)
                    await channel.send(content=f"@everyone 🚨 **{mins}-MINUTE CAPITAL TITLE PRE-ALERT!**", embeds=embeds)

        # Check Live Phase Start for ALL Tasks
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
# 5. COMMANDS & EVENT HANDLERS
# ---------------------------------------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"📡 Synced {len(synced)} slash commands globally.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")
        
    if not schedule_check_loop.is_running():
        schedule_check_loop.start()

# Slash Command: /set_prep_channel
@bot.tree.command(name="set_prep_channel", description="Set the target channel for event notifications")
@app_commands.describe(channel="Select the text channel for event alerts")
async def set_prep_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    global PREP_CHANNEL_ID
    PREP_CHANNEL_ID = channel.id
    await interaction.response.send_message(f"✅ **Event Prep notification channel updated to:** {channel.mention}", ephemeral=True)

# Prefix Command: !next
@bot.command(name="next")
async def next_cmd(ctx):
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        cycle_hours = [0, 4, 8, 12, 16, 20]
        current_hour = now_local.hour
        
        next_hour = next((h for h in cycle_hours if h > current_hour), cycle_hours[0])
        next_date = now_local + datetime.timedelta(days=1) if next_hour <= current_hour else now_local

        target_dt = datetime.datetime(next_date.year, next_date.month, next_date.day, next_hour, 0, tzinfo=UTC_MINUS_2)
        theme, st_str, unix_start, unix_end = get_event_at_time(target_dt)
        
        embeds = build_two_embed_stack(theme, st_str, unix_start, unix_end, is_pre_alert=True, mins_left=int((target_dt - now_local).total_seconds() // 60))
        
        await ctx.send(content="📅 **UPCOMING PREP PHASE DETAILS:**", embeds=embeds, delete_after=60)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
    except Exception as e:
        await ctx.send(f"❌ Error fetching next phase: {e}", delete_after=10)

# Prefix Command: !schedule
@bot.command(name="schedule")
async def schedule_cmd(ctx):
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        embed = discord.Embed(
            title="🗓️ FULL WEEKLY EVENT SCHEDULE",
            description="All 4-hour prep phase schedules converted dynamically to your local time.",
            color=discord.Color.from_str("#34495E")
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

        embed.set_footer(text="Dark War Survival • Master Schedule (Deletes in 120s)")
        
        await ctx.send(embed=embed, delete_after=120)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
    except Exception as e:
        await ctx.send(f"❌ Error generating schedule: {e}", delete_after=10)


TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set.")
