from random import randint
from pprint import pprint
from akinator import Akinator

from ShoukoRobot import dispatcher
from telegram import Update, ParseMode ,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.files.inputmedia import InputMediaPhoto
from ShoukoRobot.modules.helper_funcs.chat_status import sudo_plus
from telegram.ext import  CommandHandler, CallbackContext, CallbackQueryHandler
from os import cpu_count, terminal_size

import akinator
from ShoukoRobot.database import (
    addUser, 
    getChildMode, 
    getCorrectGuess, 
    getLead, 
    getTotalGuess, 
    getTotalQuestions, 
    getUnfinishedGuess, 
    getUser, getWrongGuess, 
    totalUsers, 
    updateChildMode, 
    updateCorrectGuess,  
    updateTotalGuess, 
    updateTotalQuestions, 
    updateWrongGuess)

AKI_PLAY_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Yes", callback_data='aki_play_0'),
            InlineKeyboardButton("No", callback_data='aki_play_1'),
            InlineKeyboardButton("Probably", callback_data='aki_play_3')
        ],
        [
            InlineKeyboardButton("I don't know", callback_data='aki_play_2'),
            InlineKeyboardButton("Probably Not", callback_data='aki_play_4')
        ],
        [   InlineKeyboardButton("Back", callback_data= 'aki_play_5')
        ]
    ]
)

AKI_WIN_BUTTON = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Yes", callback_data='aki_win_y'),
            InlineKeyboardButton("No", callback_data='aki_win_n'),
        ]
    ]
)

AKI_LEADERBOARD_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Total Guesses", callback_data='aki_lead_tguess'),
            InlineKeyboardButton("Correct Guesses", callback_data='aki_lead_cguess'),
        ],
        [
            InlineKeyboardButton("Wrong Guesses", callback_data='aki_lead_wguess'),
            InlineKeyboardButton("Total Questions", callback_data='aki_lead_tquestions'),
        ]
    ]
)

CHILDMODE_BUTTON = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Enable", callback_data='c_mode_1'),
            InlineKeyboardButton("Disable", callback_data='c_mode_0')
        ]
    ]
)


def aki_play(update: Update, context: CallbackContext) -> None:

    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    user_name = update.effective_user.username
    addUser(user_id, first_name, last_name, user_name)
    aki = Akinator()
    msg = update.message.reply_photo(
        photo=open('ShoukoRobot/resources/komiimg/komi1.jpg', 'rb'),
        caption="Loading..."
    )
    updateTotalGuess(user_id, total_guess=1)
    q = aki.start_game(child_mode=getChildMode(user_id))
    context.user_data[f"aki_{user_id}"] = aki
    context.user_data[f"q_{user_id}"] = q
    context.user_data[f"ques_{user_id}"] = 1
    msg.edit_caption(
        caption=q,
        reply_markup=AKI_PLAY_KEYBOARD
        )

@sudo_plus
def aki_find(update: Update, context: CallbackContext) -> None:
    total_users = totalUsers()
    update.message.reply_text(f"Users : {total_users}")


def aki_ply_callback_handler(update: Update, context:CallbackContext) -> None:
    user_id = update.effective_user.id
    aki = context.user_data[f"aki_{user_id}"]
    q = context.user_data[f"q_{user_id}"]
    updateTotalQuestions(user_id, 1)
    query = update.callback_query
    a = query.data.split('_')[-1]
    if a == '5':
        updateTotalQuestions(user_id, -1)
        try:
            q = aki.back()
        except akinator.exceptions.CantGoBackAnyFurther:
            query.answer(text="This is the first question. You can't go back any further!", show_alert=True)
            return
    else:
        q = aki.answer(a)
    query.answer()
    if aki.progression < 80:
        query.message.edit_media(
            InputMediaPhoto(
                open(f'ShoukoRobot/resources/komiimg/komi1.jpg', 'rb'),
                caption=q,
            ),
            reply_markup=AKI_PLAY_KEYBOARD
        )
        context.user_data[f"aki_{user_id}"] = aki
        context.user_data[f"q_{user_id}"] = q
    else:
        aki.win()
        aki = aki.first_guess
        if aki['picture_path'] == 'none.jpg':
            aki['absolute_picture_path'] = open('ShoukoRobot/resources/komiimg/komi1.jpg', 'rb')
        query.message.edit_media(
            InputMediaPhoto(media=aki['absolute_picture_path'],
            caption=f"It's {aki['name']} ({aki['description']})! Was I correct?"
            ),
            reply_markup=AKI_WIN_BUTTON
        )
        del_data(context, user_id)


