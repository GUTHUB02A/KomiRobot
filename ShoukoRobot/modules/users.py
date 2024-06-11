import os
from io import BytesIO
from time import sleep

import ShoukoRobot.modules.sql.users_sql as sql
from ShoukoRobot import DEV_USERS, LOGGER, OWNER_ID, dispatcher
from ShoukoRobot.modules.helper_funcs.chat_status import dev_plus, sudo_plus
from ShoukoRobot.modules.sql.users_sql import get_all_users , get_user_com_chats
from telegram import TelegramError, Update
from telegram.error import BadRequest ,RetryAfter, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)

USERS_GROUP = 4
CHAT_GROUP = 5
DEV_AND_MORE = DEV_USERS.append(int(OWNER_ID))


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith('@'):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == 'Chat not found':
                    pass
                else:
                    LOGGER.exception("Error extracting user ID")

    return None



@dev_plus
def broadcast(update: Update, context: CallbackContext):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = False
        to_user = False
        if to_send[0] == '/broadcastgroups':
            to_group = True
        if to_send[0] == '/broadcastusers':
            to_user = True
        else:
            to_group = to_user = True
        chats = sql.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    context.bot.sendMessage(
                        int(chat.chat_id),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True)
                    sleep(0.1)
                except TelegramError:
                    failed += 1
        if to_user:
            for user in users:
                try:
                    context.bot.sendMessage(
                        int(user.user_id),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True)
                    sleep(0.1)
                except TelegramError:
                    failed_user += 1
        update.effective_message.reply_text(
            f"Broadcast complete.\nGroups failed: {failed}.\nUsers failed: {failed_user}."
        )



def log_user(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id,
                    chat.title)

    if msg.reply_to_message:
        sql.update_user(msg.reply_to_message.from_user.id,
                        msg.reply_to_message.from_user.username, chat.id,
                        chat.title)

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)



@sudo_plus
def chats(update: Update, context: CallbackContext):
    all_chats = sql.get_all_chats() or []
    chatfile = 'List of chats.\n0. Chat name | Chat ID | Members count\n'
    P = 1
    for chat in all_chats:
        try:
            curr_chat = context.bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(context.bot.id)
            chat_members = curr_chat.get_members_count(context.bot.id)
            chatfile += "{}. {} | {} | {}\n".format(P, chat.chat_name,
                                                    chat.chat_id, chat_members)
            P = P + 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "groups_list.txt"
        update.effective_message.reply_document(
            document=output,
            filename="groups_list.txt",
            caption="Here be the list of groups in my database.")

def get_user_common_chats(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = extract_user(msg, args)
    if not user:
        msg.reply_text("I share no common chats with the void.")
        return
    common_list = get_user_com_chats(user)
    if not common_list:
        msg.reply_text("No common chats with this user!")
        return
    name = bot.get_chat(user).first_name
    text = f"<b>Common chats with {name}</b>\n"
    for chat in common_list:
        try:
            chat_name = bot.get_chat(chat).title
            sleep(0.3)
            text += f"• <code>{chat_name}</code>\n"
        except BadRequest:
            pass
        except Unauthorized:
            pass
        except RetryAfter as e:
            sleep(e.retry_after)

    if len(text) < 4096:
        msg.reply_text(text, parse_mode="HTML")
    else:
        with open("common_chats.txt", 'w') as f:
            f.write(text)
        with open("common_chats.txt", 'rb') as f:
            msg.reply_document(f)
        os.remove("common_chats.txt")


def chat_checker(update: Update, context: CallbackContext):
    bot = context.bot
    if update.effective_message.chat.get_member(
            bot.id).can_send_messages is False:
        bot.leaveChat(update.effective_message.chat.id)


def __user_info__(user_id):
    if user_id in [777000, 1087968824]:
        return """I've seen them in <code>infinity</code> chats in total."""
    if user_id == dispatcher.bot.id:
        return """I've seen them in <code>infinity</code> chats in total."""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""I've seen them in <code>{num_chats}</code> chats in total."""


def __stats__():
    return f"• {sql.num_users()} users, across {sql.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

BROADCAST_HANDLER = CommandHandler(
    ["broadcastall", "broadcastusers", "broadcastgroups"], broadcast)
USER_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, log_user)
CHAT_CHECKER_HANDLER = MessageHandler(Filters.all & Filters.chat_type.groups, chat_checker)
CHATLIST_HANDLER = CommandHandler("groups", chats)
GET_USER_COMMON_CHATS = CommandHandler("get_user_common_chats" , get_user_common_chats)
dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)
dispatcher.add_handler(GET_USER_COMMON_CHATS)
__mod_name__ = "Users"
__handlers__ = [(USER_HANDLER, USERS_GROUP), BROADCAST_HANDLER,
                CHATLIST_HANDLER , GET_USER_COMMON_CHATS]
