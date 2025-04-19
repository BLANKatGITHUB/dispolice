import discord
import datetime
from logging_utils import log_moderation_event, offense_count_log
from replit import db # Assuming replit.db is necessary for your environment

# Base warning messages for various offense types
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


async def handle_moderation(message: discord.Message, offense_type: str, score: float, overall_score: int, filter_scores: list[float]):
    """Handles moderation actions based on offense type and scores."""

    if not message.guild:
        print(f"Cannot moderate message {message.id} (not in a guild).")
        return

    guild_id = str(message.guild.id)
    settings =  db.get(guild_id) # Fetch settings using cache

    base_warning = BASE_WARNING_MESSAGES.get(offense_type, DEFAULT_WARNING)
    full_warning = f"{message.author.mention} {base_warning}"
    timeout_duration = None
    ping_moderators = False
    delete_after_warning = 10 # Default delete time for warnings below high threshold
    reason = f"Content flagged for {offense_type} (Score: {score:.3f})"

    # Determine specific actions based on score threshold
    if overall_score >= filter_scores[2]:
        full_warning += " User temporarily muted."
        ping_moderators = True
        # Use cached settings for timeout duration
        timeout_minutes = settings.get('timeout_duration', 5)
        timeout_duration = datetime.timedelta(minutes=timeout_minutes)
        delete_after_warning = 0 # Warning message persists if mods are pinged
    elif overall_score > filter_scores[1]:
        full_warning += " Moderator review advised."
        ping_moderators = True
        delete_after_warning = 0 # Warning message persists if mods are pinged

    # Fetch and mention moderator role if needed
    if ping_moderators:
        mod_role_id = settings.get('mod_role_id') # Use cached settings
        if mod_role_id:
            try:
                moderator_role = message.guild.get_role(mod_role_id)
                if moderator_role:
                    full_warning += f" {moderator_role.mention}"
                else:
                    print(f"Warning: Could not find role with ID {mod_role_id} in guild {message.guild.name}")
            except Exception as e:
                print(f"Error fetching role {mod_role_id} in guild {message.guild.name}: {e}")
        else:
             print(f"Warning: No moderator role ID set for guild {message.guild.name}")


    # Send warning, delete message, and apply timeout if necessary
    try:
        # Send the warning message
        warning_message = await message.channel.send(full_warning, delete_after=delete_after_warning if delete_after_warning > 0 else None)

        # Delete the original message
        await message.delete()
        print(f"Deleted message {message.id} by {message.author} for {offense_type} ({score:.3f})")

        # Apply timeout if required
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

    # Log moderation event if conditions met
    # Threshold for logging remains the same based on overall_score
    if overall_score > filter_scores[0]: # Log anything above the lowest threshold
        logging_channel_id = settings.get('logging_channel_id') # Use cached settings
        if logging_channel_id:
            try:
                logging_channel = message.guild.get_channel(logging_channel_id)
                if logging_channel:
                    await log_moderation_event(message, offense_type, score, logging_channel, timeout_duration)
                    await offense_count_log(message, offense_type, message.content, logging_channel)
                else:
                     print(f"Warning: Could not find logging channel with ID {logging_channel_id} in guild {message.guild.name}")
            except Exception as e:
                 print(f"Error sending log messages in guild {message.guild.name}: {e}")
        else:
            print(f"Warning: No logging channel ID set for guild {message.guild.name}")


# function to give list of thresholds
def get_thresholds(n):
    """Calculates moderation thresholds based on a base value n."""
    # No change needed here, it's clear and efficient
    return [n * 0.3, n * 0.4, n * 0.5]

def has_moderator_perms(user: discord.Member):
    """Checks if a user has moderator permissions."""
    # No change needed here, it's clear and efficient
    return user.guild_permissions.manage_messages