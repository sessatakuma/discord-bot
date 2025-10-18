# discord-bot
A discord bot for our community

## Environment Setting
Please go [download uv](https://docs.astral.sh/uv/getting-started/installation/).

## Run the bot
To run the bot, you need to setup two environment variables first:
```bash
export BOT_TOKEN={your_bot_token}
export API_URL={your_url_to_api}
uv run bot.py
```


## Create a bot
To create a Discord bot, follow these steps:
1. Create an application at the [Discord Developer Portal](https://discord.com/developers/applications).
2. Navigate to the `Bot` section on the left panel and get the bot token, then set up your environment variables.
3. Configure the `Default Install Settings` in the `Installation` section:
    - **SCOPES**
        - `applications.commands`
        - `bot`
    - **PERMISSIONS**
        - `Embed Links`
        - `Mention Everyone`
        - `Send Messages`
        - `Use Slash Commands`
        - `View Channels`
4. Copy the `Install Link` from above and use it to invite the bot to your server.

