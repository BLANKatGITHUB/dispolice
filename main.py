import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from googleapiclient import discovery, logging
import datetime
import json


load_dotenv()
TOKEN = os.getenv('TOKEN')
PERSPECTIVE_API_KEY = os.getenv('perspective_api')

MOD_ROLE_ID = 1356674452095635747

if not TOKEN:
    raise Exception("Please add your Discord bot TOKEN to the .env file.")
if not PERSPECTIVE_API_KEY:
    raise Exception("Please add your perspective_api key to the .env file.")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="$", intents=intents)

# --- Perspective API Client ---
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
    client = None # Ensure client is None if building fails

# --- Base Warning Messages ---
BASE_WARNING_MESSAGES = {
    'SEVERE_TOXICITY': '🚫 Severely toxic content detected.',
    'THREAT': '🚫 Threatening content is not allowed.',
    'TOXICITY': '⚠️ Toxic content detected.',
    'IDENTITY_ATTACK': '🚫 Identity-based attacks are not allowed.',
    'INSULT': '⚠️ Insulting content detected.',
    'PROFANITY': '⚠️ Excessive profanity detected.',
    'SEXUALLY_EXPLICIT': '🚫 Sexually explicit content is not allowed.',
    'FLIRTATION': '⚠️ Inappropriate flirtation detected.'
}
DEFAULT_WARNING = "⚠️ Inappropriate content detected."

# --- Helper Function for Moderation ---
async def handle_moderation(message: discord.Message, offense_type: str, score: float, count: int):

    if not message.guild:
        print(f"Cannot moderate message {message.id} (not in a guild).")
        return

    base_warning = BASE_WARNING_MESSAGES.get(offense_type, DEFAULT_WARNING)
    full_warning = f"{message.author.mention} {base_warning}"
    timeout_duration = None
    ping_role = False
    reason = f"Content flagged for {offense_type} (Score: {score:.3f})"

    # Determine specific actions based on score threshold
    if score > 0.9 and count >= 2:
        full_warning += " User temporarily muted for 5 minutes."
        ping_role = True
        timeout_duration = datetime.timedelta(minutes=5)
    elif score > 0.8 and count>=2:
        full_warning += " Moderator review advised."
        ping_role = True

    # Fetch and mention role if needed (using hardcoded ID)
    moderator_role = None
    if ping_role:
        try:
            # Using the hardcoded ID here
            moderator_role = message.guild.get_role(MOD_ROLE_ID)
            if moderator_role:
                full_warning += f" {moderator_role.mention}"
            else:
                # Warn if the hardcoded role ID isn't found in this specific server
                print(f"Warning: Could not find role with hardcoded ID {MOD_ROLE_ID} in guild {message.guild.name}")
        except Exception as e:
             print(f"Error fetching role {MOD_ROLE_ID} in guild {message.guild.name}: {e}")

    # Perform actions
    try:
        await message.channel.send(full_warning, delete_after=15)
        await message.delete()
        print(f"Deleted message {message.id} by {message.author} for {offense_type} ({score:.3f})")

        if timeout_duration:
            try:
                await message.author.timeout(timeout_duration, reason=reason)
                print(f"Timed out {message.author} for {timeout_duration} due to: {reason}")
            except discord.Forbidden:
                print(f"Error: Missing 'Moderate Members' permission to time out {message.author}.")
            except discord.HTTPException as e:
                 print(f"Error timing out {message.author}: {e}")

    except discord.Forbidden:
        print(f"Error: Missing permissions in channel {message.channel.name} (Guild: {message.guild.name}). Need 'Send Messages' and 'Manage Messages'.")
    except discord.NotFound:
        print(f"Warning: Message {message.id} was likely already deleted.")
    except Exception as e:
        print(f"An unexpected error occurred during moderation for message {message.id}: {e}")

    # logging
    logging:None|bool = True
    if logging:    
        logging_channel_id:None|discord.TextChannel = 1356741431250653355
        try:
            logging_channel = message.guild.get_channel(logging_channel_id)
            if logging_channel:
                embed = discord.Embed(title="Message Moderated", color=0xff0000)
                embed.add_field(name="Author", value=message.author.mention, inline=False)
                embed.add_field(name="Channel", value=message.channel.mention, inline=False)
                embed.add_field(name="Message", value=message.content, inline=False)
                embed.add_field(name="Offense Type", value=offense_type, inline=False)
                embed.add_field(name="Score", value=f"{score:.3f}", inline=False)
                if timeout_duration:
                    embed.add_field(name="Timeout Duration", value=timeout_duration, inline=False)
                await logging_channel.send(embed=embed)
        except discord.Forbidden :
            print(f"Error: Missing permissions in channel {logging_channel_id} (Guild: {message.guild})" )
        except Exception as e:
            print(f"An unexpected error occurred during logging for message {message.id}: {e}")


# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    if not client:
        print("Perspective API client failed to initialize. Moderation features will be disabled.")
    # No need to check for MOD_ROLE_ID here anymore


@bot.command()
async def hello(ctx):
    await ctx.send('Hello!')

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or message.author.bot or not message.guild:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    if not client: # Skip analysis if Perspective API client isn't available
        return

    analyze_request = {
        'comment': {'text': message.content},
        'requestedAttributes': {attr: {} for attr in BASE_WARNING_MESSAGES.keys()},
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
        count = sum(1 for score in scores.values() if score > 0.8)

        if highest_score > 0.7:
            # Call helper function (no longer passing role ID)
            await handle_moderation(message, highest_offense_type, highest_score,count)

    except Exception as e:
        print(f"Error analyzing comment (ID: {message.id}): {e}")


# --- Run Bot ---
try:
    print("Attempting to run bot...")
    bot.run(TOKEN)
except discord.HTTPException as e:
    print(f"HTTPException: {e}")
except Exception as e:
    print(f"Error running bot: {e}")