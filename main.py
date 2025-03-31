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
        "comment": message.content,
        "requestedAttributes": {
          "TOXICITY": {},
          "SEVERE_TOXICITY": {},
          "IDENTITY_ATTACK": {},
          "INSULT": {},
          "PROFANITY": {},
          "THREAT": {},
          "SEXUALLY_EXPLICIT": {},
          "FLIRTATION": {},
        },
        "languages": ["en"]
      }
      response = await client.comments().analyze(body=analyze).execute()  
      print(json.dumps(response, indent=2))

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