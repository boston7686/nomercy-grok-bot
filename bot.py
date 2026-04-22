import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI
from discord import app_commands

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

grok = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====================== MOD CHECK ======================
def is_mod(interaction: discord.Interaction) -> bool:
    """Check if user has administrator or manage_messages permission"""
    return interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_messages

# Channels Grok will scan
WATCH_CHANNELS = [
    "general", "memes", "clips-medias", "roast-no-mercy",
    "unhinged-nsfw", "irl-pets-nature", "foods-arts", "quotes",
    "movie-chat", "hr-chat"
]

def split_message(text, limit=1900):
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text[:limit].rfind('\n')
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip('\n')
    return chunks

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and connected to No Mercy Hub!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Grok is ready 🧠")

# ====================== NEW: SAY COMMAND (from your other server) ======================
@bot.tree.command(name="say", description="Make the bot post a message as itself (Mods only)")
@app_commands.describe(message="The message the bot should post")
@app_commands.check(is_mod)
async def say(interaction: discord.Interaction, message: str):
    try:
        await interaction.channel.send(message)
        await interaction.response.send_message("✅ Message posted successfully!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to post message: {str(e)}", ephemeral=True)

@bot.tree.command(name="analyze", description="Grok analyzes the ENTIRE server + wellness flags")
async def analyze(interaction: discord.Interaction):
    await interaction.response.defer()

    guild = interaction.guild
    all_messages = []

    for channel_name in WATCH_CHANNELS:
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            continue
        try:
            messages = []
            async for msg in channel.history(limit=50):
                if not msg.author.bot:
                    messages.append(f"#{channel.name} | {msg.author.display_name}: {msg.content}")
            all_messages.extend(reversed(messages))
        except:
            continue

    recent_chat = "\n".join(all_messages[-600:])

    system_prompt = """You are Grok, the official co-pilot and advisor for **No Mercy Hub** — a small, chill gaming Discord server with ~28 members.
The server is for friends to hang out, team up in games, share clips, roast each other, and post memes.
Tone: friendly, direct, fun, no corporate fluff. You can be sarcastic when appropriate but always fair.

Your job: Analyze the recent activity across the whole server and give clear recommendations in this exact format:

**📊 Quick Summary**
(one short paragraph about overall vibe and activity)

**⚠️ Discipline / Issues** (if any)
- list any problems with reasoning and which channel

**🧠 Wellness Flags** (if any)
- Flag any messages that seem to show anger, frustration, low mood, sadness, or possible distress
- Include channel + short quote for context
- IMPORTANT: You are NOT a therapist. This is only an awareness flag for mods to check in if they want. Never diagnose anyone.

**🚀 Engagement Ideas** (3 specific post topics or activities for the next few days)

**🔧 Server Improvement Suggestions**
- any small changes that would help the server

Be honest and helpful. This is a small friend group — keep suggestions realistic and fun."""

    try:
        response = grok.chat.completions.create(
            model="grok-4.20-reasoning",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is recent activity from multiple channels:\n\n{recent_chat}\n\nGive me your full analysis."}
            ],
            temperature=0.7,
            max_tokens=750
        )
        grok_reply = response.choices[0].message.content

        header = "**Grok's Full Server Analysis**:\n\n"
        full_response = header + grok_reply

        for chunk in split_message(full_response):
            await interaction.followup.send(chunk)

    except Exception as e:
        await interaction.followup.send(f"❌ Something went wrong: {str(e)}")

bot.run(DISCORD_TOKEN)
