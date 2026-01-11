import os
import base64
import io
import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI

class ImagesOpenAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY ontbreekt in .env")
        self.client = OpenAI(api_key=key)

    @app_commands.command(name="image", description="Genereer een AI-afbeelding (OpenAI).")
    @app_commands.describe(prompt="Beschrijf wat je wilt zien.")
    async def image(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(thinking=True)

        img = self.client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
        )

        b64 = img.data[0].b64_json
        data = base64.b64decode(b64)

        file = discord.File(fp=io.BytesIO(data), filename="bromeo.png")
        await interaction.followup.send("🖼️ Hier is je afbeelding!", file=file)

async def setup(bot):
    await bot.add_cog(ImagesOpenAICog(bot))
