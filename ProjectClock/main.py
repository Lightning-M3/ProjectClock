import asyncio
import os
import signal
import sys
from dotenv import load_dotenv

import disnake

from timeclock import database, log
from timeclock.bot import TimeClockBot

# Load environment variables
load_dotenv()

# Get environment variables
TIMECLOCK_TOKEN = os.getenv('TIMECLOCK_TOKEN')
TIMECLOCK_MONGODB_URI = os.getenv('TIMECLOCK_MONGODB_URI')

logger = log.get_logger(__name__)

_intents = disnake.Intents.default()
_intents.members = True


async def main() -> None:
    """Create and run the bot"""

    bot: TimeClockBot = TimeClockBot(intents=_intents)
    await check_database(bot)

    try:
        bot.load_extensions()
    except Exception:
        await bot.close()
        raise

    logger.info("Bot is starting...")

    if os.name != "nt":
        loop = asyncio.get_event_loop()

        future = asyncio.ensure_future(bot.start(TIMECLOCK_TOKEN), loop=loop)
        loop.add_signal_handler(signal.SIGINT, lambda: future.cancel())
        loop.add_signal_handler(signal.SIGTERM, lambda: future.cancel())

        try:
            await future
        except asyncio.CancelledError:
            logger.warning("Kill command was sent to the bot. Closing bot and event loop")
            if not bot.is_closed():
                await bot.close()
    else:
        await bot.start(TIMECLOCK_TOKEN)
