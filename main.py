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
          
          # You can now easily check specific thresholds
          if sorted_scores['TOXICITY'] > 0.8:
              await message.channel.send(f"{message.author} ⚠️ Warning: Message detected as highly toxic",delete_after=5)
              await message.delete()
              
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