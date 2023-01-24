import os

import dotenv
import discord
from discord.ext import commands

dotenv.load_dotenv()


def getenv(key: str) -> str:
    env = os.getenv(key)
    if not env:
        raise RuntimeError(f"{key} not set in .env")
    return env


class BBBot(commands.Bot):
    EXTS = ["ext.todo", "jishaku"]

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            help_command=None,
            intents=discord.Intents.default() | discord.Intents(message_content=True),
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/new-todo"
            ),
            status=discord.Status.idle,
        )

    async def setup_hook(self) -> None:
        for ext in self.EXTS:
            await self.load_extension(ext)


bot = BBBot()


bot.run(getenv("TOKEN"))
