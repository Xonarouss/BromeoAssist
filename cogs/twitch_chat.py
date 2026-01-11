import os
import asyncio
import time
import random
from discord.ext import commands

TWITCH_IRC_HOST = "irc.chat.twitch.tv"
TWITCH_IRC_PORT = 6667

RESPOND_COOLDOWN_SEC = 2.0
REPLY_CHANCE = 0.35


class TwitchChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.username = os.getenv("TWITCH_BOT_USERNAME", "").strip()
        self.oauth = os.getenv("TWITCH_OAUTH_TOKEN", "").strip()
        self.channel = os.getenv("TWITCH_CHANNEL", "").strip().lstrip("#")

        self._task = self.bot.loop.create_task(self._main())
        self._last_reply = 0.0

    def cog_unload(self):
        try:
            self._task.cancel()
        except Exception:
            pass

    def _now(self) -> float:
        return time.time()

    async def _send(self, writer: asyncio.StreamWriter, msg: str):
        writer.write((msg + "\r\n").encode("utf-8"))
        await writer.drain()

    async def _main(self):
        await self.bot.wait_until_ready()
        if not self.username or not self.oauth or not self.channel:
            return

        while not self.bot.is_closed():
            try:
                reader, writer = await asyncio.open_connection(TWITCH_IRC_HOST, TWITCH_IRC_PORT)

                await self._send(writer, f"PASS {self.oauth}")
                await self._send(writer, f"NICK {self.username}")
                await self._send(writer, f"JOIN #{self.channel}")

                while not self.bot.is_closed():
                    line = await reader.readline()
                    if not line:
                        break
                    raw = line.decode("utf-8", errors="ignore").strip()

                    if raw.startswith("PING"):
                        await self._send(writer, "PONG :tmi.twitch.tv")
                        continue

                    if "PRIVMSG" not in raw:
                        continue

                    try:
                        prefix, msg = raw.split(" PRIVMSG ", 1)
                        user = prefix.split("!", 1)[0].lstrip(":")
                        content = msg.split(" :", 1)[1]
                    except Exception:
                        continue

                    if user.lower() == self.username.lower():
                        continue
                    if len(content.strip()) < 3:
                        continue

                    if (self._now() - self._last_reply) < RESPOND_COOLDOWN_SEC:
                        continue

                    # reageer vaker als ze je naam typen
                    if "bromeoassist" in content.lower():
                        p = 0.9
                    else:
                        p = REPLY_CHANCE

                    if random.random() > p:
                        continue

                    self._last_reply = self._now()

                    reply = ""
                    if hasattr(self.bot, "gemini_answer"):
                        prompt = f"[Twitch chat] {user}: {content}"
                        reply = await self.bot.gemini_answer(user, prompt)

                    reply = (reply or "").strip()
                    if not reply:
                        continue

                    reply = reply[:350]
                    await self._send(writer, f"PRIVMSG #{self.channel} :{reply}")

                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

            except Exception:
                await asyncio.sleep(10)


async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchChat(bot))
