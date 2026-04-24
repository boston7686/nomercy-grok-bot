import discord
from discord.ext import commands, tasks
import os
import json
import re
from datetime import datetime, time
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

# ====================== SWE AR JAR FEATURE ======================

SWEAR_WORDS = [
    "fuck", "fucking", "fucked", "fucker", "motherfucker", "motherfuckers",
    "shit", "shitty", "shithead", "bullshit", "horseshit",
    "ass", "asshole", "assholes", "dumbass", "jackass",
    "bitch", "bitches", "bitching", "son of a bitch",
    "damn", "dammit", "goddamn", "god damn",
    "hell",
    "cunt", "cunts",
    "dick", "dicks", "dickhead", "dickwad",
    "pussy", "pussies",
    "cock", "cocks", "cockhead",
    "tits", "titties", "boobs", "boobies",
    "bastard", "bastards",
    "whore", "whores",
    "slut", "sluts",
    "nigger", "nigga", "niggaz",
    "retard", "retarded", "retards",
    "fag", "faggot", "fags",
    "crap", "crappy",
    "piss", "pissed", "pissing",
    "douche", "douchebag",
    "twat", "twats",
    "wanker", "wankers",
    "bollocks", "bugger",
    "arse", "arsehole",
    "knob", "knobhead",
    "bellend",
    "spunk",
    "jizz", "cum",
    "wank", "wanking",
    "tosser",
    "prick", "pricks",
    "cocksucker",
    "motherfucking",
    "fucking hell",
    "holy shit",
    "son of a bitch",
    "piece of shit",
    "fuck off",
    "fuck you",
    "go fuck yourself",
    "what the fuck",
    "for fuck's sake",
    "fuck sake",
    "jesus christ",
    "jesus fucking christ",
    "christ almighty",
    "god fucking damnit"
]

def load_swear_data():
    try:
        with open("swear_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"counts": {}, "month": datetime.now().strftime("%Y-%m")}

def save_swear_data(data):
    with open("swear_data.json", "w") as f:
        json.dump(data, f, indent=2)

swear_data = load_swear_data()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    text = message.content.lower()
    swear_count = 0
    
    for word in SWEAR_WORDS:
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = re.findall(pattern, text)
        swear_count += len(matches)
    
    if swear_count > 0:
        user_id = str(message.author.id)
        
        if user_id not in swear_data["counts"]:
            swear_data["counts"][user_id] = 0
        swear_data["counts"][user_id] += swear_count
        
        save_swear_data(swear_data)
        
        await message.channel.send(f"{message.author.mention} swore, ${swear_count} to the swear jar 💰")
    
    await bot.process_commands(message)

@tasks.loop(time=time(hour=10, minute=0))
async def monthly_report():
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    
    if swear_data.get("month") != current_month:
        if swear_data["counts"]:
            general = discord.utils.get(bot.guilds[0].text_channels, name="general")
            if general:
                sorted_users = sorted(swear_data["counts"].items(), key=lambda x: x[1], reverse=True)
                
                embed = discord.Embed(
                    title="💰 Swear Jar Monthly Report",
                    description=f"**{now.strftime('%B %Y')}** results are in!",
                    color=0xFFD700
                )
                
                total = sum(swear_data["counts"].values())
                embed.add_field(name="Total Swears This Month", value=str(total), inline=True)
                embed.add_field(name="Total $ Collected", value=f"${total}", inline=True)
                
                leaderboard = ""
                for i, (user_id, count) in enumerate(sorted_users[:10], 1):
                    user = bot.get_user(int(user_id))
                    name = user.display_name if user else "Unknown User"
                    leaderboard += f"**{i}.** {name} — **{count}** swears (${count})\n"
                
                embed.add_field(name="🏆 Top Swearers", value=leaderboard or "No one swore this month! 🎉", inline=False)
                embed.set_footer(text="Swear jar has been reset for the new month!")
                
                await general.send(embed=embed)
        
        swear_data["counts"] = {}
        swear_data["month"] = current_month
        save_swear_data(swear_data)
        print("Swear jar reset for new month")

@bot.tree.command(name="swearjar", description="Check current swear jar standings")
@app_commands.describe(user="Optional: Check a specific person's count")
async def swearjar(interaction: discord.Interaction, user: discord.Member = None):
    if user:
        user_id = str(user.id)
        count = swear_data["counts"].get(user_id, 0)
        await interaction.response.send_message(
            f"{user.display_name} has sworn **{count}** times this month (${count} to the jar).",
            ephemeral=True
        )
    else:
        if not swear_data["counts"]:
            await interaction.response.send_message("No one has sworn yet this month! 🎉", ephemeral=True)
            return
        
        sorted_users = sorted(swear_data["counts"].items(), key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(title="💰 Current Swear Jar Standings", color=0xFFD700)
        
        leaderboard = ""
        for i, (user_id, count) in enumerate(sorted_users[:15], 1):
            u = bot.get_user(int(user_id))
            name = u.display_name if u else "Unknown"
            leaderboard += f"**{i}.** {name} — **{count}** (${count})\n"
        
        embed.description = leaderboard
        total = sum(swear_data["counts"].values())
        embed.set_footer(text=f"Total: ${total} | Resets on the 1st of next month")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and connected to No Mercy Hub!")
    
    # Force sync commands to THIS server only (instant)
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=YOUR_SERVER_ID_HERE))
        print(f"Synced {len(synced)} commands to this server")
    except Exception as e:
        print(e)
    
    if not monthly_report.is_running():
        monthly_report.start()

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! Grok is ready 🧠")

@bot.tree.command(name="say", description="Make the bot post a message as itself (Mods only)")
@app_commands.describe(message="The message the bot should post")
@app_commands.check(lambda i: i.user.guild_permissions.administrator or i.user.guild_permissions.manage_messages)
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

@bot.tree.command(name="sync", description="Force refresh all slash commands (Admin only)")
async def sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=YOUR_SERVER_ID_HERE))
        await interaction.followup.send(f"✅ Successfully synced {len(synced)} slash commands!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error syncing commands: {str(e)}", ephemeral=True)

bot.run(DISCORD_TOKEN)
