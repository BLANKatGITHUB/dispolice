import os
import json
import discord
from discord.ext import commands
from dotenv import load_dotenv
from googleapiclient import discovery
from moderation import handle_moderation,get_thresholds,has_moderator_perms
from replit import db

valid_filters = ['TOXICITY', 'SEVERE_TOXICITY', 'THREAT', 'IDENTITY_ATTACK', 'INSULT', 'PROFANITY', 'SEXUALLY_EXPLICIT', 'FLIRTATION']

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
async def set_mod_role(ctx,role: discord.Role|str = ""):
    if role == "" or type(role) is not discord.Role:
        await ctx.send("Please mention a role or provide a role ID.")
        return
    try:
        guild_data = db.get(str(ctx.guild.id),{})
        guild_data['mod_role_id'] = role.id
        db[str(ctx.guild.id)] = guild_data
        await ctx.send(f"Moderator role set to {role.mention}")
    except Exception as e:
        print("Error setting moderator role:", e)
        await ctx.send("An error occurred while setting the moderator role.")


@bot.command()
async def set_logging_channel(ctx,channel: discord.TextChannel|str = ""):
    if channel == "" or type(channel) is not discord.TextChannel:
        await ctx.send("Please mention a channel or provide a channel ID.")
        return
    try:
        guild_data = db.get(str(ctx.guild.id),{})
        guild_data['logging_channel_id'] = channel.id
        db[str(ctx.guild.id)] = guild_data
        await ctx.send(f"Logging channel set to {channel.mention}")
    except Exception as e:
        print("Error setting logging channel:", e)
        await ctx.send("An error occurred while setting the logging channel.")

@bot.command()
async def clear(ctx,num:int = 0):
    if num == 0:
        await ctx.send("Please provide a number of messages to delete.")
        return
    try:
        await ctx.channel.purge(limit=num+1)
        await ctx.send(f"{num} messages deleted.",delete_after=5)
    except Exception as e:
        print("Error clearing messages:", e)

@bot.command()
async def set_filters(ctx, *filters):
    if not filters:
        await ctx.send("Please provide a list of filters to set.")
        current_filters = db.get(str(ctx.guild.id), {}).get('filters', ['TOXICITY', 'SEVERE_TOXICITY', 'THREAT', 'IDENTITY_ATTACK', 'SEXUALLY_EXPLICIT'])
        await ctx.send(f"Current filters: {', '.join(current_filters)}")
        return

    # Check if all filters are valid
    for filter in filters:
        if filter not in valid_filters:
            await ctx.send(f"Invalid filter: {filter}. Please use one of the following: {', '.join(valid_filters)}")
            return

    try:
        guild_data = db.get(str(ctx.guild.id),{})
        guild_data['filters'] = filters
        db[str(ctx.guild.id)] = guild_data
        await ctx.send(f"Filters set to {', '.join(filters)}")
    except Exception as e:
        print("Error setting filters:", e)
        await ctx.send("An error occurred while setting the filters.")

@bot.command()
async def list_all_filters(ctx):
    await ctx.send(f"All available filters: {', '.join(valid_filters)}")

@bot.command()
async def clear_db(ctx,text:str = ""):
    if text == "":
        await ctx.send("Please provide confirmation text \"Clear Database\".")
    elif text=="Clear Database":
        db.clear()
        await ctx.send("Database cleared.")   
    else:
        await ctx.send("Incorrect confirmation text. correct text is \"Clear Database\".")

@bot.command()
async def list_user_offenses(ctx, user: discord.Member):
    if has_moderator_perms(ctx.author):
        offenses = db.get(str(ctx.guild.id), {}).get(str(user.id), {})
        offense_arr = offenses.get('offense_arr', [])
        offense_count = offenses.get('offense_count', 0)
        await ctx.send(f"User {user.mention} has {offense_count} offenses: {', '.join(offense_arr)}")

    

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    if not client:  
        return
    # applies filters to message
    filters = db.get(str(message.guild.id), {}).get('filters', ['TOXICITY', 'SEVERE_TOXICITY', 'THREAT', 'IDENTITY_ATTACK', 'SEXUALLY_EXPLICIT'])

    # list to store threshold scores for filters
    filter_scores = get_thresholds(len(filters))


    analyze_request = {
        'comment': {'text': message.content},
        'requestedAttributes': {
            attr: {} for attr in filters
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

        overall_score = sum(scores.values())
        print(overall_score)

        if overall_score >= filter_scores[0] :
            await handle_moderation(message,highest_offense_type,highest_score,overall_score,filter_scores)
            return

    except Exception as e:
        print(f"Error analyzing comment (ID: {message.id}): {e}")



# --- Run Bot ---
try:
    print("Attempting to run bot...")
    bot.run(TOKEN)
except Exception as e:
    print(f"Error running bot: {e}")
