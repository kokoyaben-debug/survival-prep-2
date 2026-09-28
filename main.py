import os
import datetime
import threading
from flask import Flask
import discord
from discord.ext import commands, tasks

# 1. FLASK KEEP-ALIVE SERVER (Prevents Render Inactivity Sleep)
app = Flask('')

@app.route('/')
def home():
    return "Dark War Event Bot is Alive & Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()


# 2. DISCORD BOT SETUP
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "1554020108878217247"))
ROLE_ID = os.environ.get("ROLE_ID")

UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))

# Hex Color Palette
PHASE_COLORS = {
    "Shelter Expansion": discord.Color.from_str("#F1C40F"),  # Gold
    "Age of Science":    discord.Color.from_str("#3498DB"),  # Blue
    "Hero Initiative":   discord.Color.from_str("#9B59B6"),  # Purple
    "Unit Training":     discord.Color.from_str("#2ECC71"),  # Green
    "Arms Expert":       discord.Color.from_str("#E74C3C")   # Red
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

PRE_ALERT_TIMES = [
    datetime.time(hour=3, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=7, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=11, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=15, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=19, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=23, minute=55, tzinfo=UTC_MINUS_2)
]

LIVE_ALERT_TIMES = [
    datetime.time(hour=0, minute=0, tzinfo=UTC_MINUS_2),
    datetime.time(hour=4, minute=0, tzinfo=UTC_MINUS_2),
    datetime.time(hour=8, minute=0, tzinfo=UTC_MINUS_2),
    datetime.time(hour=12, minute=0, tzinfo=UTC_MINUS_2),
    datetime.time(hour=16, minute=0, tzinfo=UTC_MINUS_2),
    datetime.time(hour=20, minute=0, tzinfo=UTC_MINUS_2)
]

def get_ping_mention() -> str:
    if ROLE_ID and ROLE_ID.isdigit():
        return f"<@&{ROLE_ID}>"
    return "@everyone"

def get_event_at_time(dt_local: datetime.datetime):
    weekday = dt_local.weekday()
    hour = dt_local.hour
    theme = WEEKLY_SCHEDULE.get(weekday, {}).get(hour, "Survival Prep Phase")
    unix_ts = int(dt_local.astimezone(datetime.timezone.utc).timestamp())
    return theme, unix_ts

def build_pre_alert_embed(theme: str, timestamp: int) -> discord.Embed:
    countdown = f""
    color = PHASE_COLORS.get(theme, discord.Color.dark_grey())

    if theme == "Shelter Expansion":
        embed = discord.Embed(
            title="🏗️ SURVIVAL PREP — SHELTER EXPANSION",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=color
        )
        embed.add_field(
            name="🔴 MANDATORY CAPITAL POSITION",
            value="> 👑 **APPLY FOR SECRETARY OF CONSTRUCTION AT THE CAPITAL NOW!**\n> 🛑 Do NOT finish upgrades until the event officially starts!",
            inline=False
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Precision Part in Upgrades:** 600 pts / unit\n"
                "• **Structure CP Increase:** 20 pts per 100 CP\n"
                "• **Tech CP Increase:** 20 pts per 100 CP\n"
                "• **Wisdom Medals Consumed:** 20 pts / medal\n"
                "• **Construction Acceleration:** 10 pts per 1-min speedup\n"
                "• **Research Acceleration:** 10 pts per 1-min speedup"
            ),
            inline=False
        )

    elif theme == "Age of Science":
        embed = discord.Embed(
            title="🔬 SURVIVAL PREP — AGE OF SCIENCE",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=color
        )
        embed.add_field(
            name="🔴 MANDATORY CAPITAL POSITION",
            value="> 👑 **APPLY FOR SECRETARY OF SCIENCE AT THE CAPITAL NOW!**\n> 🛑 Do NOT collect or rush tech nodes early!",
            inline=False
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Tech CP Increase:** 20 pts per 100 CP\n"
                "• **Wisdom Medals Consumed:** 20 pts / medal\n"
                "• **Research Acceleration:** 10 pts per 1-min speedup\n"
                "• **Construction Acceleration:** 10 pts per 1-min speedup"
            ),
            inline=False
        )

    elif theme == "Hero Initiative":
        embed = discord.Embed(
            title="🦸 SURVIVAL PREP — HERO TRIAL",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=color
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Orange Hero Fragment (Star Rise):** 1,350 pts / fragment\n"
                "• **Prime Recruitment:** 900 pts per pull\n"
                "• **Purple Hero Fragment (Star Rise):** 300 pts / fragment\n"
                "• **Blue Hero Fragment (Star Rise):** 150 pts / fragment"
            ),
            inline=False
        )
        embed.add_field(name="💡 PRO STRATEGY", value="> 🎟️ Focus recruitment pulls in bulk during this phase.", inline=False)

    elif theme == "Unit Training":
        embed = discord.Embed(
            title="🪖 SURVIVAL PREP — UNIT TRAINING",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=color
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value="• **Train Lv.1 Unit:** 12 pts / unit\n• **Training Acceleration:** 10 pts per 1-min speedup",
            inline=False
        )
        embed.add_field(name="💡 PRO STRATEGY", value="> 🛡️ Leave finished troops in barracks until phase starts!", inline=False)

    elif theme == "Arms Expert":
        embed = discord.Embed(
            title="🎯 SURVIVAL PREP — ARMS EXPERT",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=color
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Orange Hero Fragment:** 1,350 pts / fragment\n"
                "• **Purple Hero Fragment:** 300 pts / fragment\n"
                "• **Blue Hero Fragment:** 150 pts / fragment\n"
                "• **Wisdom Medals Consumed:** 10 pts / medal\n"
                "• **Gears Used:** 3 pts / gear\n"
                "• **1-min Accelerations (Any):** 10 pts per speedup"
            ),
            inline=False
        )
        embed.add_field(name="💡 PRO STRATEGY", value="> ⚙️ Combine gears and general speedups to reach max milestone chests!", inline=False)

    else:
        embed = discord.Embed(title="⚔️ SURVIVAL PREP ALERT", description=f"### ⏳ Phase Starts {countdown}!", color=color)

    embed.set_footer(text="Dark War Survival • Data Integration")
    return embed

