# pylint: disable=wrong-import-position, unused-import, missing-module-docstring, import-error
from crypt import methods
import os
import logging
import secrets
import asyncio

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

import telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

import webhook
from webhook import Webhook
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, request, Response

import db
from db import users

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


def extract_message_fields(update: Update):
    return {
        "user_id": str(update.message.from_user.id),
        "chat_type": update.message.chat.type,
        "chat_id": str(update.message.chat.id),
    }


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = "This is how you can use this bot"
    await update.message.reply_text(help_message)


async def secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fields = extract_message_fields(update=update)
    while True:
        secret = secrets.token_hex(nbytes=20)
        if users.Secret.get(secret=secret) is None:
            break

    secret = users.Secret(secret=secret, chat_id=fields["chat_id"])

    user = users.User.get(telegram_id=fields["user_id"])
    if user is None:
        user = users.User(telegram_id=fields["user_id"])
        user.save()

    user.secrets.append(secret)

    secret.user = user
    secret.update()

    url = os.environ.get("URL", None)

    """ 
        In all other places characters 
        '_', '*', '[', ']', '(', ')', '~', '`', '>', 
        '#', '+', '-', '=', '|', '{', '}', '.', '!' 
        must be escaped with the preceding character '\'.
    """
    await update.message.reply_text(
        f"Secret:\n||{secret.secret}||\n\n\
Payload URL: \n{url}/github?identity={secret.secret}".replace(
            ".", "\."
        ).replace(
            "=", "\="
        ),
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def send_github(secret_string, data, formatted_data):
    secret = users.Secret.get(secret=secret_string)
    if secret is None:
        return

    token = os.environ.get("TOKEN", None)
    assert (
        token is not None
    ), "set environment variable TOKEN to your telegram bot's token."
    bot = telegram.Bot(token=token)

    try:
        formatted = formatted_data.replace(".", "\.").replace("=", "\=")
        await bot.send_message(
            chat_id=secret.chat_id,
            text=formatted,
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        )
    except:
        await bot.send_message(
            chat_id=secret.chat_id,
            text=formatted_data,
        )


async def main() -> None:
    """Start the bot."""
    print("*********** Setting up DB connection")
    db.global_init()

    url = os.environ.get("URL", None)
    assert url is not None, "set environment variable URL to your domain url."
    token = os.environ.get("TOKEN", None)
    assert (
        token is not None
    ), "set environment variable TOKEN to your telegram bot's token."

    # proxy_url = "socks5://127.0.0.1:1080"
    # proxy_url = "http://127.0.0.1:1081"
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder().token(token)
        # .read_timeout(30)
        # .write_timeout(30)
        # .pool_timeout(30)
        .connect_timeout(30)
        # .get_updates_read_timeout(42)
        # .proxy_url(proxy_url)
        .build()
    )

    # Add Handlers to application that will be used for handling updates
    application.add_handler(CommandHandler("start", help))
    application.add_handler(CommandHandler("secret", secret))

    # Run the bot until the user presses Ctrl-C
    # application.run_polling(poll_interval=2)

    # Pass webhook settings to telegram
    url = f"{url}/telegram"
    logger.debug(f"setting webhook url to \n\t{url}")
    await application.bot.set_webhook(url=url)

    app = Flask(__name__)

    @app.get("/health")
    def health():
        return "Hello, World!"

    @app.route("/telegram", methods=["POST"])
    async def telegram():
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        content_type = request.headers.get("Content-Type")
        logger.debug(f"Content-Type : {content_type}")
        if content_type == "application/json":
            json = request.json
            await application.update_queue.put(
                Update.de_json(data=json, bot=application.bot)
            )
            return Response()
        else:
            logger.info("Content-Type not supported!")
            return "Content-Type not supported!"

    @app.route("/github", methods=["POST"])
    async def github():
        """Handle incoming Telegram updates by putting them into the `update_queue`
        https://doma.in/github?identity=SECRET
        """
        content_type = request.headers.get("Content-Type")
        logger.debug(f"Content-Type : {content_type}")
        secret = request.args.get("identity", None)
        logger.debug(f"got secret : {secret}")
        if secret is None:
            return

        wbh = Webhook(secret=secret)
        data, formatted = wbh.postreceive(request=request)

        await send_github(secret_string=secret, data=data, formatted_data=formatted)

        return "", 204

    asgi_app = WsgiToAsgi(app)
    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=asgi_app,
            port=4560,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()

    # app.run(host="0.0.0.0", port=4560)

    # uvicorn main:app --port 4560 --host 0.0.0.0 --workers 1
    # asgi_app = WsgiToAsgi(app)
    # uvicorn.run("main:asgi_app", host="0.0.0.0", port=4560, log_level="info")


if __name__ == "__main__":
    asyncio.run(main())
