import os
import io
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

ELEVEN_API = "https://api.elevenlabs.io/v1/text-to-speech"

class TTSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tts", description="Tekst naar spraak (ElevenLabs).")
    @app_commands.describe(tekst="Wat moet BromeoASSIST zeggen?")
    async def tts(self, interaction: discord.Interaction, tekst: str):
        await interaction.response.defer(thinking=True)

        api_key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        if not api_key or not voice_id:
            return await interaction.followup.send("❌ ELEVENLABS_API_KEY of ELEVENLABS_VOICE_ID ontbreekt in .env")

        url = f"{ELEVEN_API}/{voice_id}/convert"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": tekst,
            "model_id": "eleven_multilingual_v2"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as r:
                if r.status != 200:
                    body = await r.text()
                    return await interaction.followup.send(f"❌ ElevenLabs fout: {r.status}\n```{body[:1500]}```")
                audio = await r.read()

        file = discord.File(fp=io.BytesIO(audio), filename="bromeoassist.mp3")
        await interaction.followup.send("🔊 BromeoASSIST spreekt:", file=file)

async def setup(bot):
    await bot.add_cog(TTSCog(bot))