def build_live_alert_embed(theme: str) -> discord.Embed:
    color = PHASE_COLORS.get(theme, discord.Color.red())
    embed = discord.Embed(
        title=f"🔥 {theme.upper()} IS NOW LIVE!",
        description="### ⚡ Event points are now active! Start completing tasks now.",
        color=color
    )
    if theme == "Shelter Expansion":
        embed.add_field(
            name="🔴 CAPITAL BUFF REMINDER",
            value="> 🏛️ Ensure you have **Secretary of Construction** active before executing building upgrades!",
            inline=False
        )
    elif theme == "Age of Science":
        embed.add_field(
            name="🔴 CAPITAL BUFF REMINDER",
            value="> 🔬 Ensure you have **Secretary of Science** active before starting high-tier research!",
            inline=False
        )
    embed.set_footer(text="Dark War Survival • Live Event Monitor")
    return embed

# Automated Loops
@tasks.loop(time=PRE_ALERT_TIMES)
async def pre_alert_loop():
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            now_local = datetime.datetime.now(UTC_MINUS_2)
            target_dt = now_local + datetime.timedelta(minutes=5)
            theme, timestamp = get_event_at_time(target_dt)
            embed = build_pre_alert_embed(theme, timestamp)
            ping = get_ping_mention()
            await channel.send(content=f"{ping} 🚨 **5-MINUTE EVENT ALERT!**", embed=embed)
    except Exception as e:
        print(f"❌ Error in pre_alert_loop: {e}")

@tasks.loop(time=LIVE_ALERT_TIMES)
async def live_alert_loop():
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            now_local = datetime.datetime.now(UTC_MINUS_2)
            theme, _ = get_event_at_time(now_local)
            embed = build_live_alert_embed(theme)
            ping = get_ping_mention()
            await channel.send(content=f"{ping} 🔥 **EVENT IS NOW LIVE!**", embed=embed)
    except Exception as e:
        print(f"❌ Error in live_alert_loop: {e}")

@pre_alert_loop.before_loop
@live_alert_loop.before_loop
async def before_loops():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user.name}")
    print(f"📡 Channel ID: {CHANNEL_ID}")
    if not pre_alert_loop.is_running():
        pre_alert_loop.start()
    if not live_alert_loop.is_running():
        live_alert_loop.start()

# Commands
@bot.command(name="test")
async def test_cmd(ctx):
    await ctx.send("🤖 **Bot is online and active!**", delete_after=10)
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

@bot.command(name="next")
async def next_cmd(ctx):
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        cycle_hours = [0, 4, 8, 12, 16, 20]
        current_hour = now_local.hour
        
        next_hour = next((h for h in cycle_hours if h > current_hour), cycle_hours[0])
        next_date = now_local + datetime.timedelta(days=1) if next_hour <= current_hour else now_local

        target_dt = datetime.datetime(next_date.year, next_date.month, next_date.day, next_hour, 0, tzinfo=UTC_MINUS_2)
        event_theme, unix_ts = get_event_at_time(target_dt)
        color = PHASE_COLORS.get(event_theme, discord.Color.blue())

        embed = discord.Embed(
            title="📅 UPCOMING PHASE DETAILS",
            description=f"### Next Phase: **{event_theme}**\n⏳ Starts:  ()",
            color=color
        )
        
        today_schedule = WEEKLY_SCHEDULE.get(now_local.weekday(), {})
        timeline_str = ""
        for h in cycle_hours:
            theme = today_schedule.get(h, "Unknown")
            slot_dt = datetime.datetime(now_local.year, now_local.month, now_local.day, h, 0, tzinfo=UTC_MINUS_2)
            slot_ts = int(slot_dt.astimezone(datetime.timezone.utc).timestamp())
            marker = "➡️ " if h == (current_hour // 4) * 4 else "• "
            timeline_str += f"{marker} — **{theme}**\n"

        embed.add_field(name="📍 Today's Daily Timeline", value=timeline_str, inline=False)
        embed.set_footer(text="Dark War Survival • Localized Timestamps (Deletes in 60s)")
        
        await ctx.send(embed=embed, delete_after=60)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
    except Exception as e:
        await ctx.send(f"❌ Error in !next command: {e}", delete_after=10)

@bot.command(name="schedule")
async def schedule_cmd(ctx):
    """Generates a comprehensive weekly schedule breakdown with relative countdowns."""
    try:
        now_local = datetime.datetime.now(UTC_MINUS_2)
        embed = discord.Embed(
            title="🗓️ FULL WEEKLY EVENT SCHEDULE",
            description="All phases shown with automatic local time conversions and countdowns.",
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

@bot.command(name="triggeralert")
async def trigger_cmd(ctx):
    now_local = datetime.datetime.now(UTC_MINUS_2)
    target_dt = now_local + datetime.timedelta(minutes=5)
    theme, timestamp = get_event_at_time(target_dt)
    embed = build_pre_alert_embed(theme, timestamp)
    ping = get_ping_mention()
    await ctx.send(content=f"🧪 **[MANUAL TEST PRE-ALERT]** {ping}", embed=embed)

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set.")
