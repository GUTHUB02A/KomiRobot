from pprint import pprint
from typing import Any
from typing import Dict, List, Union
from pymongo import MongoClient
from telegram import user ,chat
from ShoukoRobot import MONGO_URL
import itertools

my_client = MongoClient(host=MONGO_URL)
my_db = my_client["aki-db"]



async def int_to_alpha(user_id: int) -> str:
    alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    text = ""
    user_id = str(user_id)
    for i in user_id:
        text += alphabet[int(i)]
    return text


async def alpha_to_int(user_id_alphabet: str) -> int:
    alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
    user_id = ""
    for i in user_id_alphabet:
        index = alphabet.index(i)
        user_id += str(index)
    user_id = int(user_id)
    return user_id


async def get_karmas_count() -> dict:
    chats = my_db.find({"chat_id": {"$lt": 0}})
    if not chats:
        return {}
    chats_count = 0
    karmas_count = 0
    for chat in await chats.to_list(length=1000000):
        for i in chat["karma"]:
            karma_ = chat["karma"][i]["karma"]
            if karma_ > 0:
                karmas_count += karma_
        chats_count += 1
    return {"chats_count": chats_count, "karmas_count": karmas_count}


async def user_global_karma(user_id) -> int:
    chats = my_db.find({"chat_id": {"$lt": 0}})
    if not chats:
        return 0
    total_karma = 0
    for chat in await chats.to_list(length=1000000):
        karma = await get_karma(chat["chat_id"], await int_to_alpha(user_id))
        if karma and (int(karma["karma"]) > 0):
            total_karma += int(karma["karma"])
    return total_karma


async def get_karmas(chat_id: int) -> Dict[str, int]:
    karma = my_db.find_one({"chat_id": chat_id})
    if not karma:
        return {}
    return karma["karma"]


async def get_karma(chat_id: int, name: str) -> Union[bool, dict]:
    name = name.lower().strip()
    karmas = await get_karmas(chat_id)
    if name in karmas:
        return karmas[name]


async def update_karma(chat_id: int, name: str, karma: dict):
    name = name.lower().strip()
    karmas = await get_karmas(chat_id)
    karmas[name] = karma
    my_db.update_one(
        {"chat_id": chat_id}, {"$set": {"karma": karmas}}, upsert=True
    )


async def is_karma_on(chat_id: int) -> bool:
    chat = my_db.find_one({"chat_id_toggle": chat_id})
    if not chat:
        return True
    return False


async def karma_on(chat_id: int):
    is_karma = await is_karma_on(chat_id)
    if is_karma:
        return
    return my_db.delete_one({"chat_id_toggle": chat_id})


async def karma_off(chat_id: int):
    is_karma = await is_karma_on(chat_id)
    if not is_karma:
        return
    return my_db.insert_one({"chat_id_toggle": chat_id})


def addUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Adding the User to the database. If user already present in the database,
    it will check for any changes in the user_name, first_name, last_name and will update if true.
    """
    #"Users" Collection (Table).
    my_col = my_db["users"]
    #Finding if the user_id of the user is in the collection (Table), if found, assigning it to user variable.
    user = my_col.find_one({"user_id": user_id})
    #Checking if the user_id matches with the one from the Collection (Table).
    #If the user_id is not in the Collection (Table), the below statement adds the user to the Collection (Table).
    if user is None:
        my_dict = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "user_name": user_name,
        "aki_lang": "en",
        "child_mode": 1,
        "total_guess": 0,
        "correct_guess": 0,
        "wrong_guess": 0,
        "unfinished_guess": 0,
        "total_questions": 0,
    }
        my_col.insert_one(my_dict)
    elif user["user_id"] == user_id:
        updateUser(user_id, first_name, last_name, user_name)

    
def totalUsers():
    my_col = my_db["users"]
    #Returns the total no.of users who has started the bot.
    return len(list(my_col.find({})))


def updateUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Update a User in the collection (Table).
    """
    my_col = my_db["users"]
    to_update = {
        "user_name": user_name,
        "first_name": first_name,
        "last_name": last_name,
    }
    my_col.update_one({"user_id": user_id}, {"$set":to_update})


def getUser(user_id: int) -> Any or None:
    """
    Returns the user document (Record)
    """
    my_col = my_db["users"]
    return my_col.find_one({"user_id": user_id})

def getChildMode(user_id: int) -> int:
    """
    Get(Returns) the Child mode status of the user. (str)
    """
    my_col = my_db["users"]
    return my_col.find_one({"user_id": user_id})["child_mode"]


def getTotalGuess(user_id: int) -> int:
    """
    
    """
    return my_db["users"].find_one({"user_id": user_id})["total_guess"]


def getCorrectGuess(user_id: int) -> int:
    """
    
    """
    return my_db["users"].find_one({"user_id": user_id})["correct_guess"]



def getWrongGuess(user_id: int) -> int:
    """
    
    """
    return my_db["users"].find_one({"user_id": user_id})["wrong_guess"]


def getUnfinishedGuess(user_id: int) -> int:
    """
    
    """
    crct_wrong_guess = getCorrectGuess(user_id)+getWrongGuess(user_id)
    unfinished_guess = getTotalGuess(user_id)-crct_wrong_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"unfinished_guess": unfinished_guess}})
    return my_db["users"].find_one({"user_id": user_id})["unfinished_guess"]



def getTotalQuestions(user_id: int) -> int:
    """
    
    """
    return my_db["users"].find_one({"user_id": user_id})["total_questions"]

def updateChildMode(user_id: int, mode: int) -> None:
    """
    Update Child Mode of the User.
    """
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"child_mode": mode}})

def updateTotalGuess(user_id: int, total_guess: int) -> None:
    """
    
    """
    total_guess = getTotalGuess(user_id)+total_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"total_guess": total_guess}})


def updateCorrectGuess(user_id: int, correct_guess: int) -> None:
    """
    
    """
    correct_guess = getCorrectGuess(user_id)+correct_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"correct_guess": correct_guess}})


def updateWrongGuess(user_id: int, wrong_guess: int) -> None:
    """
    
    """
    wrong_guess = getWrongGuess(user_id)+wrong_guess
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"wrong_guess": wrong_guess}})
    

def updateTotalQuestions(user_id: int, total_questions: int) -> None:
    """
    
    """
    total_questions = total_questions+ getTotalQuestions(user_id)
    my_db["users"].update_one({"user_id": user_id}, {"$set": {"total_questions": total_questions}})


################# LEADERBOARD FUNCTIONS ####################

def getLead(what:str) -> list:
    lead_dict = {}
    for user in my_db['users'].find({}):
        lead_dict.update({user['first_name']: user[what]})
    lead_dict = sorted(lead_dict.items(), key=lambda x: x[1], reverse=True)
    return lead_dict[:10]
