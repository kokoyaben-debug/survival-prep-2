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

# Target Channel ID
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "1554020108878217247"))

# UTC-2 Server Timezone
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))

# Schedule Matrix
WEEKLY_SCHEDULE = {
    0: {0: "Shelter Expansion", 4: "Hero Initiative", 8: "Unit Training", 12: "Age of Science", 16: "Arms Expert", 20: "Shelter Expansion"},
    1: {0: "Hero Initiative", 4: "Unit Training", 8: "Age of Science", 12: "Arms Expert", 16: "Shelter Expansion", 20: "Hero Initiative"},
    2: {0: "Unit Training", 4: "Age of Science", 8: "Arms Expert", 12: "Shelter Expansion", 16: "Hero Initiative", 20: "Unit Training"},
    3: {0: "Age of Science", 4: "Arms Expert", 8: "Shelter Expansion", 12: "Hero Initiative", 16: "Unit Training", 20: "Age of Science"},
    4: {0: "Arms Expert", 4: "Shelter Expansion", 8: "Hero Initiative", 12: "Unit Training", 16: "Age of Science", 20: "Arms Expert"},
    5: {0: "Shelter Expansion", 4: "Hero Initiative", 8: "Unit Training", 12: "Age of Science", 16: "Arms Expert", 20: "Shelter Expansion"},
    6: {0: "Hero Initiative", 4: "Unit Training", 8: "Age of Science", 12: "Arms Expert", 16: "Shelter Expansion", 20: "Hero Initiative"}
}

# Exact alert execution times (5 minutes before 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC-2)
ALERT_TIMES = [
    datetime.time(hour=3, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=7, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=11, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=15, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=19, minute=55, tzinfo=UTC_MINUS_2),
    datetime.time(hour=23, minute=55, tzinfo=UTC_MINUS_2)
]

def get_upcoming_event_details():
    now_local = datetime.datetime.now(UTC_MINUS_2)
    target_time_local = now_local + datetime.timedelta(minutes=5)
    
    weekday = target_time_local.weekday()
    target_hour = target_time_local.hour
    
    event_theme = WEEKLY_SCHEDULE.get(weekday, {}).get(target_hour, "Survival Prep Phase")
    
    target_utc = target_time_local.astimezone(datetime.timezone.utc)
    unix_timestamp = int(target_utc.timestamp())
    
    return event_theme, unix_timestamp

def build_alert_embed(theme: str, timestamp: int) -> discord.Embed:
    countdown = f""
    
    if theme == "Shelter Expansion":
        embed = discord.Embed(
            title="🏗️ SURVIVAL PREP — SHELTER EXPANSION",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.gold()
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
        embed.add_field(
            name="⚠️ MANDATORY ALLIANCE ACTION",
            value=(
                "> 🏛️ **Apply for Secretary of Construction** at the Capital right now!\n"
                "> 🛑 **Do NOT** complete upgrades until the event timer officially starts!"
            ),
            inline=False
        )

    elif theme == "Age of Science":
        embed = discord.Embed(
            title="🔬 SURVIVAL PREP — AGE OF SCIENCE",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.blue()
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
        embed.add_field(
            name="⚠️ MANDATORY ALLIANCE ACTION",
            value=(
                "> 🏛️ **Apply for Secretary of Science** at the Capital right now!\n"
                "> 🛑 **Do NOT** start or finish high-level tech nodes early!"
            ),
            inline=False
        )

    elif theme == "Hero Initiative":
        embed = discord.Embed(
            title="🦸 SURVIVAL PREP — HERO TRIAL",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.purple()
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
        embed.add_field(
            name="💡 PRO STRATEGY",
            value=(
                "> 🎟️ Focus your recruitment pulls in bulk during this window.\n"
                "> 🌟 Prioritize spending Orange hero fragments for maximum value!"
            ),
            inline=False
        )

    elif theme == "Unit Training":
        embed = discord.Embed(
            title="🪖 SURVIVAL PREP — UNIT TRAINING",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Train Lv.1 Unit:** 12 pts / unit\n"
                "• **Training Acceleration:** 10 pts per 1-min speedup"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 PRO STRATEGY",
            value=(
                "> 🛡️ Leave finished troops queued in barracks until phase starts!\n"
                "> ⏩ Use training speedups to continuously train or promote units."
            ),
            inline=False
        )

    elif theme == "Arms Expert":
        embed = discord.Embed(
            title="🎯 SURVIVAL PREP — ARMS EXPERT",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.red()
        )
        embed.add_field(
            name="📊 EXACT TASK SCORING",
            value=(
                "• **Orange Hero Fragment (Star Rise):** 1,350 pts / fragment\n"
                "• **Purple Hero Fragment (Star Rise):** 300 pts / fragment\n"
                "• **Blue Hero Fragment (Star Rise):** 150 pts / fragment\n"
                "• **Wisdom Medals Consumed:** 10 pts / medal\n"
                "• **Gears Used:** 3 pts / gear\n"
                "• **1-min Accelerations (Any):** 10 pts per speedup"
            ),
            inline=False
        )
        embed.add_field(
            name="💡 PRO STRATEGY",
            value=(
                "> ⚙️ Use gears and combine speedups to hit milestone chest thresholds!"
            ),
            inline=False
        )

    else:
        embed = discord.Embed(
            title="⚔️ SURVIVAL PREP ALERT",
            description=f"### ⏳ Phase Starts {countdown}!\n---",
            color=discord.Color.dark_grey()
        )
        embed.add_field(
            name="⚔️ ACTION PLAN",
            value=f"> Get ready! The next phase is **{theme}**.",
            inline=False
        )

    embed.set_footer(text="Dark War Survival • Data Integration", icon_url="https://i.imgur.com/vH9Z338.png")
    return embed

# Automated Scheduled Task Loop
@tasks.loop(time=ALERT_TIMES)
async def scheduled_alert_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        theme, timestamp = get_upcoming_event_details()
        embed = build_alert_embed(theme, timestamp)
        await channel.send(content="@everyone 🚨 **5-MINUTE EVENT ALERT!**", embed=embed)

@scheduled_alert_loop.before_loop
async def before_alert_loop():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f"✅ Bot online as {bot.user.name}")
    print(f"📡 Target Channel Configured: {CHANNEL_ID}")
    if not scheduled_alert_loop.is_running():
        scheduled_alert_loop.start()

# Commands
@bot.command(name="test")
async def test_cmd(ctx):
    await ctx.send("🤖 **Bot is online and active!**")

@bot.command(name="triggeralert")
async def trigger_cmd(ctx):
    theme, timestamp = get_upcoming_event_details()
    embed = build_alert_embed(theme, timestamp)
    await ctx.send(content="🧪 **[MANUAL TEST TRIGGER]** Upcoming Alert Preview:", embed=embed)

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_TOKEN environment variable not set.")
