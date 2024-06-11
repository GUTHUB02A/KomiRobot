from ShoukoRobot import DRAGONS, dispatcher
from telegram.ext import CallbackContext, CommandHandler
from telegram import ParseMode, Update , ChatAdministratorRights


def rights(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message

    if bot.ChatAdministratorRights("is_anonymous =True ", chat.id):
        text += "komi have power of anonymous"
    else:
        ""
    if bot.ChatAdministratorRights("can_manage_chat =True ", chat.id):
        text += "komi have power of anonymous"
    else:
        ""
    if bot.ChatAdministratorRights("can_delete_messages =True ", chat.id):
        text += "komi have power of anonymous"
    else:
        ""

RIGHTS_HANDLER = CommandHandler("rights" , rights)

dispatcher.add_handler(RIGHTS_HANDLER)
