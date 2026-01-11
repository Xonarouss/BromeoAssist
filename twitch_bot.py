import os
from dotenv import load_dotenv
from twitchio.ext import commands

load_dotenv()

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.getenv("TWITCH_ACCESS_TOKEN"),
            client_id=os.getenv("TWITCH_CLIENT_ID"),
            client_secret=os.getenv("TWITCH_CLIENT_SECRET"),
            bot_id=os.getenv("TWITCH_BOT_ID"),
            prefix="!",
            initial_channels=[os.getenv("TWITCH_CHANNEL")]
        )

    async def event_ready(self):
        print(f"✅ Twitch bot online als {self.user.name}")

@commands.command(name="ping")
async def ping(self, ctx):
    await ctx.send("🏓 Pong! BromeoASSIST is online.")


    async def event_message(self, message):
        if message.echo:
            return

        print(f"[{message.channel.name}] {message.author.name}: {message.content}")
        await self.handle_commands(message)

bot = TwitchBot()
bot.run()

