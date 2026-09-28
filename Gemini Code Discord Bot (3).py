import os
import datetime
import discord
from discord.ext import commands, tasks

# Enable required intent permissions
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ⚠️ REPLACE THIS WITH YOUR COPIED DISCORD CHANNEL ID
CHANNEL_ID = 123456789012345678  

# Define UTC-2 Timezone Offset (-2 Hours)
UTC_MINUS_2 = datetime.timezone(datetime.timedelta(hours=-2))

# Schedule in UTC-2 local times (:55 of the hour preceding each 4-hour event start)
TIMES = [
    datetime.time(hour=21, minute=55, tzinfo=UTC_MINUS_2), # Shelter Expansion (22:00 start)
    datetime.time(hour=1,  minute=55, tzinfo=UTC_MINUS_2), # Hero Initiative (02:00 start)
    datetime.time(hour=5,  minute=55, tzinfo=UTC_MINUS_2), # Unit Training (06:00 start)
    datetime.time(hour=9,  minute=55, tzinfo=UTC_MINUS_2), # Age of Science (10:00 start)
    datetime.time(hour=13, minute=55, tzinfo=UTC_MINUS_2), # Arms Expert (14:00 start)
    datetime.time(hour=17, minute=55, tzinfo=UTC_MINUS_2)  # Shelter Expansion (18:00 start)
]

def generate_alert_message(hour: int) -> str:
    """Generates the appropriate message based on the hour in UTC-2."""
    if hour in [21, 17]:
        return (
            "@everyone 🚨 **SURVIVAL PREP ALERT — 5 MINUTES!** 🚨\n\n"
            "The next phase is **SHELTER EXPANSION**! 🏗️\n"
            "⚠️ **Do NOT start building upgrades yet!**\n"
            "👉 **Apply for the Secretary of Construction buff** at the Capital right now!"
        )
    elif hour == 9:
        return (
            "@everyone 🚨 **SURVIVAL PREP ALERT — 5 MINUTES!** 🚨\n\n"
            "The next phase is **AGE OF SCIENCE**! 🔬\n"
            "⚠️ **Do NOT start or finish tech research yet!**\n"
            "👉 **Apply for the Secretary of Science buff** at the Capital right now!"
        )
    else:
        return (
            "@everyone 🚨 **SURVIVAL PREP ALERT — 5 MINUTES!** 🚨\n\n"
            "The next Survival Prep phase is starting in 5 minutes! Prepare your items and get ready! ⚔️"
        )

@tasks.loop(time=TIMES)
async def survival_prep_alerts():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Channel ID {CHANNEL_ID} not found.")
        return

    now_local = datetime.datetime.now(UTC_MINUS_2)
    msg = generate_alert_message(now_local.hour)
    await channel.send(msg)

@bot.event
async def on_ready():
    print(f"✅ Bot online! Logged in as: {bot.user.name}")
    print(f"🕒 Configured for UTC-2 schedule.")
    if not survival_prep_alerts.is_running():
        survival_prep_alerts.start()

# --- TESTING COMMANDS ---

@bot.command(name="test")
async def test_command(ctx):
    """Simple connection test."""
    await ctx.send("🤖 **Bot is active and listening!**")

@bot.command(name="triggeralert")
async def trigger_alert_command(ctx):
    """Manually triggers the alert message for testing."""
    now_local = datetime.datetime.now(UTC_MINUS_2)
    msg = generate_alert_message(now_local.hour)
    await ctx.send("🧪 **[MANUAL TEST TRIGGER]** Sending alert preview:")
    await ctx.send(msg)

# Load Token from Environment Variable
TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: DISCORD_TOKEN environment variable is not set!")