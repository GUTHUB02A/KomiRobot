from telegram import  Update 
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)
from ShoukoRobot import OWNER_USERNAME
from ShoukoRobot import OWNER_ID , SUPPORT_CHAT ,dispatcher
from ShoukoRobot.modules.helper_funcs.extraction import extract_user

def bug(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user =  extract_user(message, args)
    to_send = update.effective_message.text.split(None, 1)

    thumbnail = ""
    bug = to_send

    bug_report = f"""
**#BUG : ** **@{OWNER_USERNAME}**

**Group : ** **{chat.username}**

**Bug Report : ** **{bug}**"""
    
    if chat.type == "private":
        update.effective_message.reply_text("this only work in public group")


    if user.id == OWNER_ID :
        if bug :
            update.effective_message.reply_text("Noob Onwer")

    if user.id != OWNER_ID :
        if bug:
            update.effective_message.reply_text("The bug was successfully reported to the support group!</b>")

            dispatcher.bot.sendMessage(
                f"@{SUPPORT_CHAT}" ,
                photo = thumbnail,
                caption = f"{bug_report}",
            )
        else:
            None

BUG_HANDLER = CommandHandler("bug", bug)

dispatcher.add_handler(BUG_HANDLER)




