import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True

COGS = ['ai_gemini', 'ambient_ai', 'fortnite_api', 'images_openai', 'rebuild', 'tts_autoplay', 'tts_elevenlabs', 'twitch_chat', 'voice_lounge']

# Cogs that require certain env vars. If missing, we skip the cog (bot stays online).
OPTIONAL_BY_KEY = {
    "ai_gemini": "GEMINI_API_KEY",
    "images_openai": "OPENAI_API_KEY",
    "tts_elevenlabs": "ELEVENLABS_API_KEY",
}

class BromeoAssist(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=INTENTS)

    async def setup_hook(self):
        import traceback

        for cog in COGS:
            key = OPTIONAL_BY_KEY.get(cog)
            if key and not os.getenv(key):
                print(f"[SKIP] cogs.{cog} (missing {key})")
                continue

            try:
                await self.load_extension(f"cogs.{cog}")
                print(f"[OK] Loaded cogs.{cog}")
            except Exception as e:
                print(f"[FAIL] cogs.{cog}: {e}")
                traceback.print_exc()

        # Show what slash commands exist locally (debug)
        try:
            cmds = [c.qualified_name for c in self.tree.get_commands()]
            print(f"[TREE] Local slash commands ({len(cmds)}): {cmds}")
        except Exception as e:
            print(f"[TREE] Could not list commands: {e}")

        # Sync slash commands: use guild sync if GUILD_ID is set (instant),
        # otherwise global sync (can take longer).
        try:
            gid = os.getenv("GUILD_ID")
            if gid:
                guild = discord.Object(id=int(gid))
                await self.tree.sync(guild=guild)
                print(f"[SYNC] Synced commands to guild {gid}")
            else:
                await self.tree.sync()
                print("[SYNC] Synced commands globally")
        except Exception as e:
            print(f"[SYNC] Failed to sync: {e}")

bot = BromeoAssist()

@bot.event
async def on_ready():
    print(f"✅ Ingelogd als {bot.user} — BromeoASSIST")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN ontbreekt. Zet DISCORD_TOKEN in Coolify.")
    bot.run(token)