def aki_win(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    query = update.callback_query
    ans = query.data.split('_')[-1]
    if ans =='y':
        query.message.edit_media(
            InputMediaPhoto(
                media=open('ShoukoRobot/resources/komiimg/komi1.jpg', 'rb'),
                caption="gg!"
            ),
            reply_markup=None
        )
        updateCorrectGuess(user_id=user_id, correct_guess=1)
    else:
        query.message.edit_media(
            InputMediaPhoto(
                media=open('ShoukoRobot/resources/komiimg/komi1.jpg', 'rb'),
                caption="bruh :("
            ),
            reply_markup=None
        )
        updateWrongGuess(user_id=user_id, wrong_guess=1)

ME_MSG = """
<b>Name :</b> <code>{}</code>
<b>User Name :</b> <code>{}</code>
<b>User ID :</b> <code>{}</code>
<b>Language :</b> <code>{}</code>
<b>Child Mode :</b> <code>{}</code>
<b>Total Guess :</b> <code>{}</code>
<b>Correct Guess :</b> <code>{}</code>
<b>Wrong Guess :</b> <code>{}</code>
<b>Unfinished Guess :</b> <code>{}</code>
<b>Total Questions :</b> <code>{}</code>
"""


def aki_me(update: Update, context: CallbackContext) -> None:
    #/me command
    user_id = update.effective_user.id
    profile_pic = update.effective_user.get_profile_photos(limit=1).photos
    if len(profile_pic) == 0:
        profile_pic = "https://telegra.ph/file/a65ee7219e14f0d0225a9.png"
    else:
        profile_pic = profile_pic[0][1]
    user = getUser(user_id)
    update.message.reply_photo(photo= profile_pic, 
                               caption=ME_MSG.format(user["first_name"], 
                                                     user["user_name"], 
                                                     user["user_id"],
                                                     "Enabled" if getChildMode(user_id) else "Disabled",
                                                     getTotalGuess(user_id),
                                                     getCorrectGuess(user_id),
                                                     getWrongGuess(user_id),
                                                     getUnfinishedGuess(user_id),
                                                     getTotalQuestions(user_id),
                                                     ),
                               parse_mode=ParseMode.HTML)



def aki_childmode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    status = "enabled" if getChildMode(user_id) else "disabled"
    update.message.reply_text(
        text="""If Child mode is enabled, akinator won't show any NSFW content. <b>Current Status :</b> <pre>Child mode is {} !</pre>""".format(status),
        parse_mode=ParseMode.HTML,
        reply_markup=CHILDMODE_BUTTON
    )


def aki_set_child_mode(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    query = update.callback_query
    to_set = int(query.data.split('_')[-1])
    updateChildMode(user_id, to_set)
    query.edit_message_text(f"Child mode is {'enabled' if to_set else 'disabled'} Successfully!")


def del_data(context:CallbackContext, user_id: int):
    del context.user_data[f"aki_{user_id}"]
    del context.user_data[f"q_{user_id}"]


def aki_lead(update: Update, _:CallbackContext) -> None:
    update.message.reply_text(
        text="Check Leaderboard on specific categories in Akinator.",
        reply_markup=AKI_LEADERBOARD_KEYBOARD
    )


def get_lead_total(lead_list: list, lead_category: str) -> str:
    lead = f'Top 10 {lead_category} are :\n'
    for i in lead_list:
        lead = lead+f"{i[0]} : {i[1]}\n"
    return lead


def aki_lead(update: Update, context:CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')[-1]
    #print(data)
    if data == 'cguess':
        text = get_lead_total(getLead("correct_guess"), 'correct guesses')
        query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'tguess':
        text = get_lead_total(getLead("total_guess"), 'total guesses')
        query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'wguess':
        text = get_lead_total(getLead("wrong_guess"), 'wrong guesses')
        query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )
    elif data == 'tquestions':
        text = get_lead_total(getLead("total_questions"), 'total questions')
        query.edit_message_text(
            text= text,
            reply_markup=AKI_LEADERBOARD_KEYBOARD
        )


AKI_PLAY_HANDLER = CommandHandler("guess" ,aki_play)
AKI_FIND_HANDLER = CommandHandler("find", aki_find)
AKI_ME_HANDLER = CommandHandler("me", aki_me)
AKI_LEAD_HANDLER =  CommandHandler("leaderboard", aki_lead)
AKI_CHILDMODE_HANDLER = CommandHandler("childmode",aki_childmode)
aki_play_callback_handler = CallbackQueryHandler(aki_ply_callback_handler ,pattern =r"aki_play_")
aki_win_callback_handler = CallbackQueryHandler(aki_win , pattern =r"aki_win_")
aki_set_child_mode_callback_handler = CallbackQueryHandler(aki_set_child_mode , pattern = r"c_mode_")
aki_lead_callback_hanlder = CallbackQueryHandler(aki_lead, pattern=r"aki_lead_")

dispatcher.add_handler(AKI_CHILDMODE_HANDLER)
dispatcher.add_handler(AKI_FIND_HANDLER)
dispatcher.add_handler(AKI_LEAD_HANDLER)
dispatcher.add_handler(AKI_ME_HANDLER)
dispatcher.add_handler(AKI_PLAY_HANDLER)
dispatcher.add_handler(aki_win_callback_handler)
dispatcher.add_handler(aki_lead_callback_hanlder)
dispatcher.add_handler(aki_play_callback_handler)
dispatcher.add_handler(aki_set_child_mode_callback_handler)
