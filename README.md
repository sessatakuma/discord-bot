# discord-bot
A discord bot for our community

## Environment Setting
```bash
conda create -n dcbot python=3.10 -y
conda activate dcbot
pip install -r requirements.txt
```

## Run the bot
To run the bot, you need to setup two environment variables first:
```bash
export BOT_TOKEN={your_bot_token}
export API_URL={your_url_to_api}
python bot.py
```
