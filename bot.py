import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Load tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Grok client (xAI API)
grok = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"
)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and connected to No Mercy Hub!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

# Simple test command
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Grok is ready 🧠")

# === YOUR GROK AGENT COMMAND ===
@bot.tree.command(name="analyze", description="Ask Grok to analyze the server and give recommendations")
async def analyze(interaction: discord.Interaction):
    await interaction.response.defer()  # This prevents timeout

    channel = interaction.channel  # or you can hardcode a specific channel

    # Get last 50 messages
    messages = []
    async for msg in channel.history(limit=50):
        if not msg.author.bot:  # ignore bot messages
            messages.append(f"{msg.author.display_name}: {msg.content}")

    recent_chat = "\n".join(reversed(messages))  # oldest first

    # Custom system prompt tailored to YOUR server
    system_prompt = """You are Grok, the official co-pilot and advisor for **No Mercy Hub** — a small, chill gaming Discord server with ~28 members.
The server is for friends to hang out, team up in games (Overwatch, Destiny, Lethal Company, Palworld, etc.), share clips, roast each other in #roast-no-mercy, and post memes.
Tone: friendly, direct, fun, no corporate fluff. You can be sarcastic when appropriate but always fair.
Server rules: Respectful at core, but unhinged fun is allowed in the right channels.

Your job: Analyze the recent chat and give clear recommendations in this exact format:

**📊 Quick Summary**
(one short paragraph)

**⚠️ Discipline / Issues** (if any)
- list any problems with reasoning

**🚀 Engagement Ideas** (3 specific post topics or activities for the next few days)

**🔧 Server Improvement Suggestions**
- any small changes that would help the server

Be honest and helpful. This is a small friend group — keep suggestions realistic and fun."""

    try:
        response = grok.chat.completions.create(
            model="grok-4.20-reasoning",   # best model for this kind of analysis
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Here is the recent chat from the channel:\n\n{recent_chat}\n\nGive me your analysis and recommendations."}
            ],
            temperature=0.7,
            max_tokens=800
        )
        grok_reply = response.choices[0].message.content

        # Send the reply
        await interaction.followup.send(f"**Grok's Analysis for {channel.name}**:\n\n{grok_reply}")

    except Exception as e:
        await interaction.followup.send(f"❌ Something went wrong: {str(e)}")

bot.run(DISCORD_TOKEN)