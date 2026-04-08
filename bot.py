import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI

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

# ←←← ADD YOUR CHANNELS HERE (these are the ones Grok will scan)
WATCH_CHANNELS = [
    "general",
    "memes",
    "clips-medias",
    "roast-no-mercy",
    "unhinged-nsfw",
    "irl-pets-nature",
    "foods-arts",
    "quotes",
    "movie-chat",
    "hr-chat"
    # Add or remove any channel names you want
]

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

@bot.tree.command(name="analyze", description="Grok analyzes the ENTIRE server")
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
            async for msg in channel.history(limit=25):  # 25 messages per channel
                if not msg.author.bot:
                    messages.append(f"#{channel.name} | {msg.author.display_name}: {msg.content}")
            all_messages.extend(reversed(messages))  # oldest first
        except:
            continue  # skip channels we can't read

    recent_chat = "\n".join(all_messages[-400:])  # limit total size for cost

    system_prompt = """You are Grok, the official co-pilot and advisor for **No Mercy Hub** — a small, chill gaming Discord server with ~28 members.
The server is for friends to hang out, team up in games, share clips, roast each other, and post memes.
Tone: friendly, direct, fun, no corporate fluff. You can be sarcastic when appropriate but always fair.

Your job: Analyze the recent activity across the **whole server** and give clear recommendations in this exact format:

**📊 Quick Summary**
(one short paragraph about overall vibe and activity)

**⚠️ Discipline / Issues** (if any)
- list any problems with reasoning and which channel

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
            max_tokens=900
        )
        grok_reply = response.choices[0].message.content

        await interaction.followup.send(f"**Grok's Full Server Analysis**:\n\n{grok_reply}")

    except Exception as e:
        await interaction.followup.send(f"❌ Something went wrong: {str(e)}")

bot.run(DISCORD_TOKEN)
