import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True  # handig voor member info, mag aan


class BromeoAssist(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)

    async def setup_hook(self):
        for cog in ("ai_gemini", "images_openai", "tts_elevenlabs", "fortnite_api", "music", "rebuild", "ambient_ai","ai_gemini", "ambient_ai", "voice_lounge", "tts_autoplay", "twitch_chat",):
            await self.load_extension(f"cogs.{cog}")
        await self.tree.sync()

bot = BromeoAssist()

@bot.event
async def on_ready():
    print(f"✅ Ingelogd als {bot.user} — BromeoASSIST")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN ontbreekt. Vul dit in je .env.")
    bot.run(token)
