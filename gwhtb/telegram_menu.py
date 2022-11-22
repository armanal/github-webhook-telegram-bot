import os
from typing import Any
import functools
import secrets
import logging

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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)

import db
from tools import markdown_char_escape


logger = logging.getLogger(__name__)


def extract_message_fields(update: Update):
    return {
        "user_id": str(update.message.from_user.id),
        "chat_type": update.message.chat.type,
        "chat_id": str(update.message.chat.id),
    }


def extract_callback_query_fields(update: Update):
    return {
        "user_id": str(update.callback_query.from_user.id),
        "chat_type": update.callback_query.message.chat.type,
        "chat_id": str(update.callback_query.message.chat.id),
    }


def reply_func(update: Update):
    if hasattr(update.callback_query, "edit_message_text"):
        func = update.callback_query.edit_message_text
    else:
        func = update.message.reply_text
    return func


def get_state_context(data):
    logger.debug(f"got keyboard context : {data}")
    if "-" in data:
        dlist = data.split("-")
        state, context = dlist[0], dlist[1:]
    else:
        state, context = data, None
    return state, context


async def init_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fields = extract_message_fields(update=update)
    return await state_dict["7917"](update, context, fields=fields)


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fields = extract_callback_query_fields(update=update)

    query = update.callback_query
    await query.answer()

    state, fields["context"] = get_state_context(query.data)

    if state in state_dict.keys():
        return await state_dict[state](update, context, fields=fields)
    elif state == "none":
        return await reply_func(update)(
            text=f"Action is not supported yet. \
developers are working on it. Please be patient"
        )
    else:
        return await reply_func(update)(text=f"Invalid state.")


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, fields) -> None:
    keyboard = [
        [
            InlineKeyboardButton("new secret", callback_data="30564"),
            InlineKeyboardButton("my secrets", callback_data="20356"),
        ],
        [
            InlineKeyboardButton("exit", callback_data="6491"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await reply_func(update=update)("Please choose:", reply_markup=reply_markup)


async def secret(update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict):
    while True:
        identity = secrets.token_hex(nbytes=20)
        if db.Secret.get(identity=identity) is None:
            break

    secret = secrets.token_hex(nbytes=20)
    secret = db.Secret(identity=identity, secret=secret, chat_id=fields["chat_id"])

    user = db.User.get(telegram_id=fields["user_id"])
    if user is None:
        user = db.User(telegram_id=fields["user_id"])
        user.save()

    user.secrets.append(secret)

    secret.user = user
    secret.update()

    url = os.environ.get("URL", None)

    await reply_func(update)(
        f"Secret:\n||{markdown_char_escape(str(secret.secret))}||\n\n\
Payload URL: \n{markdown_char_escape(url)}/github?identity\={markdown_char_escape(secret.identity)}",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def my_secrets(update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict):
    user = db.User.get(telegram_id=fields["user_id"])
    secrets_list = db.Secret.objects(user=user)

    keyboard = [
        [
            InlineKeyboardButton(
                str(secret.identity), callback_data=f"20243-{str(secret.identity)}"
            )
        ]
        for secret in secrets_list
    ]
    keyboard += [
        [
            InlineKeyboardButton("back", callback_data="7917"),
            InlineKeyboardButton("exit", callback_data="6491"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await reply_func(update=update)(
        "Please choose a secret:", reply_markup=reply_markup
    )


async def secrets_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict
):
    keyboard = [
        [
            InlineKeyboardButton("info", callback_data=f"16336-{fields['context'][0]}"),
            InlineKeyboardButton(
                "delete", callback_data=f"18787-{fields['context'][0]}"
            ),
        ],
        [
            InlineKeyboardButton("back", callback_data="20356"),
            InlineKeyboardButton("exit", callback_data="6491"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await reply_func(update=update)("Please choose:", reply_markup=reply_markup)


async def secret_info(update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict):
    secret = db.Secret.get(identity=fields["context"][0])
    url = os.environ.get("URL", None)

    await reply_func(update)(
        f"Secret:\n||{markdown_char_escape(str(secret.secret))}||\n\n\
Repository: \n {markdown_char_escape(secret.repository)} \n\n\
Payload URL: \n{markdown_char_escape(url)}/github?identity\={markdown_char_escape(secret.identity)}",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def secret_delete(
    update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict
):
    secret = db.Secret.get(identity=fields["context"][0])
    identity = secret.identity
    repository = secret.repository
    secret_srt = secret.secret
    secret.delete()
    url = os.environ.get("URL", None)

    await reply_func(update)(
        f"*Deleted the following secret*:\n\n\
Secret:\n||{markdown_char_escape(secret_srt)}||\n\n\
Repository: \n {markdown_char_escape(repository)} \n\n\
Payload URL: \n{markdown_char_escape(url)}/github?identity\={markdown_char_escape(identity)}",
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
    )


async def exit(update: Update, context: ContextTypes.DEFAULT_TYPE, fields: dict):
    await reply_func(update)("🌸")


state_dict = {
    "7917": main_menu,
    "30564": secret,
    "20356": my_secrets,
    "20243": secrets_menu,
    "16336": secret_info,
    "18787": secret_delete,
    "6491": exit,
}
