import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
from googleapiclient import discovery
from moderation import handle_moderation
from replit import db

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')
PERSPECTIVE_API_KEY = os.getenv('perspective_api')

if not TOKEN:
    raise Exception("Please add your Discord bot TOKEN to the .env file.")
if not PERSPECTIVE_API_KEY:
    raise Exception("Please add your perspective_api key to the .env file.")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.auto_moderation = True
bot = commands.Bot(command_prefix="$", intents=intents)

# --- Perspective API Client Setup ---
try:
    client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=PERSPECTIVE_API_KEY,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        static_discovery=False,
    )
except Exception as e:
    print(f"Error building Perspective API client: {e}")
    client = None  # Disable moderation if client fails

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    if not client:
        print("Perspective API client failed to initialize. Moderation features will be disabled.")

@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

@bot.command()
async def set_mod_role(ctx,role: discord.Role):
    try:
        guild_data = db.get(str(ctx.guild.id),{})
        guild_data['mod_role_id'] = role.id
        db[str(ctx.guild.id)] = guild_data
        await ctx.send(f"Moderator role set to {role.mention}")
    except Exception as e:
        print("Error setting moderator role:", e)
        await ctx.send("An error occurred while setting the moderator role.")    

@bot.command()
async def set_logging_channel(ctx,channel: discord.TextChannel):
    try:
        guild_data = db.get(str(ctx.guild.id),{})
        guild_data['logging_channel_id'] = channel.id
        db[str(ctx.guild.id)] = guild_data
        await ctx.send(f"Logging channel set to {channel.mention}")
    except Exception as e:
        print("Error setting logging channel:", e)
        await ctx.send("An error occurred while setting the logging channel.")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    if not client:  # Skip analysis if Perspective API client isn't available
        return

    analyze_request = {
        'comment': {'text': message.content},
        'requestedAttributes': {
            attr: {} for attr in ['SEVERE_TOXICITY', 'THREAT', 'TOXICITY', 'IDENTITY_ATTACK', 'INSULT', 'PROFANITY', 'SEXUALLY_EXPLICIT', 'FLIRTATION']
        },
        'languages': ['en']
    }

    try:
        response = client.comments().analyze(body=analyze_request).execute()
        scores = {
            attr: round(response['attributeScores'][attr]['summaryScore']['value'], 3)
            for attr in analyze_request['requestedAttributes']
            if attr in response.get('attributeScores', {})
        }

        if not scores:
            return

        print(f"Scores for message '{message.content[:50]}...' by {message.author}: {json.dumps(scores)}")
        highest_offense_type, highest_score = max(scores.items(), key=lambda item: item[1])

        if highest_score > 0.8:
            count = sum(1 for score in scores.values() if score > 0.8)
            await handle_moderation(message, highest_offense_type, highest_score, count)

    except Exception as e:
        print(f"Error analyzing comment (ID: {message.id}): {e}")


# --- Run Bot ---
try:
    print("Attempting to run bot...")
    bot.run(TOKEN)
except Exception as e:
    print(f"Error running bot: {e}")
