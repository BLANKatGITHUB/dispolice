import discord
import datetime
from logging_utils import log_moderation_event

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

# Hardcoded moderator role ID for pings (change as needed)
MOD_ROLE_ID = 1356674452095635747

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
    if score > 0.9 and count > 2:
        full_warning += " User temporarily muted for 5 minutes."
        ping_role = True
        timeout_duration = datetime.timedelta(minutes=5)
    elif score > 0.8 and count > 2:
        full_warning += " Moderator review advised."
        ping_role = True

    elif score > 0.7 and count > 2:
        await message.channel.send(full_warning,delete_after=10)


    # Fetch and mention moderator role if needed
    if ping_role:
        try:
            moderator_role = message.guild.get_role(MOD_ROLE_ID)
            if moderator_role:
                full_warning += f" {moderator_role.mention}"
            else:
                print(f"Warning: Could not find role with hardcoded ID {MOD_ROLE_ID} in guild {message.guild.name}")
        except Exception as e:
            print(f"Error fetching role {MOD_ROLE_ID} in guild {message.guild.name}: {e}")

    # Send warning, delete message, and apply timeout if necessary
    try:
        await message.channel.send(full_warning)
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

    # Log moderation event if conditions met
    if score > 0.8 and count > 2:
        await log_moderation_event(message, offense_type, score, timeout_duration)
