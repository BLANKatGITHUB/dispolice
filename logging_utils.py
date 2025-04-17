import discord
import datetime
from replit import db


async def log_moderation_event(message: discord.Message, offense_type: str, score: float,logging_channel_id: int, timeout_duration: datetime.timedelta|None = None):
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
                embed.add_field(name="Timeout Duration", value=str(timeout_duration), inline=False)
            await logging_channel.send(embed=embed)
    except discord.Forbidden:
        print(f"Error: Missing permissions in channel {LOGGING_CHANNEL_ID} (Guild: {message.guild})")
    except Exception as e:
        print(f"An unexpected error occurred during logging for message {message.id}: {e}")

# function to count offense
async def offense_count_log(message:discord.Message,offense_type:str,message_content:str,logging_channel_id:int):
    guild_id = str(message.guild.id)
    author_id = str(message.author.id)
    guild_data = db.get(guild_id, {})
    author_data = guild_data.get(author_id, {})

    offense_arr = author_data.get('offense_arr', [])
    offense_arr.append(f"offense_type: {offense_type}, message {message_content}")
    author_data['offense_arr'] = offense_arr

    offense_count = author_data.get('offense_count', 0) + 1
    author_data['offense_count'] = offense_count
    guild_data[author_id] = author_data
    db[guild_id] = guild_data
    try:
      if offense_count > 3:
        logging_channel = message.guild.get_channel(logging_channel_id)
        if logging_channel:
            await logging_channel.send(f"user has comited various offenses {message.author.mention}")
            await message.author.timeout(datetime.timedelta(minutes=(db["timeout_duration"] if db["timeout_duration"] else 5)*offense_count),reason=f"{offense_count} offenses")
    except discord.Forbidden:
        print(f"Error: Missing permissions in channel {logging_channel_id} (Guild: {message.guild})")
