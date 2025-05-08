
# Dispolice

**Dispolice** is a powerful and intelligent Discord moderation bot developed in Python. It leverages **Natural Language Processing (NLP)** and integrates with **Google's Perspective API** to identify harmful or hateful content in Discord servers and take appropriate moderation actions. The bot aims to foster safer and more respectful online communities.

---

## Features

- **Real-time Moderation**: Detects harmful, toxic, or hateful messages in real-time.
- **Google Perspective API Integration**: Utilizes advanced sentiment analysis to evaluate message toxicity.
- **Automated Actions**:
  - Warns users for inappropriate behavior.
  - Deletes harmful messages.
  - Temporarily or permanently bans repeat offenders.
- **Customizable Settings**: Configure moderation rules and thresholds to suit your server's needs.
- **Scalable**: Designed to handle servers of all sizes with efficiency.

---

## Technologies Used

- **Python**: The core programming language for the bot.
- **Discord.py**: A Python wrapper for the Discord API to handle bot interactions.
- **Google Perspective API**: For toxicity scoring and content moderation.
- **Natural Language Processing (NLP)**: To process and analyze message content.

---

## Installation

Follow these steps to set up Dispolice on your local environment:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/BLANKatGITHUB/dispolice.git
   cd dispolice
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # For Linux/macOS
   venv\Scripts\activate     # For Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```
     DISCORD_TOKEN=your_discord_bot_token
     PERSPECTIVE_API_KEY=your_google_perspective_api_key
     ```

5. **Run the Bot**:
   ```bash
   python bot.py
   ```

---

## Usage

1. Invite the bot to your Discord server by generating an invite link with the required permissions.
2. Configure moderation settings using the bot's commands or configuration files.
3. Let the bot automatically monitor and moderate your server.

---

## Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---


## Acknowledgements

- [Discord.py](https://github.com/Rapptz/discord.py): For simplifying Discord bot development.
- [Google Perspective API](https://perspectiveapi.com/): For advanced content analysis and toxicity detection.

---
