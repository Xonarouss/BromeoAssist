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
    import os, traceback

    # Explicit cog load order (stable & predictable)
    COGS_TO_LOAD = [
        "ai_gemini",
        "images_openai",
        "tts_elevenlabs",
        "tts_autoplay",
        "voice_lounge",
        "twitch_chat",
        "ambient_ai",
        "fortnite_api",
        "rebuild",
    ]

    OPTIONAL_BY_KEY = {
        "ai_gemini": "GEMINI_API_KEY",
        "images_openai": "OPENAI_API_KEY",
        "tts_elevenlabs": "ELEVENLABS_API_KEY",
        # twitch_chat may need its own credentials depending on implementation
    }

    for cog in COGS_TO_LOAD:
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

    # Diagnostics: list commands present in the local tree
    try:
        cmds = [c.qualified_name for c in self.tree.get_commands()]
        print(f"[TREE] Local commands ({len(cmds)}): {cmds}")
    except Exception as e:
        print(f"[TREE] Could not list commands: {e}")

    # Sync commands so Discord matches what this bot actually has.
    # If GUILD_ID is set, sync to that guild for instant updates.
    try:
        gid = os.getenv("GUILD_ID")
        if gid:
            import discord
            guild = discord.Object(id=int(gid))
            await self.tree.sync(guild=guild)
            print(f"[SYNC] Synced commands to guild {gid}")
        else:
            await self.tree.sync()
            print("[SYNC] Synced commands globally")
    except Exception as e:
        print(f"[SYNC] Failed to sync: {e}")

    OPTIONAL_BY_KEY = {
        "ai_gemini": "GEMINI_API_KEY",
        "images_openai": "OPENAI_API_KEY",
        "ai_openai": "OPENAI_API_KEY",
        "tts_elevenlabs": "ELEVENLABS_API_KEY",
        "twitch_live": "TWITCH_CLIENT_ID",
    }

    # auto-discover cogs
    try:
        cogs_to_load = [m.name for m in pkgutil.iter_modules(["cogs"]) if not m.name.startswith("_")]
    except Exception:
        cogs_to_load = []

    for cog in cogs_to_load:
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

    # Optional cogs that require API keys; if key missing we skip instead of crashing.
    OPTIONAL_BY_KEY = {
        "ai_gemini": "GEMINI_API_KEY",
        "images_openai": "OPENAI_API_KEY",
        "ai_openai": "OPENAI_API_KEY",
        "tts_elevenlabs": "ELEVENLABS_API_KEY",
        "twitch_live": "TWITCH_CLIENT_ID",  # if you have this cog
    }

    # Determine which cogs to load.
    # Prefer an existing list variable if present; otherwise load all modules in ./cogs
    cogs_to_load = None
    try:
        cogs_to_load = None
    except Exception:
        cogs_to_load = None

    if not cogs_to_load:
        try:
            import pkgutil
            cogs_to_load = [m.name for m in pkgutil.iter_modules(["cogs"]) if not m.name.startswith("_")]
        except Exception:
            cogs_to_load = []

    for cog in cogs_to_load:
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
            # Don't crash the whole bot because 1 cog failed.

bot = BromeoAssist()

@bot.event
async def on_ready():
    print(f"✅ Ingelogd als {bot.user} — BromeoASSIST")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN ontbreekt. Vul dit in je .env.")
    bot.run(token)
