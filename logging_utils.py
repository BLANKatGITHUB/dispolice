import discord
import datetime
# Hardcoded logging channel ID (change as needed)
LOGGING_CHANNEL_ID = 1356741431250653355

async def log_moderation_event(message: discord.Message, offense_type: str, score: float, timeout_duration: datetime.timedelta|None = None):
    try:
        logging_channel = message.guild.get_channel(LOGGING_CHANNEL_ID)
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
