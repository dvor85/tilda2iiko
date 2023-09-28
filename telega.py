#!/usr/bin/env python3

import config
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your chat_id={update.effective_chat.id}")


async def send_message(text):
    bot = Bot(config.TELEGRAM_TOKEN)
    async with bot:
        for chat_id in config.TELEGRAM_CHATS:
            await bot.send_message(text=text, chat_id=chat_id)


if __name__ == '__main__':
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()
