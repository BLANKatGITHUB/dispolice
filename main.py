import discord 
import os
from dotenv import load_dotenv
from googleapiclient import discovery
import json

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

client = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey=os.getenv("perspective_api"),
  discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery=False,
)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello!')
    else:
      analyze = {
        'comment': {'text': message.content},
        'requestedAttributes': {
          'TOXICITY': {},
          'SEVERE_TOXICITY': {},
          'IDENTITY_ATTACK': {},
          'INSULT': {},
          'PROFANITY': {},
          'THREAT': {},
          'SEXUALLY_EXPLICIT': {},
          'FLIRTATION': {},
        },
        'languages': ['en']
      }
      try:
          response = client.comments().analyze(body=analyze).execute()
          scores = {
              attr: round(response['attributeScores'][attr]['summaryScore']['value'], 3)
              for attr in analyze['requestedAttributes']
          }
          
          # Sort scores by value to easily see highest risks
          sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))
          print(json.dumps(sorted_scores, indent=2))
          
          # Get highest scoring offense
          highest_offense = max(sorted_scores.items(), key=lambda x: x[1])
          offense_type, score = highest_offense

          if score > 0.7:
              await message.delete()
              warning_messages = {
                  'SEVERE_TOXICITY': '🚫 Message removed - Severely toxic content detected',
                  'THREAT': '🚫 Message removed - Threatening content is not allowed',
                  'TOXICITY': '⚠️ Message removed - Toxic content detected',
                  'IDENTITY_ATTACK': '🚫 Message removed - Identity-based attacks are not allowed',
                  'INSULT': '⚠️ Message removed - Insulting content detected',
                  'PROFANITY': '⚠️ Message removed - Excessive profanity detected',
                  'SEXUALLY_EXPLICIT': '🚫 Message removed - Sexually explicit content is not allowed',
                  'FLIRTATION': '⚠️ Message removed - Inappropriate flirtation detected'
              }
              message = warning_messages.get(offense_type, '⚠️ Message removed - Inappropriate content detected')
              await message.channel.send(f"{message.author.mention} {message}", delete_after=10)
              return
              
      except Exception as e:
          print(f"Error analyzing comment: {e}")
          await message.channel.send("couldn't analyze that message.")

try:
  TOKEN = os.getenv('TOKEN') or ""
  if TOKEN == "":
    raise Exception("Please add your token to the Secrets pane.")
  bot.run(TOKEN)
except discord.HTTPException as e:
    if e.status == 429:
        print(
            "The Discord servers denied the connection for making too many requests"
        )
        print(
            "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
        )