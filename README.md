# discord-bot
A discord bot for our community

## Run the bot
1. You need to setup the following environment variables in your `.env` file:
    ```bash
    BOT_TOKEN={our_bot_token}
    API_URL={our_url_to_api}
    GOOGLESHEET_ID={our_google_sheet_id}
    GOOGLESHEET_PRIVATE_KEY_ID={our_googlesheet_private_key_id}
    GOOGLESHEET_PRIVATE_KEY={our_googlesheet_private_key}
    GOOGLESHEET_CLIENT_ID={our_googlesheet_client_id}
    ```
2. Go [download uv](https://docs.astral.sh/uv/getting-started/installation/) before run the bot with this command:
    ```bash
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


## Create a command
To create a command, first make a file under `/cogs`, then append this file name after `COGS` in `config/settings.py`:
```python
COGS= [
    "cogs.dict_query",
    ...,
    "cogs.{your_file_name}"
]
```

Then you can work on implementing the function of that command. Here is the quick template to build your command:
```python
import discord
from discord import app_commands
from discord.ext import commands

class YOUR_COMMAND_CLASS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="command", description="xxxxx")
    async def your_command_function(self, interaction: discord.Interaction):
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(YOUR_COMMAND_CLASS(bot))

```