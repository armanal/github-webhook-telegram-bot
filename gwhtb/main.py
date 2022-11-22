# pylint: disable=wrong-import-position, unused-import, missing-module-docstring, import-error
from crypt import methods
import os
import logging
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
    CallbackQueryHandler,
)

import webhook
from webhook import Webhook
import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, request, Response

import db
import telegram_menu

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = "This is how you can use this bot\. _italic \*text_"
    await update.message.reply_text(
        help_message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
    )


async def send_github(secret, data, formatted_data):
    token = os.environ.get("TOKEN", None)
    bot = telegram.Bot(token=token)

    await bot.send_message(
        chat_id=secret.chat_id,
        text=formatted_data,
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
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
    application.add_handler(CommandHandler("menu", telegram_menu.init_menu))
    application.add_handler(CallbackQueryHandler(telegram_menu.menu_router))

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
        """https://doma.in/github?identity=IDENTITY"""
        content_type = request.headers.get("Content-Type")
        identity = request.args.get("identity", None)

        logger.debug(f"Content-Type : {content_type}")
        logger.debug(f"Got Identity : {identity}")

        if identity is None:
            return "No Identity provided", 400

        secret = db.Secret.get(identity=identity)
        if secret is None:
            logger.debug(f"Identity not found.")
            return "Invalid or unauthorized apikey", 401

        wbh = Webhook(secret=secret.secret)
        payload = wbh.postreceive(request=request)
        if payload is None:
            logger.debug(f"Hash mismatch.")
            return "Hash mismatch", 401
        data, formatted = payload

        repo_url = data["repository"]["html_url"]
        if secret.repository == "None":
            secret.repository = repo_url
        elif secret.repository != repo_url:
            logger.debug(
                f"Invalid repository {repo_url}."
                + f"Recorded repository for this secret {secret.repository}"
            )
            return "Invalid repository. Request another secret for your new repo.", 401
        secret.update()

        await send_github(secret=secret, data=data, formatted_data=formatted)

        return "OK", 204

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


if __name__ == "__main__":
    asyncio.run(main())
