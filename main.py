import asyncio
import os
import random
import re
import string
import time
import urllib.parse
import dns.resolver
from datetime import datetime
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    UserNotParticipantError,
    FloodWaitError,
    UserIsBlockedError,
)
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityBlockquote

# ============================================================
#                      CONFIGURATION
# ============================================================

API_ID = int(os.environ.get("API_ID", 1234567))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", 3002937363))
LOGGER_ID = int(os.environ.get("LOGGER_ID", -1001234567890))
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://...")

FORCE_CHANNEL = "ll_NAGUMO_lll"
OWNER_USERNAME = "ll_NAGUMO_ll"

BRAND = "ᴀꜱʜɪꜱʜ x ʜᴏꜱᴛᴇʀ"
DISPLAY_BRAND = BRAND
MASTER = "ASHISH"
SIGNATURE = "ᴀꜱʜɪꜱʜ x ʜᴏꜱᴛᴇʀ"

START_TIME = time.monotonic()
PHOTO_CACHE_PATH = "welcome_photo.jpg"

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

bot = TelegramClient("ashish_hoster_bot", API_ID, API_HASH)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["AshishHosterV5"]
sessions_col = db["sessions"]
settings_col = db["settings"]

active_clients = {}
chup_chats = set()
backup_profiles = {}
user_locks = {}
active_raids = set()
active_reply_raids = set()


# ============================================================
#                      RAID ASSETS
# ============================================================

RAID_TEXTS = [
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗖𝗛𝗔𝗞𝗨 𝗗𝗔𝗔𝗟 𝗞𝗔𝗥 𝗖𝗛𝗨𝗧 𝗞𝗔 𝗞𝗛𝗢𝗢𝗡 𝗞𝗔𝗥 𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗞𝗘𝗟𝗘 𝗞𝗘 𝗖𝗛𝗜𝗟𝗞𝗘",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗟𝗘𝗧𝗜 𝗠𝗘𝗥𝗜 𝗟𝗨𝗡𝗗 𝗕𝗔𝗗𝗘 𝗠𝗔𝗦𝗧𝗜 𝗦𝗘",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗞𝗢 𝗠𝗘𝗡𝗘 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗕𝗢𝗛𝗢𝗧 𝗦𝗔𝗦𝗧𝗘 𝗦𝗘",
    "𝗧𝗘𝗥𝗘 𝗕𝗔𝗔𝗣 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗",
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗟𝗘𝗞𝗘 𝗕𝗛𝗔𝗚 𝗝𝗔𝗔𝗨𝗡𝗚𝗔",
    "𝗞𝗜𝗗𝗭 𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘",
    "𝗝𝗨𝗡𝗚𝗟𝗘 𝗠𝗘 𝗡𝗔𝗖𝗛𝗧𝗔 𝗛𝗘 𝗠𝗢𝗥𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗠𝗘 𝗥𝗘𝗛𝗧𝗔 𝗛𝗘 𝗦𝗔𝗡𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔",
    "𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗠𝗨𝗝𝗛𝗞𝗢 𝗣𝗔𝗣𝗔 𝗞𝗬𝗢𝗨𝗡𝗞𝗜 𝗠𝗘𝗡𝗘 𝗕𝗔𝗡𝗔𝗗𝗜𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢𝗧𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗣𝗨𝗥𝗔 𝗙𝗔𝗔𝗗 𝗗𝗜𝗔 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗔𝗕𝗕 𝗧𝗘𝗥𝗜 𝗚𝗙 𝗞𝗢 𝗕𝗛𝗘𝗝 😆💦🤤",
    "𝗧𝗘𝗥𝗜 𝗚𝗙 𝗞𝗢 𝗘𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘 𝗧𝗘𝗥𝗜 𝗚𝗙 𝗧𝗢 𝗠𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗕𝗔𝗡𝗚𝗔𝗬𝗜 𝗔𝗕𝗕 𝗖𝗛𝗔𝗟 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗𝗧𝗔 𝗙𝗜𝗥𝗦𝗘 ♥️💦😆😆😆😆",
    "𝗛𝗔𝗥𝗜 𝗛𝗔𝗥𝗜 𝗚𝗛𝗔𝗔𝗦 𝗠𝗘 𝗝𝗛𝗢𝗣𝗗𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 🤣🤣💋💦",
    "𝗖𝗛𝗔𝗟 𝗧𝗘𝗥𝗘 𝗕𝗔𝗔𝗣 𝗞𝗢 𝗕𝗛𝗘𝗝 𝗧𝗘𝗥𝗔 𝗕𝗔𝗦𝗞𝗔 𝗡𝗛𝗜 𝗛𝗘 𝗣𝗔𝗣𝗔 𝗦𝗘 𝗟𝗔𝗗𝗘𝗚𝗔 𝗧𝗨",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗕𝗢𝗠𝗕 𝗗𝗔𝗟𝗞𝗘 𝗨𝗗𝗔 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗞𝗘 𝗟𝗔𝗪𝗗𝗘",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗧𝗥𝗔𝗜𝗡 𝗠𝗘 𝗟𝗘𝗝𝗔𝗞𝗘 𝗧𝗢𝗣 𝗕𝗘𝗗 𝗣𝗘 𝗟𝗜𝗧𝗔𝗞𝗘 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 🤣🤣💋💋",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗘 𝗡𝗨𝗗𝗘𝗦 𝗚𝗢𝗢𝗚𝗟𝗘 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗘𝗪𝗗𝗘 👻🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗩𝗜𝗗𝗘𝗢 𝗕𝗔𝗡𝗔𝗞𝗘 𝗫𝗡𝗫𝗫.𝗖𝗢𝗠 𝗣𝗘 𝗡𝗘𝗘𝗟𝗔𝗠 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗞𝗨𝗧𝗧𝗘 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💦💋",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗞𝗢 𝗣𝗢𝗥𝗡𝗛𝗨𝗕.𝗖𝗢𝗠 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗦𝗨𝗔𝗥 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘 🤣💋💦",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗘𝗞𝗢 𝗖𝗛𝗔𝗞𝗞𝗢 𝗦𝗘 𝗣𝗜𝗟𝗪𝗔𝗩𝗨𝗡𝗚𝗔 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 🤣🤣",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗙𝗔𝗔𝗗𝗞𝗘 𝗥𝗔𝗞𝗗𝗜𝗔 𝗠𝗔‌𝗔‌𝗞𝗘 𝗟𝗢𝗗𝗘 𝗝𝗔𝗔 𝗔𝗕𝗕 𝗦𝗜𝗟𝗪𝗔𝗟𝗘 👄👄",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗘𝗥𝗔 𝗟𝗨𝗡𝗗 𝗞𝗔𝗔𝗟𝗔",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗟𝗘𝗧𝗜 𝗠𝗘𝗥𝗜 𝗟𝗨𝗡𝗗 𝗕𝗔𝗗𝗘 𝗠𝗔𝗦𝗧𝗜 𝗦𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗠𝗘𝗡𝗘 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗕𝗢𝗛𝗢𝗧 𝗦𝗔𝗦𝗧𝗘 𝗦𝗘",
    "𝗕𝗘𝗧𝗘 𝗧𝗨 𝗕𝗔𝗔𝗣 𝗦𝗘 𝗟𝗘𝗚𝗔 𝗣𝗔𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗞𝗔𝗥𝗞𝗘 𝗡𝗔𝗡𝗚𝗔 💦💋",
    "𝗛𝗔𝗛𝗔𝗛𝗔𝗛 𝗠𝗘𝗥𝗘 𝗕𝗘𝗧𝗘 𝗔𝗚𝗟𝗜 𝗕𝗔𝗔𝗥 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗟𝗘𝗞𝗘 𝗔𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗧 𝗢𝗥 𝗠𝗘𝗥𝗘 𝗠𝗢𝗧𝗘 𝗟𝗨𝗡𝗗 𝗦𝗘 𝗖𝗛𝗨𝗗𝗪𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗥",
    "𝗖𝗛𝗔𝗟 𝗕𝗘𝗧𝗔 𝗧𝗨𝗝𝗛𝗘 𝗠𝗔‌𝗔‌𝗙 𝗞𝗜𝗔 🤣 𝗔𝗕𝗕 𝗔𝗣𝗡𝗜 𝗚𝗙 𝗞𝗢 𝗕𝗛𝗘𝗝",
    "𝗦𝗛𝗔𝗥𝗔𝗠 𝗞𝗔𝗥 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗞𝗜𝗧𝗡𝗔 𝗚𝗔𝗔𝗟𝗜𝗔 𝗦𝗨𝗡𝗪𝗔𝗬𝗘𝗚𝗔 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗨𝗣𝗘𝗥",
    "𝗔𝗕𝗘 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗔𝗨𝗞𝗔𝗧 𝗡𝗛𝗜 𝗛𝗘𝗧𝗢 𝗔𝗣𝗡𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗟𝗘𝗞𝗘 𝗔𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗥 𝗛𝗔𝗛𝗔𝗛𝗔𝗛𝗔",
    "𝗞𝗜𝗗𝗭 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗧𝗘𝗥𝗥 𝗟𝗜𝗬𝗘 𝗕𝗛𝗔𝗜 𝗗𝗘𝗗𝗜𝗬𝗔",
    "𝗝𝗨𝗡𝗚𝗟𝗘 𝗠𝗘 𝗡𝗔𝗖𝗛𝗧𝗔 𝗛𝗘 𝗠𝗢𝗥𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗗𝗘𝗞𝗞𝗘 𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗢𝗡𝗖𝗘 𝗠𝗢𝗥𝗘 𝗢𝗡𝗖𝗘 𝗠𝗢𝗥𝗘 🤣🤣💦💋",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗠𝗘 𝗥𝗘𝗛𝗧𝗔 𝗛𝗘 𝗦𝗔𝗡𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗢𝗥 𝗕𝗔𝗡𝗔 𝗗𝗜𝗔 𝗥𝗔𝗡𝗗 🤤🤣",
    "𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗠𝗨𝗝𝗛𝗞𝗢 𝗣𝗔𝗣𝗔 𝗞𝗬𝗢𝗨𝗡𝗞𝗜 𝗠𝗘𝗡𝗘 𝗕𝗔𝗡𝗔𝗗𝗜𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧 🤣🤣",
    "𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗦𝗨𝗔𝗥 𝗞𝗔 𝗟𝗢𝗨𝗗𝗔 𝗢𝗥 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗘𝗥𝗔 𝗟𝗢𝗗𝗔",
    "𝗖𝗛𝗔𝗟 𝗖𝗛𝗔𝗟 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗖𝗛𝗜𝗬𝗔 𝗗𝗜𝗞𝗔",
    "𝗛𝗔𝗛𝗔𝗛𝗔𝗛𝗔 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗜𝗔 𝗡𝗔𝗡𝗚𝗔 𝗞𝗔𝗥𝗞𝗘",
    "𝗧𝗘𝗥𝗜 𝗚𝗙 𝗛𝗘 𝗕𝗔𝗗𝗜 𝗦𝗘𝗫𝗬 𝗨𝗦𝗞𝗢 𝗣𝗜𝗟𝗔𝗞𝗘 𝗖𝗛𝗢𝗢𝗗𝗘𝗡𝗚𝗘 𝗣𝗘𝗣𝗦𝗜",
    "2 𝗥𝗨𝗣𝗔𝗬 𝗞𝗜 𝗣𝗘𝗣𝗦𝗜 𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗦𝗔𝗕𝗦𝗘 𝗦𝗘𝗫𝗬 💋💦",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗘𝗘𝗠𝗦 𝗦𝗘 𝗖𝗛𝗨𝗗𝗪𝗔𝗩𝗨𝗡𝗚𝗔 𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💦🤣",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗨𝗧𝗛𝗞𝗘 𝗙𝗔𝗥𝗔𝗥 𝗛𝗢𝗝𝗔𝗩𝗨𝗡𝗚𝗔 𝗛𝗨𝗜 𝗛𝗨𝗜 𝗛𝗨𝗜",
    "𝗦𝗣𝗘𝗘𝗗 𝗟𝗔𝗔𝗔 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💋💦🤣",
    "𝗧𝗨𝗝𝗛𝗘 𝗔𝗕 𝗧𝗔𝗞 𝗡𝗔𝗛𝗜 𝗦𝗠𝗝𝗛 𝗔𝗬𝗔 𝗞𝗜 𝗠𝗔𝗜 𝗛𝗜 𝗛𝗨 𝗧𝗨𝗝𝗛𝗘 𝗣𝗔𝗜𝗗𝗔 𝗞𝗔𝗥𝗡𝗘 𝗪𝗔𝗟𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘𝗘 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌ 𝗦𝗘 𝗣𝗨𝗖𝗛 𝗥Æ𝗡𝗗𝗜 𝗞𝗘 𝗕𝗔𝗖𝗛𝗘𝗘𝗘𝗘 🤩👊👤😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗦𝗣𝗢𝗧𝗜𝗙𝗬 𝗗𝗔𝗟 𝗞𝗘 𝗟𝗢𝗙𝗜 𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔 𝗗𝗜𝗡 𝗕𝗛𝗔𝗥 😍🎶🎶💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗡𝗔𝗬𝗔 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗔 𝗞𝗛𝗢𝗟𝗨𝗡𝗚𝗔 𝗖𝗛𝗜𝗡𝗧𝗔 𝗠𝗔𝗧 𝗞𝗔𝗥 👊🤣🤣😳",
    "𝗧𝗘𝗥𝗔 𝗕𝗔𝗔𝗣 𝗛𝗨 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗘 𝗣𝗘 𝗖𝗛𝗨𝗗𝗪𝗔 𝗞𝗘 𝗨𝗦 𝗣𝗔𝗜𝗦𝗘 𝗞𝗜 𝗗𝗔𝗔𝗥𝗨 𝗣𝗘𝗘𝗧𝗔 𝗛𝗨 🍷🤩🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗔𝗣𝗡𝗔 𝗕𝗔𝗗𝗔 𝗦𝗔 𝗟𝗢𝗗𝗔 𝗚𝗛𝗨𝗦𝗦𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗞𝗔𝗟𝗟𝗔𝗔𝗣 𝗞𝗘 𝗠𝗔𝗥 𝗝𝗔𝗬𝗘𝗚𝗜 🤩😳😳🔥",
    "𝗧𝗢𝗛𝗔𝗥 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜𝗡𝗚𝗙𝗜𝗦𝗛𝗘𝗥 𝗞𝗜 𝗕𝗢𝗧𝗧𝗟𝗘 𝗗𝗔𝗟 𝗞𝗘 𝗧𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗔𝗡𝗗𝗘𝗥 𝗛𝗜 😱😂🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗞𝗜 𝗦𝗔𝗣𝗡𝗘 𝗠𝗘𝗜 𝗕𝗛𝗜 𝗠𝗘𝗥𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗬𝗔𝗔𝗗 𝗞𝗔𝗥𝗘𝗚𝗜 𝗥Æ𝗡𝗗𝗜 🥳😍👊💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗔𝗨𝗥 𝗕𝗔𝗛𝗘𝗡 𝗞𝗢 𝗗𝗔𝗨𝗗𝗔 𝗗𝗔𝗨𝗗𝗔 𝗡𝗘 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗨𝗡𝗞𝗘 𝗡𝗢 𝗕𝗢𝗟𝗡𝗘 𝗣𝗘 𝗕𝗛𝗜 𝗟𝗔𝗡𝗗 𝗚𝗛𝗨𝗦𝗔 𝗗𝗨𝗡𝗚𝗔 𝗔𝗡𝗗𝗘𝗥 𝗧𝗔𝗞 😎😎🤣🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗢 𝗢𝗡𝗟𝗜𝗡𝗘 𝗢𝗟𝗫 𝗣𝗘 𝗕𝗘𝗖𝗛𝗨𝗡𝗚𝗔 𝗔𝗨𝗥 𝗣𝗔𝗜𝗦𝗘 𝗦𝗘 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗞𝗢𝗧𝗛𝗔 𝗞𝗛𝗢𝗟 𝗗𝗨𝗡𝗚𝗔 😎🤩😝😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗔 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗞𝗜 𝗧𝗨 𝗖𝗔𝗛 𝗞𝗘 𝗕𝗛𝗜 𝗪𝗢 𝗠𝗔𝗦𝗧 𝗖𝗛𝗨𝗗𝗔𝗜 𝗦𝗘 𝗗𝗨𝗥 𝗡𝗛𝗜 𝗝𝗔 𝗣𝗔𝗬𝗘𝗚𝗔𝗔 😏😏🤩😍",
    "𝗦𝗨𝗡 𝗕𝗘 𝗥Æ𝗡𝗗𝗜 𝗞𝗜 𝗔𝗨𝗟𝗔𝗔𝗗 𝗧𝗨 𝗔𝗣𝗡𝗜 𝗕𝗔𝗛𝗘𝗡 𝗦𝗘 𝗦𝗘𝗘𝗞𝗛 𝗞𝗨𝗖𝗛 𝗞𝗔𝗜𝗦𝗘 𝗚𝗔𝗔𝗡𝗗 𝗠𝗔𝗥𝗪𝗔𝗧𝗘 𝗛𝗔𝗜😏🤬🔥💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗬𝗔𝗔𝗥 𝗛𝗨 𝗠𝗘𝗜 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗣𝗬𝗔𝗔𝗥 𝗛𝗨 𝗠𝗘𝗜 𝗔𝗝𝗔 𝗠𝗘𝗥𝗔 𝗟𝗔𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 𝗟𝗘 🤩🤣💥",
    "𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗨𝗦𝗘𝗥𝗕𝗢𝗧 𝗟𝗔𝗚𝗔𝗔𝗨𝗡𝗚𝗔 𝗦𝗔𝗦𝗧𝗘 𝗦𝗣𝗔𝗠 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗦𝗔𝗥𝗜𝗬𝗔 𝗗𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗨𝗦𝗜 𝗦𝗔𝗥𝗜𝗬𝗘 𝗣𝗥 𝗧𝗔𝗡𝗚 𝗞𝗘 𝗕𝗔𝗖𝗛𝗘 𝗣𝗔𝗜𝗗𝗔 𝗛𝗢𝗡𝗚𝗘 😱😱",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 ✋ 𝗛𝗔𝗧𝗧𝗛 𝗗𝗔𝗟𝗞𝗘 👶 𝗕𝗔𝗖𝗛𝗘 𝗡𝗜𝗞𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 😍",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗞𝗘𝗟𝗘 𝗞𝗘 𝗖𝗛𝗜𝗟𝗞𝗘 🤤🤤",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣💋",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦 𝗣𝗘𝗘𝗟𝗔𝗞𝗘 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😚",
    "𝗧𝗘𝗥𝗜 𝗜𝗧𝗘𝗠 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗟𝗨𝗡𝗗 𝗗𝗔𝗔𝗟𝗞𝗘,𝗧𝗘𝗥𝗘 𝗝𝗔𝗜𝗦𝗔 𝗘𝗞 𝗢𝗥 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😆🤤💋",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗟𝗨𝗡𝗗 𝗣𝗥 𝗜𝗧𝗡𝗔 𝗝𝗛𝗨𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗞𝗜 𝗝𝗛𝗨𝗟𝗧𝗘 𝗝𝗛𝗨𝗟𝗧𝗘 𝗛𝗜 𝗕𝗔𝗖𝗛𝗔 𝗣𝗔𝗜𝗗𝗔 𝗞𝗥 𝗗𝗘𝗚𝗜 💦💋",
    "𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗦𝗔𝗗𝗔𝗞 𝗣𝗥 𝗟𝗜𝗧𝗔𝗞𝗘 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 😂😆🤤",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗 𝗞𝗥 𝗣𝗜𝗟𝗟𝗘 𝗣𝗔𝗣𝗔 𝗦𝗘 𝗟𝗔𝗗𝗘𝗚𝗔 𝗧𝗨 😼😂🤤",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗡𝗘 𝗦𝗛𝗢𝗥 𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗥Æ𝗡𝗗𝗜 𝗖𝗛𝗢𝗥 𝗛𝗘 💋💋💦",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗞𝗨𝗧𝗧𝗘 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘 😂👻🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗔𝗜𝗦𝗘 𝗖𝗛𝗢𝗗𝗔 𝗔𝗜𝗦𝗘 𝗖𝗛𝗢𝗗𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔 𝗕𝗘𝗗 𝗣𝗘𝗛𝗜 𝗠𝗨𝗧𝗛 𝗗𝗜𝗔 💦💦💦💦",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗔𝗔𝗚 𝗟𝗔𝗚𝗔𝗗𝗜𝗔 𝗠𝗘𝗥𝗔 𝗠𝗢𝗧𝗔 𝗟𝗨𝗡𝗗 𝗗𝗔𝗟𝗞𝗘 🔥🔥💦😆😆",
    "𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗖𝗛𝗔𝗟 𝗡𝗜𝗞𝗔𝗟",
    "𝗞𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨 𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗔𝗕𝗕 𝗔𝗣𝗡𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗕𝗛𝗘𝗝 😆👻🤤",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗛𝗢𝗗 𝗞𝗘 𝗨𝗦𝗠𝗘 𝗖𝗬𝗟𝗜𝗡𝗗𝗘𝗥 ⛽️ 𝗙𝗜𝗧 𝗞𝗔𝗥𝗞𝗘 𝗨𝗦𝗠𝗘𝗘 𝗗𝗔𝗟 𝗠𝗔𝗞𝗛𝗔𝗡𝗜 𝗕𝗔𝗡𝗔𝗨𝗡𝗚𝗔𝗔𝗔🤩👊🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗘𝗘𝗦𝗛𝗔 𝗗𝗔𝗟 𝗗𝗨𝗡𝗚𝗔𝗔𝗔 𝗔𝗨𝗥 𝗖𝗛𝗔𝗨𝗥𝗔𝗛𝗘 𝗣𝗘 𝗧𝗔𝗔𝗡𝗚 𝗗𝗨𝗡𝗚𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘😈😱🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗖𝗥𝗘𝗗𝗜𝗧 𝗖𝗔𝗥𝗗 𝗗𝗔𝗟 𝗞𝗘 𝗔𝗚𝗘 𝗦𝗘 500 𝗞𝗘 𝗞𝗔𝗔𝗥𝗘 𝗞𝗔𝗔𝗥𝗘 𝗡𝗢𝗧𝗘 𝗡𝗜𝗞𝗔𝗟𝗨𝗡𝗚𝗔𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘💰💰🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗦𝗔𝗧𝗛 𝗦𝗨𝗔𝗥 𝗞𝗔 𝗦𝗘𝗫 𝗞𝗔𝗥𝗪𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗘𝗞 𝗦𝗔𝗧𝗛 6-6 𝗕𝗔𝗖𝗛𝗘 𝗗𝗘𝗚𝗜💰🔥😱",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗔𝗣𝗣𝗟𝗘 𝗞𝗔 18𝗪 𝗪𝗔𝗟𝗔 𝗖𝗛𝗔𝗥𝗚𝗘𝗥 🔥🤩",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘𝗜 𝗢𝗡𝗘𝗣𝗟𝗨𝗦 𝗞𝗔 𝗪𝗥𝗔𝗣 𝗖𝗛𝗔𝗥𝗚𝗘𝗥 30𝗪 𝗛𝗜𝗚𝗛 𝗣𝗢𝗪𝗘𝗥 💥😂😎",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗢 𝗔𝗠𝗔𝗭𝗢𝗡 𝗦𝗘 𝗢𝗥𝗗𝗘𝗥 𝗞𝗔𝗥𝗨𝗡𝗚𝗔 10 𝗿𝘀 𝗠𝗘𝗜 𝗔𝗨𝗥 𝗙𝗟𝗜𝗣𝗞𝗔𝗥𝗧 𝗣𝗘 20 𝗥𝗦 𝗠𝗘𝗜 𝗕𝗘𝗖𝗛 𝗗𝗨𝗡𝗚𝗔🤮👿😈🤖",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗕𝗔𝗗𝗜 𝗕𝗛𝗨𝗡𝗗 𝗠𝗘 𝗭𝗢𝗠𝗔𝗧𝗢 𝗗𝗔𝗟 𝗞𝗘 𝗦𝗨𝗕𝗪𝗔𝗬 𝗞𝗔 𝗕𝗙𝗙 𝗩𝗘𝗚 𝗦𝗨𝗕 𝗖𝗢𝗠𝗕𝗢 [15𝗰𝗺 , 16 𝗶𝗻𝗰𝗵𝗲𝘀 ] 𝗢𝗥𝗗𝗘𝗥 𝗖𝗢𝗗 𝗞𝗥𝗩𝗔𝗨𝗡𝗚𝗔 𝗢𝗥 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗝𝗔𝗕 𝗗𝗜𝗟𝗜𝗩𝗘𝗥𝗬 𝗗𝗘𝗡𝗘 𝗔𝗬𝗘𝗚𝗜 𝗧𝗔𝗕 𝗨𝗦𝗣𝗘 𝗝𝗔𝗔𝗗𝗨 𝗞𝗥𝗨𝗡𝗚𝗔 𝗢𝗥 𝗙𝗜𝗥 9 𝗠𝗢𝗡𝗧𝗛 𝗕𝗔𝗔𝗗 𝗩𝗢 𝗘𝗞 𝗢𝗥 𝗙𝗥𝗘𝗘 𝗗𝗜𝗟𝗜𝗩𝗘𝗥𝗬 𝗗𝗘𝗚𝗜🙀👍🥳🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔𝗔𝗟𝗜🙁🤣💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 𝗙𝗜𝗥 𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖𝗔𝗟𝗟𝗬 𝗨𝗣𝗗𝗔𝗧𝗘 𝗛𝗢𝗝𝗔𝗔𝗬𝗘𝗚𝗜🤖🙏🤔",
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗨𝗦𝗜 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗜𝗡𝗗𝗜𝗔𝗡 𝗥𝗔𝗜𝗟𝗪𝗔𝗬 🚂💥😂",
    "𝗧𝗨 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗧𝗘𝗥𝗔 𝗞𝗛𝗔𝗡𝗗𝗔𝗡 𝗦𝗔𝗕 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗪𝗗𝗘 𝗥Æ𝗡𝗗𝗜 𝗛𝗔𝗜 𝗥Æ𝗡𝗗𝗜 🤢✅🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗜𝗢𝗡𝗜𝗖 𝗕𝗢𝗡𝗗 𝗕𝗔𝗡𝗔 𝗞𝗘 𝗩𝗜𝗥𝗚𝗜𝗡𝗜𝗧𝗬 𝗟𝗢𝗢𝗦𝗘 𝗞𝗔𝗥𝗪𝗔 𝗗𝗨𝗡𝗚𝗔 𝗨𝗦𝗞𝗜 📚 😎🤩",
    "𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌ 𝗦𝗘 𝗣𝗨𝗖𝗛𝗡𝗔 𝗕𝗔𝗔𝗣 𝗞𝗔 𝗡𝗔𝗔𝗠 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘𝗘𝗘𝗘𝗘 🤩🥳😳",
    "𝗧𝗨 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗗𝗢𝗡𝗢 𝗞𝗜 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗠𝗘𝗧𝗥𝗢 𝗖𝗛𝗔𝗟𝗪𝗔 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔𝗗𝗔𝗥𝗫𝗛𝗢𝗗 🚇🤩😱🥶",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗔 𝗕𝗔𝗔𝗣 𝗕𝗛𝗜 𝗨𝗦𝗞𝗢 𝗣𝗔𝗛𝗖𝗛𝗔𝗡𝗔𝗡𝗘 𝗦𝗘 𝗠𝗔𝗡𝗔 𝗞𝗔𝗥 𝗗𝗘𝗚𝗔😂👿🤩",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗛𝗔𝗜𝗥 𝗗𝗥𝗬𝗘𝗥 𝗖𝗛𝗔𝗟𝗔 𝗗𝗨𝗡𝗚𝗔𝗔💥🔥🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗞𝗜 𝗦𝗔𝗥𝗜 𝗥Æ𝗡𝗗𝗜𝗬𝗢𝗡 𝗞𝗔 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗔 𝗞𝗛𝗢𝗟 𝗗𝗨𝗡𝗚𝗔𝗔👿🤮😎",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗟𝗘𝗫𝗔 𝗗𝗔𝗟 𝗞𝗘𝗘 𝗗𝗝 𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔𝗔𝗔 🎶 ⬆️🤩💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗚𝗜𝗧𝗛𝗨𝗕 𝗗𝗔𝗟 𝗞𝗘 𝗔𝗣𝗡𝗔 𝗕𝗢𝗧 𝗛𝗢𝗦𝗧 𝗞𝗔𝗥𝗨𝗡𝗚𝗔𝗔 🤩👊👤😍",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗩𝗣𝗦 𝗕𝗔𝗡𝗔 𝗞𝗘 24*7 𝗕𝗔𝗦𝗛 𝗖𝗛𝗨𝗗𝗔𝗜 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗗𝗘 𝗗𝗨𝗡𝗚𝗔𝗔 🤩💥🔥🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗧𝗘𝗥𝗘 𝗟𝗔𝗡𝗗 𝗞𝗢 𝗗𝗔𝗟 𝗞𝗘 𝗞𝗔𝗔𝗧 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 🔪😂🔥",
    "𝗦𝗨𝗡 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗕𝗛𝗜 𝗕𝗛𝗢𝗦𝗗𝗔 👿😎👊",
    "𝗧𝗨𝗝𝗛𝗘 𝗗𝗘𝗞𝗛 𝗞𝗘 𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗕𝗔𝗛𝗘𝗡 𝗣𝗘 𝗧𝗔𝗥𝗔𝗦 𝗔𝗧𝗔 𝗛𝗔𝗜 𝗠𝗨𝗝𝗛𝗘 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘𝗘𝗘𝗘 👿💥🤩🔥",
    "𝗦𝗨𝗡 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗝𝗬𝗔𝗗𝗔 𝗡𝗔 𝗨𝗖𝗛𝗔𝗟 𝗠𝗔‌𝗔‌ 𝗖𝗛𝗢𝗗 𝗗𝗘𝗡𝗚𝗘 𝗘𝗞 𝗠𝗜𝗡 𝗠𝗘𝗜 ✅🤣🔥🤩",
    "𝗔𝗣𝗡𝗜 𝗔𝗠𝗠𝗔 𝗦𝗘 𝗣𝗨𝗖𝗛𝗡𝗔 𝗨𝗦𝗞𝗢 𝗨𝗦 𝗞𝗔𝗔𝗟𝗜 𝗥𝗔𝗔𝗧 𝗠𝗘𝗜 𝗞𝗔𝗨𝗡 𝗖𝗛𝗢𝗗𝗡𝗘𝗘 𝗔𝗬𝗔 𝗧𝗛𝗔𝗔𝗔! 𝗧𝗘𝗥𝗘 𝗜𝗦 𝗣𝗔𝗣𝗔 𝗞𝗔 𝗡𝗔𝗔𝗠 𝗟𝗘𝗚𝗜 😂👿😳",
    "𝗧𝗢𝗛𝗔𝗥 𝗕𝗔𝗛𝗜𝗡 𝗖𝗛𝗢𝗗𝗨 𝗕𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗪𝗗𝗘 𝗨𝗦𝗠𝗘 𝗠𝗜𝗧𝗧𝗜 𝗗𝗔𝗟 𝗞𝗘 𝗖𝗘𝗠𝗘𝗡𝗧 𝗦𝗘 𝗕𝗛𝗔𝗥 𝗗𝗨 🏠🤢🤩💥",
    "𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗚𝗛𝗨𝗧𝗞𝗔 𝗞𝗛𝗔𝗔𝗞𝗘 𝗧𝗛𝗢𝗢𝗞 𝗗𝗨𝗡𝗚𝗔 🤣🤣",
    "𝗧𝗘𝗥𝗘 𝗕𝗘‌𝗛𝗘𝗡 𝗞 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗞𝗨 𝗗𝗔𝗔𝗟 𝗞𝗔𝗥 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔 𝗞𝗛𝗢𝗢𝗡 𝗞𝗔𝗥 𝗗𝗨𝗚𝗔",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗡𝗛𝗜 𝗛𝗔𝗜 𝗞𝗬𝗔? 9 𝗠𝗔𝗛𝗜𝗡𝗘 𝗥𝗨𝗞 𝗦𝗔𝗚𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗗𝗘𝗧𝗔 𝗛𝗨 🤣🤣🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗘𝗥𝗢𝗣𝗟𝗔𝗡𝗘𝗣𝗔𝗥𝗞 𝗞𝗔𝗥𝗞𝗘 𝗨𝗗𝗔𝗔𝗡 𝗕𝗛𝗔𝗥 𝗗𝗨𝗚𝗔 ✈️🛫",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗖𝗢𝗢𝗧𝗘𝗥 𝗗𝗔𝗔𝗟 𝗗𝗨𝗚𝗔👅",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔𝗞𝗧𝗘 🤱 𝗚𝗔𝗟𝗜 𝗞𝗘 𝗞𝗨𝗧𝗧𝗢 🦮 𝗠𝗘 𝗕𝗔𝗔𝗧 𝗗𝗨𝗡𝗚𝗔 𝗣𝗛𝗜𝗥 🍞 𝗕𝗥𝗘𝗔𝗗 𝗞𝗜 𝗧𝗔𝗥𝗛 𝗞𝗛𝗔𝗬𝗘𝗡𝗚𝗘 𝗪𝗢 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧",
    "𝗗𝗨𝗗𝗛 𝗛𝗜𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗘 𝗨𝗣𝗥 𝗡𝗜𝗖𝗛𝗘 🆙🆒😙",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 @ll_ALPHA_BABY_lll 𝗞𝗔 𝗟𝗨𝗡𝗗 𝗗𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗙𝗜𝗥 𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜 🍌🍌😍",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗗𝗛𝗔𝗡𝗗𝗛𝗘 𝗩𝗔𝗔𝗟𝗜 😋😛",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗖 𝗟𝗔𝗚𝗔 𝗗𝗨𝗡𝗚𝗔 𝗦𝗔𝗔𝗥𝗜 𝗚𝗔𝗥𝗠𝗜 𝗡𝗜𝗞𝗔𝗟 𝗝𝗔𝗔𝗬𝗘𝗚𝗜",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦 𝗣𝗘𝗘𝗟𝗔𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😚",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗞𝗢𝗟𝗞𝗔𝗧𝗔 𝗩𝗔𝗔𝗟𝗘 𝗝𝗜𝗧𝗨 𝗕𝗛𝗔𝗜𝗬𝗔 𝗞𝗔 𝗟𝗨𝗡𝗗 𝗠𝗨𝗕𝗔𝗥𝗔𝗞 🤩🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗙𝗔𝗡𝗧𝗔𝗦𝗬 𝗛𝗨 𝗟𝗔𝗪𝗗𝗘, 𝗧𝗨 𝗔𝗣𝗡𝗜 𝗕𝗛𝗘𝗡 𝗞𝗢 𝗦𝗠𝗕𝗛𝗔𝗔𝗟 😈😈",
    "𝗧𝗘𝗥𝗔 𝗣𝗘𝗛𝗟𝗔 𝗕𝗔𝗔𝗣 𝗛𝗨 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗫𝗩𝗜𝗗𝗘𝗢𝗦.𝗖𝗢𝗠 𝗖𝗛𝗔𝗟𝗔 𝗞𝗘 𝗠𝗨𝗧𝗛 𝗠𝗔‌𝗔‌𝗥𝗨𝗡𝗚𝗔 🤡😹",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗚𝗥𝗢𝗨𝗣 𝗩𝗔𝗔𝗟𝗢𝗡 𝗦𝗔𝗔𝗧𝗛 𝗠𝗜𝗟𝗞𝗘 𝗚𝗔𝗡𝗚 𝗕𝗔𝗡𝗚 𝗞𝗥𝗨𝗡𝗚𝗔🙌🏻☠️",
    "𝗧𝗘𝗥𝗜 𝗜𝗧𝗘𝗠 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗟𝗨𝗡𝗗 𝗗𝗔𝗔𝗟𝗞𝗘,𝗧𝗘𝗥𝗘 𝗝𝗔𝗜𝗦𝗔 𝗘𝗞 𝗢𝗥 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗🤘🏻🙌🏻☠️",
    "𝗔𝗨𝗞𝗔𝗔𝗧 𝗠𝗘 𝗥𝗘𝗛 𝗩𝗥𝗡𝗔 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗗𝗔𝗡𝗗𝗔 𝗗𝗔𝗔𝗟 𝗞𝗘 𝗠𝗨𝗛 𝗦𝗘 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗦𝗛𝗔𝗥𝗜𝗥 𝗕𝗛𝗜 𝗗𝗔𝗡𝗗𝗘 𝗝𝗘𝗦𝗔 𝗗𝗜𝗞𝗛𝗘𝗚𝗔 🙄🤭🤭",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗘 𝗦𝗔𝗔𝗧𝗛 𝗟𝗨𝗗𝗢 𝗞𝗛𝗘𝗟𝗧𝗘 𝗞𝗛𝗘𝗟𝗧𝗘 𝗨𝗦𝗞𝗘 𝗠𝗨𝗛 𝗠𝗘 𝗔𝗣𝗡𝗔 𝗟𝗢𝗗𝗔 𝗗𝗘 𝗗𝗨𝗡𝗚𝗔☝🏻☝🏻😬",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗟𝗨𝗡𝗗 𝗣𝗥 𝗜𝗧𝗡𝗔 𝗝𝗛𝗨𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗞𝗜 𝗝𝗛𝗨𝗟𝗧𝗘 𝗝𝗛𝗨𝗟𝗧𝗘 𝗛𝗜 𝗕𝗔𝗖𝗛𝗔 𝗣𝗔𝗜𝗗𝗔 𝗞𝗥 𝗗𝗘𝗚𝗜👀👯",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗕𝗔𝗧𝗧𝗘𝗥𝗬 𝗟𝗔𝗚𝗔 𝗞𝗘 𝗣𝗢𝗪𝗘𝗥𝗕𝗔𝗡𝗞 𝗕𝗔𝗡𝗔 𝗗𝗨𝗡𝗚𝗔 🔋 🔥🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗖++ 𝗦𝗧𝗥𝗜𝗡𝗚 𝗘𝗡𝗖𝗥𝗬𝗣𝗧𝗜𝗢𝗡 𝗟𝗔𝗚𝗔 𝗗𝗨𝗡𝗚𝗔 𝗕𝗔𝗛𝗧𝗜 𝗛𝗨𝗬𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗥𝗨𝗞 𝗝𝗔𝗬𝗘𝗚𝗜𝗜𝗜𝗜😈🔥😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘𝗜 𝗝𝗛𝗔𝗔𝗗𝗨 𝗗𝗔𝗟 𝗞𝗘 𝗠𝗢𝗥 🦚 𝗕𝗔𝗡𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 🤩🥵😱",
    "𝗧𝗘𝗥𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗢𝗨𝗟𝗗𝗘𝗥𝗜𝗡𝗚 𝗞𝗔𝗥 𝗗𝗨𝗡𝗚𝗔𝗔 𝗛𝗜𝗟𝗔𝗧𝗘 𝗛𝗨𝗬𝗘 𝗕𝗛𝗜 𝗗𝗔𝗥𝗗 𝗛𝗢𝗚𝗔𝗔𝗔😱🤮👺",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗥𝗘𝗗𝗜 𝗣𝗘 𝗕𝗔𝗜𝗧𝗛𝗔𝗟 𝗞𝗘 𝗨𝗦𝗦𝗘 𝗨𝗦𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗕𝗜𝗟𝗪𝗔𝗨𝗡𝗚𝗔𝗔 💰 😵🤩",
    "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 4 𝗛𝗢𝗟𝗘 𝗛𝗔𝗜 𝗨𝗡𝗠𝗘 𝗠𝗦𝗘𝗔𝗟 𝗟𝗔𝗚𝗔 𝗕𝗔𝗛𝗨𝗧 𝗕𝗔𝗛𝗘𝗧𝗜 𝗛𝗔𝗜 𝗕𝗛𝗢𝗙𝗗𝗜𝗞𝗘👊🤮🤢🤢",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗕𝗔𝗥𝗚𝗔𝗗 𝗞𝗔 𝗣𝗘𝗗 𝗨𝗚𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗖𝗢𝗥𝗢𝗡𝗔 𝗠𝗘𝗜 𝗦𝗔𝗕 𝗢𝗫𝗬𝗚𝗘𝗡 𝗟𝗘𝗞𝗔𝗥 𝗝𝗔𝗬𝗘𝗡𝗚𝗘🤢🤩🥳",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗨𝗗𝗢 𝗟𝗔𝗚𝗔 𝗞𝗘 𝗕𝗜𝗚𝗦𝗣𝗔𝗠 𝗟𝗔𝗚𝗔 𝗞𝗘 9999 𝗙𝗨𝗖𝗞 𝗟𝗔𝗚𝗔𝗔 𝗗𝗨 🤩🥳🔥",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗠𝗘𝗜 𝗕𝗘𝗦𝗔𝗡 𝗞𝗘 𝗟𝗔𝗗𝗗𝗨 𝗕𝗛𝗔𝗥 𝗗𝗨𝗡𝗚𝗔🤩🥳🔥😈",
]

ONE_WORD_RAID_TEXTS = [
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗖𝗛𝗔𝗞𝗨", "𝗗𝗔𝗔𝗟", "𝗞𝗔𝗥", "𝗖𝗛𝗨𝗧", "𝗞𝗔",
    "𝗞𝗛𝗢𝗢𝗡", "𝗞𝗔𝗥", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗞𝗘𝗟𝗘", "𝗞𝗘",
    "𝗖𝗛𝗜𝗟𝗞𝗘", "𝗧𝗘𝗥𝗘", "𝗕𝗔𝗔𝗣", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗞𝗜𝗗𝗭", "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗝𝗨𝗡𝗚𝗟𝗘", "𝗠𝗘", "𝗡𝗔𝗖𝗛𝗧𝗔", "𝗛𝗘", "𝗠𝗢𝗥𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗠𝗘", "𝗥𝗘𝗛𝗧𝗔", "𝗛𝗘", "𝗦𝗔𝗡𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗔𝗟𝗔", "𝗦𝗔𝗕", "𝗕𝗢𝗟𝗧𝗘", "𝗠𝗨𝗝𝗛𝗞𝗢", "𝗣𝗔𝗣𝗔", "𝗞𝗬𝗢𝗨𝗡𝗞𝗜", "𝗠𝗘𝗡𝗘", "𝗕𝗔𝗡𝗔𝗗𝗜𝗔",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗠𝗘𝗡𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗔𝗟𝗔",
    "𝗕𝗢𝗛𝗢𝗧", "𝗦𝗔𝗦𝗧𝗘", "𝗦𝗘", "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗞𝗢", "𝗘𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗔", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗘",
    "𝗟𝗢𝗗𝗘", "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗧𝗢", "𝗠𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗕𝗔𝗡𝗚𝗔𝗬𝗜", "𝗔𝗕𝗕", "𝗖𝗛𝗔𝗟", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗𝗧𝗔", "𝗙𝗜𝗥𝗦𝗘", "𝗛𝗔𝗥𝗜", "𝗛𝗔𝗥𝗜", "𝗚𝗛𝗔𝗔𝗦", "𝗠𝗘", "𝗝𝗛𝗢𝗣𝗗𝗔", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗖𝗛𝗔𝗟", "𝗧𝗘𝗥𝗘", "𝗕𝗔𝗔𝗣", "𝗞𝗢", "𝗕𝗛𝗘𝗝", "𝗧𝗘𝗥𝗔", "𝗕𝗔𝗦𝗞𝗔",
    "𝗡𝗛𝗜", "𝗛𝗘", "𝗣𝗔𝗣𝗔", "𝗦𝗘", "𝗟𝗔𝗗𝗘𝗚𝗔", "𝗧𝗨", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗧",
    "𝗠𝗘", "𝗕𝗢𝗠𝗕", "𝗗𝗔𝗟𝗞𝗘", "𝗨𝗗𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗧𝗥𝗔𝗜𝗡", "𝗠𝗘",
    "𝗟𝗘𝗝𝗔𝗞𝗘", "𝗧𝗢𝗣", "𝗕𝗘𝗗", "𝗣𝗘", "𝗟𝗜𝗧𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘",
    "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗩𝗜𝗗𝗘𝗢", "𝗕𝗔𝗡𝗔𝗞𝗘", "𝗫𝗡𝗫𝗫", "𝗣𝗘", "𝗡𝗘𝗘𝗟𝗔𝗠",
    "𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔", "𝗞𝗨𝗧𝗧𝗘", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗞𝗢", "𝗣𝗢𝗥𝗡𝗛𝗨𝗕",
    "𝗣𝗘", "𝗨𝗣𝗟𝗢𝗔𝗗", "𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔", "𝗔𝗕𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗖𝗛𝗢𝗗𝗨", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗕𝗔𝗖𝗛𝗛𝗘",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗙𝗔𝗔𝗗𝗞𝗘", "𝗥𝗔𝗞𝗗𝗜𝗔", "𝗠𝗔𝗔", "𝗞𝗘", "𝗟𝗢𝗗𝗘", "𝗝𝗔𝗔",
    "𝗔𝗕𝗕", "𝗦𝗜𝗟𝗪𝗔𝗟𝗘", "𝗕𝗘𝗧𝗘", "𝗧𝗨", "𝗕𝗔𝗔𝗣", "𝗦𝗘", "𝗟𝗘𝗚𝗔", "𝗣𝗔𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗞𝗔𝗥𝗞𝗘", "𝗡𝗔𝗡𝗚𝗔", "𝗠𝗘𝗥𝗘", "𝗕𝗘𝗧𝗘", "𝗔𝗚𝗟𝗜", "𝗕𝗔𝗔𝗥", "𝗔𝗣𝗡𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗟𝗘𝗞𝗘", "𝗔𝗔𝗬𝗔", "𝗠𝗔𝗧𝗛", "𝗞𝗔𝗥", "𝗖𝗛𝗔𝗟", "𝗕𝗘𝗧𝗔", "𝗧𝗨𝗝𝗛𝗘", "𝗠𝗔𝗔𝗙",
    "𝗞𝗜𝗔", "𝗔𝗕𝗕", "𝗔𝗣𝗡𝗜", "𝗚𝗙", "𝗞𝗢", "𝗕𝗛𝗘𝗝", "𝗔𝗕𝗘", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗕𝗔𝗖𝗛𝗛𝗘", "𝗔𝗨𝗞𝗔𝗧",
    "𝗡𝗛𝗜", "𝗛𝗘𝗧𝗢", "𝗔𝗣𝗡𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗟𝗘𝗞𝗘", "𝗔𝗔𝗬𝗔", "𝗠𝗔𝗧𝗛", "𝗞𝗔𝗥", "𝗞𝗜𝗗𝗭",
    "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗧𝗘𝗥𝗥", "𝗟𝗜𝗬𝗘", "𝗕𝗛𝗔𝗜", "𝗗𝗘𝗗𝗜𝗬𝗔",
    "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗠𝗘", "𝗥𝗘𝗛𝗧𝗔", "𝗛𝗘", "𝗦𝗔𝗡𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗",
    "𝗗𝗔𝗟𝗔", "𝗢𝗥", "𝗕𝗔𝗡𝗔", "𝗗𝗜𝗔", "𝗥𝗔𝗡𝗗", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗠𝗘𝗥𝗔", "𝗟𝗢𝗗𝗔", "𝗖𝗛𝗔𝗟", "𝗖𝗛𝗔𝗟", "𝗔𝗣𝗡𝗜", "𝗠𝗔𝗔", "𝗞𝗜",
    "𝗖𝗛𝗨𝗖𝗛𝗜𝗬𝗔", "𝗗𝗜𝗞𝗔", "𝗕𝗔𝗖𝗛𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗜𝗔", "𝗡𝗔𝗡𝗚𝗔", "𝗞𝗔𝗥𝗞𝗘",
    "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗛𝗘", "𝗕𝗔𝗗𝗜", "𝗦𝗘𝗫𝗬", "𝗨𝗦𝗞𝗢", "𝗣𝗜𝗟𝗔𝗞𝗘", "𝗖𝗛𝗢𝗢𝗗𝗘𝗡𝗚𝗘", "𝗣𝗘𝗣𝗦𝗜", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗘𝗘𝗠𝗦", "𝗦𝗘", "𝗖𝗛𝗨𝗗𝗪𝗔𝗩𝗨𝗡𝗚𝗔", "𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗦𝗣𝗘𝗘𝗗", "𝗟𝗔𝗔𝗔",
    "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗖𝗛𝗢𝗗𝗨", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗔", "𝗕𝗔𝗔𝗣", "𝗛𝗨", "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗥𝗔𝗡𝗗𝗜", "𝗞𝗛𝗔𝗡𝗘", "𝗣𝗘", "𝗖𝗛𝗨𝗗𝗪𝗔", "𝗞𝗘", "𝗨𝗦", "𝗣𝗔𝗜𝗦𝗘", "𝗞𝗜",
    "𝗗𝗔𝗔𝗥𝗨", "𝗣𝗘𝗘𝗧𝗔", "𝗛𝗨", "𝗧𝗢𝗛𝗔𝗥", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗣𝗨𝗥𝗜", "𝗞𝗜",
    "𝗣𝗨𝗥𝗜", "𝗞𝗜𝗡𝗚𝗙𝗜𝗦𝗛𝗘𝗥", "𝗞𝗜", "𝗕𝗢𝗧𝗧𝗟𝗘", "𝗗𝗔𝗟", "𝗞𝗘", "𝗧𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗔𝗡𝗗𝗘𝗥", "𝗛𝗜",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗜𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗞𝗜", "𝗦𝗔𝗣𝗡𝗘", "𝗠𝗘𝗜", "𝗕𝗛𝗜", "𝗠𝗘𝗥𝗜",
    "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗬𝗔𝗔𝗗", "𝗞𝗔𝗥𝗘𝗚𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗔𝗨𝗥", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗢", "𝗗𝗔𝗨𝗗𝗔",
    "𝗗𝗔𝗨𝗗𝗔", "𝗡𝗘", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗢", "𝗢𝗡𝗟𝗜𝗡𝗘", "𝗢𝗟𝗫",
    "𝗣𝗘", "𝗕𝗘𝗖𝗛𝗨𝗡𝗚𝗔", "𝗦𝗨𝗡", "𝗕𝗘", "𝗥𝗔𝗡𝗗𝗜", "𝗞𝗜", "𝗔𝗨𝗟𝗔𝗔𝗗", "𝗧𝗘𝗥𝗜", "𝗕𝗛𝗘𝗡", "𝗞𝗜",
    "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗨𝗦𝗘𝗥𝗕𝗢𝗧", "𝗟𝗔𝗚𝗔𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘", "𝗦𝗔𝗥𝗜𝗬𝗔",
    "𝗗𝗔𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗞𝗘𝗟𝗘", "𝗞𝗘", "𝗖𝗛𝗜𝗟𝗞𝗘",
    "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗢", "𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦", "𝗣𝗘𝗘𝗟𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗦𝗔𝗗𝗔𝗞", "𝗣𝗥", "𝗟𝗜𝗧𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗡𝗘",
    "𝗦𝗛𝗢𝗥", "𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗥𝗔𝗡𝗗𝗜", "𝗖𝗛𝗢𝗥", "𝗛𝗘", "𝗞𝗜𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗨", "𝗧𝗘𝗥𝗜",
    "𝗥𝗔𝗡𝗗𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗛𝗢𝗗", "𝗞𝗘",
    "𝗨𝗦𝗠𝗘", "𝗖𝗬𝗟𝗜𝗡𝗗𝗘𝗥", "𝗙𝗜𝗧", "𝗞𝗔𝗥𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗦𝗛𝗘𝗘𝗦𝗛𝗔",
    "𝗗𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗖𝗥𝗘𝗗𝗜𝗧", "𝗖𝗔𝗥𝗗", "𝗗𝗔𝗟",
    "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗦𝗔𝗧𝗛", "𝗦𝗨𝗔𝗥", "𝗞𝗔", "𝗦𝗘𝗫", "𝗞𝗔𝗥𝗪𝗔", "𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗔𝗣𝗣𝗟𝗘", "𝗞𝗔", "𝗖𝗛𝗔𝗥𝗚𝗘𝗥", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡",
    "𝗞𝗜", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘𝗜", "𝗢𝗡𝗘𝗣𝗟𝗨𝗦", "𝗞𝗔", "𝗪𝗥𝗔𝗣", "𝗖𝗛𝗔𝗥𝗚𝗘𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜",
    "𝗕𝗔𝗗𝗜", "𝗕𝗛𝗨𝗡𝗗", "𝗠𝗘", "𝗭𝗢𝗠𝗔𝗧𝗢", "𝗗𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗞𝗔𝗔𝗟𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗖𝗛𝗔𝗡𝗚𝗘𝗦", "𝗖𝗢𝗠𝗠𝗜𝗧", "𝗞𝗥𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗨𝗦𝗜", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗜𝗡𝗗𝗜𝗔𝗡", "𝗥𝗔𝗜𝗟𝗪𝗔𝗬", "𝗧𝗨", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗧𝗘𝗥𝗔",
    "𝗞𝗛𝗔𝗡𝗗𝗔𝗡", "𝗦𝗔𝗕", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗟𝗔𝗪𝗗𝗘", "𝗥𝗔𝗡𝗗𝗜", "𝗛𝗔𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡",
    "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗜𝗢𝗡𝗜𝗖", "𝗕𝗢𝗡𝗗", "𝗕𝗔𝗡𝗔", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗠𝗔𝗔",
    "𝗦𝗘", "𝗣𝗨𝗖𝗛𝗡𝗔", "𝗕𝗔𝗔𝗣", "𝗞𝗔", "𝗡𝗔𝗔𝗠", "𝗧𝗨", "𝗔𝗨𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗗𝗢𝗡𝗢",
    "𝗞𝗜", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗠𝗘𝗧𝗥𝗢", "𝗖𝗛𝗔𝗟𝗪𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘",
    "𝗠𝗘𝗜", "𝗛𝗔𝗜𝗥", "𝗗𝗥𝗬𝗘𝗥", "𝗖𝗛𝗔𝗟𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗔𝗟𝗘𝗫𝗔",
    "𝗗𝗔𝗟", "𝗞𝗘", "𝗗𝗝", "𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗚𝗜𝗧𝗛𝗨𝗕",
    "𝗗𝗔𝗟", "𝗞𝗘", "𝗔𝗣𝗡𝗔", "𝗕𝗢𝗧", "𝗛𝗢𝗦𝗧", "𝗞𝗔𝗥𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗧𝗘𝗥𝗘", "𝗟𝗔𝗡𝗗", "𝗞𝗢", "𝗗𝗔𝗟", "𝗞𝗘", "𝗞𝗔𝗔𝗧", "𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗡", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗔𝗨𝗥", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗔", "𝗕𝗛𝗜", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗧𝗨𝗝𝗛𝗘",
    "𝗗𝗘𝗞𝗛", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗣𝗘", "𝗧𝗔𝗥𝗔𝗦", "𝗔𝗧𝗔", "𝗛𝗔𝗜", "𝗦𝗨𝗡",
    "𝗠𝗔𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗝𝗬𝗔𝗗𝗔", "𝗡𝗔", "𝗨𝗖𝗛𝗔𝗟", "𝗠𝗔𝗔", "𝗖𝗛𝗢𝗗", "𝗗𝗘𝗡𝗚𝗘", "𝗔𝗣𝗡𝗜", "𝗔𝗠𝗠𝗔", "𝗦𝗘",
    "𝗣𝗨𝗖𝗛𝗡𝗔", "𝗧𝗢𝗛𝗔𝗥", "𝗕𝗔𝗛𝗜𝗡", "𝗖𝗛𝗢𝗗𝗨", "𝗕𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗟𝗔𝗪𝗗𝗘", "𝗧𝗘𝗥𝗘", "𝗕𝗘𝗛𝗘𝗡", "𝗞",
    "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗖𝗛𝗔𝗞𝗨", "𝗗𝗔𝗔𝗟", "𝗞𝗔𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘",
    "𝗔𝗘𝗥𝗢𝗣𝗟𝗔𝗡𝗘", "𝗣𝗔𝗥𝗞", "𝗞𝗔𝗥𝗞𝗘", "𝗨𝗗𝗔𝗔𝗡", "𝗕𝗛𝗔𝗥", "𝗗𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘", "𝗦𝗖𝗢𝗢𝗧𝗘𝗥", "𝗗𝗔𝗔𝗟", "𝗗𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗔𝗞𝗧𝗘", "𝗚𝗔𝗟𝗜",
    "𝗞𝗘", "𝗞𝗨𝗧𝗧𝗢", "𝗠𝗘", "𝗕𝗔𝗔𝗧", "𝗗𝗨𝗡𝗚𝗔", "𝗗𝗨𝗗𝗛", "𝗛𝗜𝗟𝗔𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗘",
    "𝗨𝗣𝗥", "𝗡𝗜𝗖𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗟𝗨𝗡𝗗", "𝗗𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗗𝗛𝗔𝗡𝗗𝗛𝗘", "𝗩𝗔𝗔𝗟𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘", "𝗔𝗖",
    "𝗟𝗔𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗢", "𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦", "𝗣𝗘𝗘𝗟𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢",
    "𝗞𝗢𝗟𝗞𝗔𝗧𝗔", "𝗩𝗔𝗔𝗟𝗘", "𝗝𝗜𝗧𝗨", "𝗕𝗛𝗔𝗜𝗬𝗔", "𝗞𝗔", "𝗟𝗨𝗡𝗗", "𝗠𝗨𝗕𝗔𝗥𝗔𝗞", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜",
    "𝗙𝗔𝗡𝗧𝗔𝗦𝗬", "𝗛𝗨", "𝗟𝗔𝗪𝗗𝗘", "𝗧𝗘𝗥𝗔", "𝗣𝗘𝗛𝗟𝗔", "𝗕𝗔𝗔𝗣", "𝗛𝗨", "𝗠𝗔𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡",
    "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘", "𝗫𝗩𝗜𝗗𝗘𝗢𝗦", "𝗖𝗛𝗔𝗟𝗔", "𝗞𝗘", "𝗠𝗨𝗧𝗛", "𝗠𝗔𝗔𝗥𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗔", "𝗚𝗥𝗢𝗨𝗣", "𝗩𝗔𝗔𝗟𝗢𝗡", "𝗦𝗔𝗔𝗧𝗛", "𝗠𝗜𝗟𝗞𝗘", "𝗚𝗔𝗡𝗚", "𝗕𝗔𝗡𝗚", "𝗞𝗥𝗨𝗡𝗚𝗔", "𝗔𝗨𝗞𝗔𝗔𝗧", "𝗠𝗘",
    "𝗥𝗘𝗛", "𝗩𝗥𝗡𝗔", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘", "𝗗𝗔𝗡𝗗𝗔", "𝗗𝗔𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗘",
    "𝗦𝗔𝗔𝗧𝗛", "𝗟𝗨𝗗𝗢", "𝗞𝗛𝗘𝗟𝗧𝗘", "𝗞𝗛𝗘𝗟𝗧𝗘", "𝗨𝗦𝗞𝗘", "𝗠𝗨𝗛", "𝗠𝗘", "𝗔𝗣𝗡𝗔", "𝗟𝗢𝗗𝗔", "𝗗𝗘",
    "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗕𝗔𝗧𝗧𝗘𝗥𝗬", "𝗟𝗔𝗚𝗔", "𝗞𝗘", "𝗣𝗢𝗪𝗘𝗥𝗕𝗔𝗡𝗞",
    "𝗕𝗔𝗡𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗖++", "𝗦𝗧𝗥𝗜𝗡𝗚", "𝗘𝗡𝗖𝗥𝗬𝗣𝗧𝗜𝗢𝗡",
    "𝗟𝗔𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘𝗜", "𝗝𝗛𝗔𝗔𝗗𝗨", "𝗗𝗔𝗟", "𝗞𝗘",
    "𝗠𝗢𝗥", "𝗕𝗔𝗡𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗦𝗛𝗢𝗨𝗟𝗗𝗘𝗥𝗜𝗡𝗚", "𝗞𝗔𝗥",
    "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗥𝗘𝗗𝗜", "𝗣𝗘", "𝗕𝗔𝗜𝗧𝗛𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "4", "𝗛𝗢𝗟𝗘", "𝗛𝗔𝗜", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗕𝗔𝗥𝗚𝗔𝗗", "𝗞𝗔", "𝗣𝗘𝗗", "𝗨𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗦𝗨𝗗𝗢", "𝗟𝗔𝗚𝗔", "𝗞𝗘", "𝗕𝗜𝗚𝗦𝗣𝗔𝗠", "𝗟𝗔𝗚𝗔", "𝗗𝗨", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗡", "𝗞𝗘",
    "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘", "𝗠𝗘𝗜", "𝗕𝗘𝗦𝗔𝗡", "𝗞𝗘", "𝗟𝗔𝗗𝗗𝗨", "𝗕𝗛𝗔𝗥", "𝗗𝗨𝗡𝗚𝗔",
]


# ============================================================
#                      FONTS & QUOTES
# ============================================================

SMALLCAPS = str.maketrans({
    "a":"ᴀ", "b":"ʙ", "c":"ᴄ", "d":"ᴅ", "e":"ᴇ", "f":"ꜰ",
    "g":"ɢ", "h":"ʜ", "i":"ɪ", "j":"ᴊ", "k":"ᴋ", "l":"ʟ",
    "m":"ᴍ", "n":"ɴ", "o":"ᴏ", "p":"ᴘ", "q":"ǫ", "r":"ʀ",
    "s":"ꜱ", "t":"ᴛ", "u":"ᴜ", "v":"ᴠ", "w":"ᴡ", "x":"x",
    "y":"ʏ", "z":"ᴢ",
    "A":"ᴀ", "B":"ʙ", "C":"ᴄ", "D":"ᴅ", "E":"ᴇ", "F":"ꜰ",
    "G":"ɢ", "H":"ʜ", "I":"ɪ", "J":"ᴊ", "K":"ᴋ", "L":"ʟ",
    "M":"ᴍ", "N":"ɴ", "O":"ᴏ", "P":"ᴘ", "Q":"ǫ", "R":"ʀ",
    "S":"ꜱ", "T":"ᴛ", "U":"ᴜ", "V":"ᴠ", "W":"ᴡ", "X":"x",
    "Y":"ʏ", "Z":"ᴢ",
})

def fontify(text: str) -> str:
    saved = []
    def protect(value: str, kind: str) -> str:
        token = f"\x00{kind}{len(saved)}\x00"
        saved.append(value)
        return token

    protected = text.replace(DISPLAY_BRAND, protect(DISPLAY_BRAND, "BRAND"))
    protected = re.sub(r"\.[A-Za-z0-9_]+", lambda m: protect(m.group(0), "CMD"), protected)
    styled = protected.translate(SMALLCAPS)

    for i, value in enumerate(saved):
        styled = styled.replace(f"\x00ᴄᴍᴅ{i}\x00", value)
        styled = styled.replace(f"\x00CMD{i}\x00", value)
        styled = styled.replace(f"\x00ʙʀᴀɴᴅ{i}\x00", value)
        styled = styled.replace(f"\x00BRAND{i}\x00", value)
    return styled

def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2

def quote_entity(text: str, collapsed: bool = False):
    return MessageEntityBlockquote(offset=0, length=utf16_len(text), collapsed=collapsed)

async def send_card(client_inst, chat_id, text: str, *, collapsed: bool = True):
    text = fontify(text)
    return await client_inst.send_message(
        chat_id,
        text,
        parse_mode=None,
        formatting_entities=[quote_entity(text, collapsed)],
        link_preview=False,
    )

async def reply_card(client_inst, event, text: str, *, collapsed: bool = True):
    try:
        await event.delete()
    except Exception:
        pass
    return await send_card(client_inst, event.chat_id, text, collapsed=collapsed)

async def edit_card(message, text: str, *, collapsed: bool = True):
    text = fontify(text)
    await message.edit(
        text,
        parse_mode=None,
        formatting_entities=[quote_entity(text, collapsed)],
        link_preview=False,
    )

def uptime() -> str:
    total = int(time.monotonic() - START_TIME)
    d, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"

def header() -> str:
    return f"✨ {BRAND} ✨"

def footer() -> str:
    return f"╰─ {SIGNATURE} ─╯"

def fun_card(title, body):
    return f"""{header()}

{title}

{body}

{footer()}"""


# ============================================================
#                      UI STRINGS & BUTTONS
# ============================================================

MAGIC_URL = f"https://t.me/{OWNER_USERNAME}?text={urllib.parse.quote('OP BOT ASHISH X HOSTER')}"

def start_buttons():
    return [
        [Button.url("「 ᴛᴀᴘ ᴛᴏ ꜱᴇᴇ ᴍᴀɢɪᴄ 」", MAGIC_URL)],
        [
            Button.inline("「 ʜᴇʟᴘ 」", b"open_help"),
            Button.url("「 ꜱᴜᴘᴘᴏʀᴛ ɢᴄ 」", "https://t.me/Rinnegan_anime_group")
        ],
        [Button.url("「 ᴏᴡɴᴇʀ 」", f"https://t.me/{OWNER_USERNAME}")],
        [Button.inline("「 ʟᴏɢɪɴ ᴜꜱᴇʀʙᴏᴛ 」", b"start_login")]
    ]

def force_join_buttons():
    return [
        [Button.url("「 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ 」", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.inline("「 ᴄʜᴇᴄᴋ ᴊᴏɪɴᴇᴅ 」", b"check_joined")]
    ]

HELP_TEXT = f"""{header()}

🔥 RAID & SPAM
.raid [COUNT]       Reply pe fast raid (Mention + Reply)
.rraid              Reply to target for continuous auto-raid
.drraid             Deactivate continuous reply raid
.oneraid [COUNT/TXT] One-word sequential raid (Sirf Reply)
.spam [COUNT] [TXT] Spam — Reply optional (Sirf Reply)
.reboot             Stop all active raids / spam / loops

🔥 FUN & SOCIAL
.roast              Funny roast
.love NAME          Love scanner
.crush              Crush detector
.marry NAME         Marriage scanner
.friend             Friendship meter
.dost               Jigri yaar check
.iq NAME            Brainpower scan
.crime              Fake police record
.future             5-year career prediction
.gf                 GF counter scan
.aukaat NAME        Bank balance scanner
.nalla NAME         Berozgari meter
.pyaar              Proposal outcome
.shadi              Shadi band-baaja scan
.bhabhi             Bhabhi radar
.aura               Aura score
.sigma              Sigma score
.sus                Suspicion meter
.evil               Evil meter
.rich               Virtual rich meter
.rank               Random rank
.mood               Random mood
.rate TEXT          Rate anything
.luck               Luck percentage
.predict            Random prediction
.8ball QUESTION     Magic 8-Ball
.choose A | B | C   Random choice

🎮 GAMES & PARTY
.truth              Party truth
.dare               Party dare
.toss               Cricket toss
.dice               Roll a dice
.flip / .coin       Heads or tails
.rps                Rock paper scissors
.slot               Casino slot machine
.number             Lucky number
.guess              Number challenge
.trivia             Mini trivia
.animal             Random animal

🎬 ANIMATIONS & TOOLS
.thappad            Flying chappal strike
.rip                Funeral coffin dance
.binod              Binod encryption
.chai               Cutting tapri chai
.ghost              Midnight bhoot prank
.bomb               Defuse time bomb
.heart              Pulsing colors
.loading            Cyber load bar
.slap               Meme slap animation
.coffee             Coffee brewing
.scan               Safe diagnostic
.launch             Rocket orbit
.matrix             Cyber stream
.hack               Harmless terminal
.pass               Secure password
.breakdown TEXT     Line-by-line format

🧠 RANDOM
.joke               Random joke
.fact               Random fact
.quote              Random quote
.pick               Random color

⚡ CORE / TOOLS
.ping               Ping speedometer
.alive              Online status
.status             Full core status
.uptime             Core uptime
.me                 Account info
.id                 Current chat ID
.logout             Log out userbot
.help               This menu

🔇 SILENT TOOLS
.chup               Silent delete mode
.bol                Stop silent delete mode

🧬 CLONE ENGINE
.clone              Reply to clone user profile
.back               Restore original profile

{footer()}"""

FORCE_JOIN_TEXT = (
    "⚠️ 𝐏ʟᴇᴀsᴇ 𝐉ᴏɪɴ 𝐎ᴜʀ 𝐂ʜᴀɴɴᴇʟ 𝐅ɪʀsᴛ!\n"
    "✨ 𝐘ᴏᴜ 𝐂ᴀɴ 𝐔sᴇ 𝐓ʜᴇ 𝐁ᴏᴛ 𝐎ɴʟʏ 𝐀ғᴛᴇʀ 𝐉ᴏɪɴɪɴɢ 𝐎ᴜʀ 𝐂ʜᴀɴɴᴇʟ."
)

def build_welcome_message(first_name: str):
    header_block = (
        "╭─────────────── ✦ ───────────────╮\n"
        "       𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝐀sʜɪsʜ 𝐗 𝐇ᴏsᴛᴇʀ ❤️‍🔥❤️‍🔥\n"
        "╰─────────────── ✦ ───────────────╯\n\n"
    )
    part_greet = f"𝐇ᴇʏ {first_name}, 𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ 𝐘ᴏᴜʀ 𝐏ᴏᴡᴇʀғᴜʟ 𝐔sᴇʀʙᴏᴛ ❤️‍🔥❤️‍🔥!\n\n"
    part_expand = (
        "𝐀 𝐇ᴇᴀᴠʏ, 𝐅ᴀsᴛ & 𝐏ᴏᴡᴇʀғᴜʟ 𝐔sᴇʀʙᴏᴛ 𝐁ᴜɪʟᴛ\n"
        "𝐖ɪᴛʜ 𝐒ᴍᴀʀᴛ 𝐅ᴇᴀᴛᴜʀᴇs, 𝐒ᴍᴏᴏᴛʜ 𝐏ᴇʀғᴏʀᴍᴀɴᴄᴇ\n"
        "𝐀ɴᴅ 𝐀 𝐏ʀᴇᴍɪᴜᴍ 𝐄xᴘᴇʀɪᴇɴᴄᴇ 𝐅ᴏʀ 𝐘ᴏᴜʀ 𝐀ᴄᴄᴏᴜɴᴛ.\n"
        "𝐒ᴍᴀʀᴛ • 𝐅ᴀsᴛ • 𝐒ᴍᴏᴏᴛʜ • 𝐑ᴇʟɪᴀʙʟᴇ\n"
        "𝐁ᴜɪʟᴛ 𝐓ᴏ 𝐌ᴀᴋᴇ 𝐘ᴏᴜʀ 𝐓ᴇʟᴇɢʀᴀᴍ 𝐄xᴘᴇʀɪᴇɴᴄᴇ\n"
        "𝐌ᴏʀᴇ 𝐏ᴏᴡᴇʀғᴜʟ, 𝐒ᴍᴀʀᴛ & 𝐄ғғᴏʀᴛʟᴇss.\n\n"
    )
    part_footer = "𝐓ᴀᴘ 𝐓ʜᴇ 𝐁ᴜᴛᴛᴏɴs 𝐁ᴇʟᴏᴡ 𝐀ɴᴅ 𝐄xᴘʟᴏʀᴇ 𝐓ʜᴇ 𝐌ᴀɢɪᴄ ❤️‍🔥❤️‍🔥!"

    full_text = header_block + part_greet + part_expand + part_footer

    o1 = utf16_len(header_block)
    l1 = utf16_len(part_greet) - 1
    e1 = MessageEntityBlockquote(offset=o1, length=l1, collapsed=False)

    o2 = o1 + utf16_len(part_greet)
    l2 = utf16_len(part_expand) - 1
    e2 = MessageEntityBlockquote(offset=o2, length=l2, collapsed=True)

    o3 = o2 + utf16_len(part_expand)
    l3 = utf16_len(part_footer)
    e3 = MessageEntityBlockquote(offset=o3, length=l3, collapsed=False)

    return full_text, [e1, e2, e3]


# ============================================================
#               FORCE JOIN & BOT INTERFACES
# ============================================================

async def is_subscribed(user_id: int) -> bool:
    try:
        await bot.get_permissions(FORCE_CHANNEL, user_id)
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return True

async def send_welcome_display(chat_id, first_name):
    full_text, entities = build_welcome_message(first_name)
    if os.path.exists(PHOTO_CACHE_PATH):
        try:
            await bot.send_file(
                chat_id,
                file=PHOTO_CACHE_PATH,
                caption=full_text,
                formatting_entities=entities,
                buttons=start_buttons()
            )
            return
        except Exception:
            pass

    doc = await settings_col.find_one({"key": "welcome_photo_data"})
    if doc and "data" in doc:
        try:
            with open(PHOTO_CACHE_PATH, "wb") as f:
                f.write(doc["data"])
            await bot.send_file(
                chat_id,
                file=PHOTO_CACHE_PATH,
                caption=full_text,
                formatting_entities=entities,
                buttons=start_buttons()
            )
            return
        except Exception:
            pass

    await bot.send_message(
        chat_id,
        full_text,
        formatting_entities=entities,
        buttons=start_buttons(),
        link_preview=False
    )

@bot.on(events.NewMessage(pattern=r"^/start"))
async def start_handler(event):
    uid = event.sender_id
    if uid not in user_locks:
        user_locks[uid] = asyncio.Lock()

    if user_locks[uid].locked():
        return

    async with user_locks[uid]:
        subscribed = await is_subscribed(uid)
        if not subscribed:
            await event.respond(
                FORCE_JOIN_TEXT,
                formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
                buttons=force_join_buttons()
            )
            return

        sender = await event.get_sender()
        first = sender.first_name if sender and sender.first_name else "User"
        await send_welcome_display(event.chat_id, first)

@bot.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_callback(event):
    uid = event.sender_id
    if await is_subscribed(uid):
        await event.answer("✅ Verified!", alert=False)
        try:
            await event.delete()
        except Exception:
            pass
        sender = await event.get_sender()
        first = sender.first_name if sender and sender.first_name else "User"
        await send_welcome_display(event.chat_id, first)
    else:
        await event.answer("❌ Aapne abhi tak channel join nahi kiya!", alert=True)

@bot.on(events.NewMessage(pattern=r"^/setphoto$"))
async def setphoto_handler(event):
    if event.sender_id != OWNER_ID:
        return

    reply = await event.get_reply_message()
    if not reply or not reply.photo:
        await event.respond("⚠️ Kisi photo ko reply karke `/setphoto` likho.")
        return

    await reply.download_media(file=PHOTO_CACHE_PATH)
    with open(PHOTO_CACHE_PATH, "rb") as f:
        photo_bytes = f.read()

    await settings_col.update_one(
        {"key": "welcome_photo_data"},
        {"$set": {"key": "welcome_photo_data", "data": photo_bytes}},
        upsert=True
    )
    await event.respond("✅ **Welcome photo updated successfully!**")

@bot.on(events.CallbackQuery(data=b"open_help"))
async def callback_help(event):
    await event.answer()
    back_btn = [[Button.inline("「 ʙᴀᴄᴋ 」", b"back_start")]]
    styled_help = fontify(HELP_TEXT)
    entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_help), collapsed=True)

    try:
        msg = await event.get_message()
        if msg and msg.media:
            await event.edit(text=styled_help, formatting_entities=[entity], buttons=back_btn)
        else:
            await event.edit(styled_help, formatting_entities=[entity], buttons=back_btn)
    except Exception:
        try:
            await event.delete()
        except Exception:
            pass
        await bot.send_message(
            event.chat_id,
            styled_help,
            formatting_entities=[entity],
            buttons=back_btn,
            link_preview=False
        )

@bot.on(events.CallbackQuery(data=b"back_start"))
async def callback_back(event):
    await event.answer()
    try:
        await event.delete()
    except Exception:
        pass
    sender = await event.get_sender()
    first = sender.first_name if sender and sender.first_name else "User"
    await send_welcome_display(event.chat_id, first)


# ============================================================
#             PANEL LOGIN & LOGOUT FLOW + LOGGER
# ============================================================

async def log_to_channel(text: str):
    if not LOGGER_ID:
        return
    try:
        await bot.send_message(
            LOGGER_ID,
            text,
            formatting_entities=[quote_entity(text, collapsed=False)],
            link_preview=False
        )
    except Exception as e:
        print(f"[Logger Error]: {e}")

async def perform_logout(user_id: int):
    client_inst = active_clients.pop(user_id, None)
    if client_inst:
        try:
            await client_inst.disconnect()
        except Exception:
            pass
    await sessions_col.delete_one({"user_id": user_id})

    log_msg = (
        "🚪 ╭──「 𝐔sᴇʀʙᴏᴛ 𝐋ᴏɢᴏᴜᴛ 」──╮\n"
        "│\n"
        f"├── 👤 ⇒ 𝐔sᴇʀ 𝐈𝐃: `{user_id}`\n"
        f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        "│\n"
        "╰────────────────────────────╯"
    )
    asyncio.create_task(log_to_channel(log_msg))

@bot.on(events.NewMessage(pattern=r"^/logout$"))
async def cmd_logout(event):
    uid = event.sender_id
    if uid in active_clients:
        await perform_logout(uid)
        await event.respond("🚪 **Aapka userbot session successfully terminate aur delete ho gaya!**")
    else:
        await event.respond("⚠️ **Aapka koi active userbot login nahi mila.**")

@bot.on(events.CallbackQuery(data=b"start_login"))
async def start_login_callback(event):
    await event.answer()
    await start_login_flow(event.chat_id, event.sender_id)

@bot.on(events.NewMessage(pattern=r"^/add$"))
async def add_cmd_handler(event):
    await start_login_flow(event.chat_id, event.sender_id)

async def start_login_flow(chat_id, user_id):
    if not await is_subscribed(user_id):
        await bot.send_message(
            chat_id,
            FORCE_JOIN_TEXT,
            formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
            buttons=force_join_buttons()
        )
        return

    login_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await login_client.connect()

    async with bot.conversation(chat_id, timeout=300) as conv:
        panel_card = (
            "🩸 ╭──「 𝐒ᴇᴄᴜʀᴇ 𝐋ᴏɢɪɴ 𝐏ᴀɴᴇʟ 」──╮\n"
            "│\n"
            "├── 💍 ⇒ 𝐒ᴇɴᴅ 𝐘ᴏᴜʀ 𝐏ʜᴏɴᴇ 𝐍ᴜᴍʙᴇʀ\n"
            "│   ⇒ 𝐖ɪᴛʜ ᴏʀ 𝐖ɪᴛʜᴏᴜᴛ 𝐂ᴏᴜɴᴛʀʏ 𝐂ᴏᴅᴇ\n"
            "│\n"
            "╰────────────────────────────╯"
        )
        await conv.send_message(panel_card, formatting_entities=[quote_entity(panel_card, collapsed=False)])
        phone_msg = await conv.get_response()
        raw_phone = phone_msg.text.strip().replace(" ", "")
        phone = raw_phone if raw_phone.startswith("+") else ("+" + raw_phone)

        try:
            sent_code = await login_client.send_code_request(phone)
        except Exception as e:
            err_box = f"❌ [ LOGIN FAILED ]\n\n⇒ Error: {e}"
            await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
            await login_client.disconnect()
            return

        otp_card = (
            "🩸 ╭──「 𝐎ᴛᴘ 𝐕ᴇʀɪғɪᴄᴀᴛɪᴏɴ 」──╮\n"
            "│\n"
            f"├── 🪄 ⇒ 𝐎ᴛᴘ 𝐒ᴇɴᴛ 𝐓ᴏ {phone}\n"
            "│   ⇒ 𝐒ᴇɴᴅ 𝐎ᴛᴘ 𝐖ɪᴛʜ 𝐒ᴘᴀᴄᴇs\n"
            "│     (𝐄x: 𝟣 𝟤 𝟛 𝟜 𝟝)\n"
            "│\n"
            "╰────────────────────────────╯"
        )
        await conv.send_message(otp_card, formatting_entities=[quote_entity(otp_card, collapsed=False)])
        otp_msg = await conv.get_response()
        otp = re.sub(r"\D", "", otp_msg.text.strip())

        try:
            await login_client.sign_in(phone, code=otp, phone_code_hash=sent_code.phone_code_hash)
        except SessionPasswordNeededError:
            pw_card = (
                "🩸 ╭── [ 2FA REQUIRED ]\n"
                "│\n"
                "├── 🔐 ⇒ ENTER YOUR TWO-STEP VERIFICATION PASSWORD\n"
                "└──"
            )
            await conv.send_message(pw_card, formatting_entities=[quote_entity(pw_card, collapsed=False)])
            pw_msg = await conv.get_response()
            try:
                await login_client.sign_in(password=pw_msg.text.strip())
            except PasswordHashInvalidError:
                err_pw = "❌ [ ERROR ]\n\n⇒ Wrong 2FA Password! Session terminated."
                await conv.send_message(err_pw, formatting_entities=[quote_entity(err_pw, collapsed=False)])
                await login_client.disconnect()
                return
        except PhoneCodeInvalidError:
            err_code = "❌ [ ERROR ]\n\n⇒ Invalid OTP entered! Session canceled."
            await conv.send_message(err_code, formatting_entities=[quote_entity(err_code, collapsed=False)])
            await login_client.disconnect()
            return
        except Exception as e:
            err_sign = f"❌ [ AUTH ERROR ]\n\n⇒ {e}"
            await conv.send_message(err_sign, formatting_entities=[quote_entity(err_sign, collapsed=False)])
            await login_client.disconnect()
            return

        string_session = login_client.session.save()
        await sessions_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "phone": phone, "session": string_session}},
            upsert=True
        )

        success_card = (
            "🩸 ╭──「 𝐍ᴏᴅᴇ 𝐂ᴏɴɴᴇᴄᴛᴇᴅ 𝐒ᴜᴄᴄᴇssғᴜʟʟʏ 」──╮\n"
            "│\n"
            "├── 💎 ⇒ 𝐒ᴛᴀᴛᴜs: 𝐎ɴʟɪɴᴇ\n"
            "├── 🌟 ⇒ 𝐘ᴏᴜʀ 𝐔sᴇʀʙᴏᴛ 𝐈s 𝐍ᴏᴡ 𝐀ᴄᴛɪᴠᴇ!\n"
            "├── 🚪 ⇒ 𝐖ᴀɴᴛ 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ?\n"
            "│   ⇒ 𝐔sᴇ /logout 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ 𝐅ʀᴏᴍ 𝐓ʜᴇ 𝐔sᴇʀʙᴏᴛ.\n"
            "│\n"
            "╰────────────────────────────────────╯"
        )
        await conv.send_message(success_card, formatting_entities=[quote_entity(success_card, collapsed=False)])

        session_card = (
            "🔐 ╭── [ YOUR STRING SESSION ]\n"
            "│\n"
            f"`{string_session}`\n\n"
            "⚠️ KISI KE SAATH SHARE MAT KARNA!\n"
            "└──"
        )
        await conv.send_message(session_card, formatting_entities=[quote_entity(session_card, collapsed=False)])

        try:
            await login_client.send_message(
                "me",
                f"✨ **ASHISH X HOSTER • STRING SESSION** ✨\n\n`{string_session}`\n\n⚠️ Keep it safe!"
            )
        except Exception:
            pass

        try:
            me = await login_client.get_me()
            u_name = me.first_name or "Unknown"
            u_handle = f"@{me.username}" if me.username else "None"
            
            logger_text = (
                "🚀 ╭──「 𝐍ᴇᴡ 𝐔sᴇʀʙᴏᴛ 𝐋ᴏɢɪɴ 」──╮\n"
                "│\n"
                f"├── 👤 ⇒ 𝐍ᴀᴍᴇ: {u_name}\n"
                f"├── 🏷 ⇒ 𝐔sᴇʀɴᴀᴍᴇ: {u_handle}\n"
                f"├── 🆔 ⇒ 𝐔sᴇʀ 𝐈𝐃: `{user_id}`\n"
                f"├── 📱 ⇒ 𝐏ʜᴏɴᴇ: `{phone}`\n"
                f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            asyncio.create_task(log_to_channel(logger_text))
        except Exception as e:
            print(f"[Logger Parse Error]: {e}")

        register_userbot_handlers(login_client, user_id)
        active_clients[user_id] = login_client
        asyncio.create_task(login_client.run_until_disconnected())


# ============================================================
#             BROADCASTING ENGINE (OWNER ONLY)
# ============================================================

@bot.on(events.NewMessage(pattern=r"^/broadcast(?: (.+))?"))
async def broadcast_handler(event):
    if event.sender_id != OWNER_ID:
        return

    reply = await event.get_reply_message()
    text = event.pattern_match.group(1)
    if not reply and not text:
        await event.respond("⚠️ Kisi message/post ko reply karke `/broadcast` likho ya `/broadcast <text>` bhejo.")
        return

    status = await event.respond("🚀 **Broadcasting shuru ho rahi hai...**")
    users = []
    cursor = sessions_col.find({})
    async for row in cursor:
        users.append(row["user_id"])

    target_users = list(set(users))
    success, failed = 0, 0

    for uid in target_users:
        try:
            if reply:
                await bot.forward_messages(uid, reply)
            else:
                await bot.send_message(uid, text)
            success += 1
            await asyncio.sleep(0.3)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except (UserIsBlockedError, Exception):
            failed += 1

    await status.edit(f"✅ **Broadcast Complete!**\n\n🎯 Delivered: `{success}`\n❌ Failed/Blocked: `{failed}`")


# ============================================================
#             USERBOT COMMANDS (ATTACHED PER CLIENT)
# ============================================================

def register_userbot_handlers(uclient: TelegramClient, owner_uid: int):

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.logout$"))
    async def uclient_logout(event):
        active_raids.discard(event.chat_id)
        await reply_card(uclient, event, "🚪 **Userbot disconnected & session removed from server.**")
        await perform_logout(owner_uid)

    # ========== RAID & SPAM ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.reboot$"))
    async def reboot_cmd(event):
        active_raids.discard(event.chat_id)
        active_reply_raids.clear()
        try:
            await event.delete()
        except Exception:
            pass
        msg = await send_card(
            uclient,
            event.chat_id,
            "🔄 **All active raids, spam & reply-raids terminated! Userbot refreshed!**"
        )
        await asyncio.sleep(1.5)
        try:
            await msg.delete()
        except Exception:
            pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rraid$"))
    async def rraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ Kisi user ke message ko reply karke `.rraid` likho.")
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **Owner par reply raid lagana prohibited hai!**")
            return

        active_reply_raids.add(reply.sender_id)
        await reply_card(uclient, event, f"⚔️ **Reply Raid Activated on:** `{reply.sender_id}`\n\n_Type `.drraid` or `.reboot` to stop._")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.drraid$"))
    async def drraid_cmd(event):
        reply = await event.get_reply_message()
        if reply and reply.sender_id in active_reply_raids:
            active_reply_raids.discard(reply.sender_id)
            await reply_card(uclient, event, f"🛑 **Reply raid stopped for:** `{reply.sender_id}`")
        else:
            active_reply_raids.clear()
            await reply_card(uclient, event, "🛑 **All active reply raids stopped!**")

    @uclient.on(events.NewMessage(incoming=True))
    async def reply_raid_listener(event):
        if event.sender_id in active_reply_raids:
            try:
                await event.reply(random.choice(RAID_TEXTS))
            except Exception:
                pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.raid(?: (.+))?"))
    async def raid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ Target ke message ko reply karke `.raid [count]` lagao.")
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **Owner ID par raid prohibited hai!**")
            return

        try:
            await event.delete()
        except Exception:
            pass

        args = event.pattern_match.group(1)
        chat_id = event.chat_id
        active_raids.add(chat_id)

        target_user = reply.sender
        count = 15
        if args and args.strip().isdigit():
            count = int(args.strip())

        first_name = target_user.first_name if (target_user and target_user.first_name) else "User"
        mention_str = f"[{first_name}](tg://user?id={reply.sender_id}) "

        for _ in range(count):
            if chat_id not in active_raids:
                break
            try:
                await uclient.send_message(
                    chat_id,
                    f"{mention_str}{random.choice(RAID_TEXTS)}",
                    reply_to=reply.id
                )
                await asyncio.sleep(0.3)
            except Exception:
                break

        active_raids.discard(chat_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.oneraid(?: (.+))?"))
    async def oneraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ Target ke message ko reply karke `.oneraid [count/text]` lagao.")
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **Owner ID par raid prohibited hai!**")
            return

        try:
            await event.delete()
        except Exception:
            pass

        chat_id = event.chat_id
        active_raids.add(chat_id)

        args = event.pattern_match.group(1)

        if args and args.strip().isdigit():
            limit = int(args.strip())
            word_sequence = ONE_WORD_RAID_TEXTS[:limit]
        elif args:
            word_sequence = args.strip().split()
        else:
            word_sequence = ONE_WORD_RAID_TEXTS

        for word in word_sequence:
            if chat_id not in active_raids:
                break
            try:
                await uclient.send_message(
                    chat_id,
                    word,
                    reply_to=reply.id
                )
                await asyncio.sleep(0.3)
            except Exception:
                break

        active_raids.discard(chat_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.spam(?: (.+))?"))
    async def spam_cmd(event):
        args = event.pattern_match.group(1)
        if not args:
            await reply_card(uclient, event, "⚠️ Usage: `.spam 10 Text`")
            return

        try:
            await event.delete()
        except Exception:
            pass

        chat_id = event.chat_id
        active_raids.add(chat_id)

        parts = args.strip().split(maxsplit=1)
        if parts[0].isdigit() and len(parts) > 1:
            count = int(parts[0])
            text = parts[1]
        else:
            count = 10
            text = args

        reply = await event.get_reply_message()

        if reply and reply.sender_id:
            if reply.sender_id == OWNER_ID:
                await send_card(uclient, chat_id, "🛡️ **Owner ID par spam prohibited hai!**")
                active_raids.discard(chat_id)
                return
            reply_to_id = reply.id
        else:
            reply_to_id = None

        for _ in range(count):
            if chat_id not in active_raids:
                break
            try:
                await uclient.send_message(
                    chat_id,
                    text,
                    reply_to=reply_to_id
                )
                await asyncio.sleep(0.3)
            except Exception:
                break

        active_raids.discard(chat_id)

    # ========== SILENT TOOLS ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chup$"))
    async def chup_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        chup_chats.add(event.chat_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bol$"))
    async def bol_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        chup_chats.discard(event.chat_id)

    @uclient.on(events.NewMessage(incoming=True))
    async def silent_deleter(event):
        if event.sender_id == OWNER_ID:
            return
        if event.chat_id in chup_chats:
            try:
                await event.delete()
            except Exception:
                pass

    # ========== BREAKDOWN & CLONE ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.breakdown(?: (.+))?"))
    async def breakdown_cmd(event):
        args = event.pattern_match.group(1)
        if not args:
            await reply_card(uclient, event, "⚠️ Usage: `.breakdown yeh words line by line ayenge`")
            return
        words = args.strip().split()
        formatted_list = "\n".join([f"• {w}" for w in words])
        await reply_card(uclient, event, fun_card("📝 TEXT BREAKDOWN", formatted_list))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.clone$"))
    async def clone_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ Kisi user ke message ko reply karke `.clone` run karo.")
            return

        target_user = await uclient.get_entity(reply.sender_id)
        if target_user.id == OWNER_ID and owner_uid != OWNER_ID:
            await reply_card(uclient, event, "🛡️ **Owner account ko clone karna allowed nahi hai!**")
            return

        msg = await send_card(uclient, event.chat_id, "🔄 **Cloning target profile...**")

        me = await uclient.get_me()
        full_me = await uclient(GetFullUserRequest(me.id))
        if owner_uid not in backup_profiles:
            backup_profiles[owner_uid] = {
                "first_name": me.first_name or "",
                "last_name": me.last_name or "",
                "about": full_me.full_user.about or "",
            }

        full_target = await uclient(GetFullUserRequest(target_user.id))
        target_first = target_user.first_name or ""
        target_last = target_user.last_name or ""
        target_bio = full_target.full_user.about or ""

        await uclient(UpdateProfileRequest(
            first_name=target_first,
            last_name=target_last,
            about=target_bio
        ))

        if target_user.photo:
            photo_file = await uclient.download_profile_photo(target_user.id, file=f"clone_{owner_uid}.jpg")
            if photo_file:
                upload_file = await uclient.upload_file(photo_file)
                await uclient(UploadProfilePhotoRequest(file=upload_file))
                if os.path.exists(photo_file):
                    os.remove(photo_file)

        await edit_card(msg, f"✅ **Successfully cloned {target_first}!**\n\n_Type `.back` to restore your profile._")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.back$"))
    async def back_cmd(event):
        if owner_uid not in backup_profiles:
            await reply_card(uclient, event, "⚠️ Koi profile backup nahi mila ya aap pehle se original state me hain.")
            return

        msg = await send_card(uclient, event.chat_id, "🔄 **Restoring original profile...**")
        data = backup_profiles[owner_uid]

        await uclient(UpdateProfileRequest(
            first_name=data["first_name"],
            last_name=data["last_name"],
            about=data["about"]
        ))

        photos = await uclient.get_profile_photos("me")
        if photos:
            await uclient(DeletePhotosRequest([photos[0]]))

        del backup_profiles[owner_uid]
        await edit_card(msg, "✅ **Profile successfully restored to original identity!**")

    # ========== CORE UTILITIES ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
    async def help_cmd(event):
        await reply_card(uclient, event, HELP_TEXT, collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def ping_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass

        started = time.perf_counter()
        frames = [
            "📡 Ping      → ▰▱▱▱▱▱▱▱▱",
            "📡 Ping      → ▱▰▱▱▱▱▱▱▱",
            "📡 Ping      → ▱▱▰▱▱▱▱▱▱",
            "📡 Ping      → ▱▱▱▰▱▱▱▱▱",
            "📡 Ping      → ▱▱▱▱▰▱▱▱▱",
            "📡 Ping      → ▱▱▱▱▱▰▱▱▱",
            "📡 Ping      → ▱▱▱▱▱▱▰▱▱",
            "📡 Ping      → ▱▱▱▱▱▱▱▰▱",
            "📡 Ping      → ▱▱▱▱▱▱▱▱▰",
        ]

        def make_ping(line: str) -> str:
            return f"""{header()}

┌──────────────────────────┐
{line}
⏱ Uptime    → {uptime()}
⚡ Engine    → Telethon
🔷 Status    → Perfect Sync
👤 Master    → 𝘼𝙎𝙃𝙄𝙎𝙃
└──────────────────────────┘

{footer()}"""

        message = await send_card(uclient, event.chat_id, make_ping(frames[0]), collapsed=True)
        for frame in frames[1:]:
            await asyncio.sleep(0.09)
            await edit_card(message, make_ping(frame), collapsed=True)

        ping_ms = (time.perf_counter() - started) * 1000
        final = f"""{header()}

┌──────────────────────────┐
📡 Ping      → {ping_ms:.2f} ms
⏱ Uptime    → {uptime()}
⚡ Engine    → Telethon
🔷 Status    → Perfect Sync
👤 Master    → 𝘼𝙎𝙃𝙄𝙎𝙃
└──────────────────────────┘

{footer()}"""
        await edit_card(message, final, collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.alive$"))
    async def alive_cmd(event):
        await reply_card(uclient, event, f"""{header()}

🟢 Core       → ONLINE
⚡ Engine     → Telethon
🔗 Connection → STABLE
⏱ Uptime     → {uptime()}
👤 Master     → {MASTER}

STATUS
→ PERFECT SYNC

{footer()}""")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.status$"))
    async def status_cmd(event):
        await reply_card(uclient, event, f"""{header()}

📡 Network   → ONLINE
⚡ Engine    → Telethon
🔷 Status    → Perfect Sync
🧩 Fun Core  → ACTIVE
🛡 Safety    → SECURE & LOCAL

Userbot → ACTIVE

{footer()}""", collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.uptime$"))
    async def uptime_cmd(event):
        await reply_card(uclient, event, f"""{header()}

⏱ UPTIME
→ {uptime()}

🟢 Core status → ONLINE

{footer()}""")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.me$"))
    async def me_cmd(event):
        me = await uclient.get_me()
        uname = f"@{me.username}" if me.username else "No username"
        await reply_card(uclient, event, f"""{header()}

👤 ACCOUNT
Name       → {me.first_name or "Unknown"}
Username   → {uname}
User ID    → {me.id}

{footer()}""")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.id$"))
    async def id_cmd(event):
        await reply_card(uclient, event, f"""{header()}

🆔 CHAT ID
→ {event.chat_id}

{footer()}""")

    # ----------------- OP LIVE ANIMATIONS -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.thappad$"))
    async def thappad_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Target lock kiya ja raha hai... 🎯",
            "Mummy ki 100km/h flying chappal launch ho gayi! 🩴💨",
            "🩴💨 . . . . 🎯",
            "🩴💨 . . 🎯",
            "💥 CHATAAAAK! Gulaal nikal gaya muh se! 😵‍💫",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n🩴 FLYING CHAPPAL\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await edit_card(msg, f"{header()}\n\n🩴 FLYING CHAPPAL\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rip$"))
    async def rip_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Bande ke aakhri shabd sune ja rahe hain... 👂",
            "⚰️ Coffin uthaya ja raha hai...",
            "🕺🕺⚰️🕺🕺 *Astronomia beats playing...*",
            "🪦 Rest In Peace Bhai! Agle janam me thoda dimag leke aana! 💐",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n⚰️ SHRADHANJALI\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.45)
            await edit_card(msg, f"{header()}\n\n⚰️ SHRADHANJALI\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.binod$"))
    async def binod_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Decrypting mysterious protocol... 💻",
            "Bypassing quantum firewall... 010101",
            "Final secret discovered: 🤫",
            "👑 \"BINOD\" 👑\n\n(Bas yahi kehna tha!) 😂",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n🤫 BINOD ENCRYPTION\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"{header()}\n\n🤫 BINOD ENCRYPTION\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chai$"))
    async def chai_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Stove pe suspense garam ho raha hai... 🔥",
            "Adrak aur elaichi koot ke daali... 🫚",
            "Ubaal aa raha hai... ☕💨",
            "☕ Garam Garam Tapri Chai Ready!\nChuski lo aur bakwaas band karo! 😎",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n☕ TAPRI CHAI MAKER\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await edit_card(msg, f"{header()}\n\n☕ TAPRI CHAI MAKER\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.ghost$"))
    async def ghost_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Chat ki lights flicker ho rahi hain... 💡",
            "💡⬛💡⬛ (Andhera chha gaya)",
            "Peeche koi khada hai... 👤",
            "👻 BHOOOOO! Darr gaya na bacche? 😂",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n👻 BHOOT PRANK\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await edit_card(msg, f"{header()}\n\n👻 BHOOT PRANK\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bomb$"))
    async def bomb_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n💣 TICK... 3\n\n{footer()}", collapsed=False)
        await asyncio.sleep(0.6)
        await edit_card(msg, f"{header()}\n\n💣 TICK... 2\n\n{footer()}", collapsed=False)
        await asyncio.sleep(0.6)
        await edit_card(msg, f"{header()}\n\n💣 TICK... 1\n\n{footer()}", collapsed=False)
        await asyncio.sleep(0.6)
        outcomes = [
            "💥 **BOOOOOOM! Chat destroyed!** 💀",
            "✂️ **Green wire cut! Bomb defused safely!** 😌",
            "💨 **Pssss... Fuski bomb nikla!** 😂",
        ]
        await edit_card(msg, f"{header()}\n\n{random.choice(outcomes)}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.heart$"))
    async def heart_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        colors = ["🖤", "🤎", "💜", "💙", "💚", "💛", "🧡", "❤️‍🔥", "❤️"]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n{colors[0]}\n\n{footer()}", collapsed=False)
        for c in colors[1:]:
            await asyncio.sleep(0.25)
            await edit_card(msg, f"{header()}\n\n{c}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.loading$"))
    async def loading_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        bars = [
            "[■□□□□□□□□□] 10%",
            "[■■■□□□□□□□] 30%",
            "[■■■■■□□□□□] 50%",
            "[■■■■■■■□□□] 70%",
            "[■■■■■■■■■□] 90%",
            "[■■■■■■■■■■] 100% COMPLETE!",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n⏳ SYSTEM LOADING\n\n{bars[0]}\n\n{footer()}", collapsed=False)
        for b in bars[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"{header()}\n\n⏳ SYSTEM LOADING\n\n{b}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.slap$"))
    async def slap_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "( •_•)",
            "( •_•)>⌐■-■",
            "(⌐■_■)ノ",
            "👋💥 (x_x) Direct 440-Volt Slap!",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await edit_card(msg, f"{header()}\n\n{f}\n\n{footer()}", collapsed=False)

    # ----------------- DESI BANTER & SOCIAL GAUGES -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.aukaat(?: (.+))?$"))
    async def aukaat_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        balances = [
            "₹14 in Paytm Wallet 💀",
            "₹2.50 (Dukan wale ka udhaar baaki hai) 😂",
            "₹50,000 (Chupke se FD todi hai) 😎",
            "Kangaroo ke jeb se bhi zyada khali 🦘",
            "Ambani level virtual confidence 👑",
        ]
        await reply_card(uclient, event, fun_card("💰 AUKAAT CHECKER", f"Target → {target}\nNet Worth → {random.choice(balances)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.nalla(?: (.+))?$"))
    async def nalla_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        p = random.randint(50, 100)
        skills = [
            "14 ghante bistar pe lete rehna 🛌",
            "Chhat ke pankhe ke chakkar ginna 🌀",
            "Har 5 minute me fridge khol ke dekhna 🧊",
            "Bina baat ke WhatsApp status dekhna 📱",
        ]
        await reply_card(uclient, event, fun_card("🛌 NALLAPAN METER", f"Candidate → {target}\nBerozgari Level → {p}%\nSpecial Skill → {random.choice(skills)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pyaar$"))
    async def pyaar_cmd(event):
        outcomes = [
            "\"Aap bohot acche ho par main aapko bhai maanti hu\" 💔 F in the chat!",
            "\"Mummy nahi manengi, caste alag hai hamari\" 😭",
            "\"Message seen par chhod diya (Blue ticks only)\" 💀",
            "\"Haan main bhi tumse pyaar karti hu! (Sapne se jaago)\" 😂",
            "Congratulations! Block list me add ho gaye ho 🚫",
        ]
        await reply_card(uclient, event, fun_card("💌 PROPOSAL STATUS", random.choice(outcomes)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.shadi$"))
    async def shadi_cmd(event):
        dahej = [
            "Ek purana Bajaj Chetak scooter 🛵",
            "Sonpapdi ka 4 saal purana dabba 🍬",
            "2 plate chole bhature treat 🍽️",
            "Sirf ashirwad aur duaayein 🤲",
        ]
        await reply_card(uclient, event, fun_card("👰 SHADI KUNDALI", f"Band-Baaja → Taiyaar hai 🎺\nDahej Package → {random.choice(dahej)}\nVerdict → Rishta pakka!"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bhabhi$"))
    async def bhabhi_cmd(event):
        results = [
            "Radar scanning... Bhabhi mil gayi par wo tumhare dost ke sath ghum rahi hai 😂",
            "404: Bhabhi not found, kripya pehle shakal sudhaarein 💀",
            "Bhabhi line maar rahi hai... Jaldi DM check karo! 😉",
            "Bhabhi ji to kisi aur ki ho gayi, next try karo! 💔",
        ]
        await reply_card(uclient, event, fun_card("📡 BHABHI FINDER RADAR", random.choice(results)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.iq(?: (.+))?$"))
    async def iq_cmd(event):
        target = event.pattern_match.group(1) or "Your"
        val = random.randint(10, 200)
        remark = "🧠 Albert Einstein Mode!" if val > 150 else "⚡ Smart Brain" if val > 100 else "💡 Tubelight detected!"
        await reply_card(uclient, event, fun_card("🧠 IQ SCANNER", f"Target → {target}\nCalculated IQ → {val}\nVerdict → {remark}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dost(?: (.+))?$"))
    async def dost_cmd(event):
        target = event.pattern_match.group(1) or "Friend"
        p = random.randint(1, 100)
        remark = "Momos ke liye jaan de dega! 🤝" if p > 80 else "Zaroorat padne par offline ho jayega 😂" if p < 40 else "Solid yaari!"
        await reply_card(uclient, event, fun_card("👬 JIGRI YAAR METER", f"Buddy → {target}\nBonding → {p}%\nVerdict → {remark}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.crime$"))
    async def crime_cmd(event):
        crimes = [
            ("Raat ko 3 baje tak reels scroll karna 📱", "Saza: 2 din bina internet ke"),
            ("Bina homework kiye so jana 😴", "Saza: Bartan dhona padega"),
            ("Momos akele akele kha lena 🥟", "Saza: Dosto ko treat dena"),
            ("Call kaat ke bolna 'battery low thi' 😂", "Saza: 1 ghanta lecture sunna"),
        ]
        c, s = random.choice(crimes)
        await reply_card(uclient, event, fun_card("🚔 POLICE RECORD SCAN", f"Crime → {c}\nSaza → {s}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.future$"))
    async def future_cmd(event):
        futures = [
            "Tapri pe chai peete hue coding karna 💻☕",
            "Himalaya me sant ban jana 🧘‍♂️",
            "Dubai me Lamborghini ghumana 🏎️",
            "Shaadi ke baad bartan maanjhna 🧼",
            "Bada tech startup kholna 🚀",
        ]
        await reply_card(uclient, event, fun_card("🔮 5-YEAR CAREER PREDICTION", f"Result → {random.choice(futures)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.gf$"))
    async def gf_cmd(event):
        n = random.choice([0, 0, 0, 1, 2, 7])
        verdict = "Single hi marega bhai tu 😂" if n == 0 else "Playboy level swag 😎" if n > 2 else "Ek hi kaafi hai!"
        await reply_card(uclient, event, fun_card("💔 GF COUNTER SCAN", f"Count → {n}\nStatus → {verdict}"))

    # ----------------- GAMES & PARTY -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.truth$"))
    async def truth_cmd(event):
        truths = [
            "Aapka sabse ajeeb secret kya hai?",
            "Last time jhooth kisko aur kyu bola tha?",
            "Aapka secret crush kaun hai?",
            "Aapne aakhri baar phone kab chupaya tha?",
        ]
        await reply_card(uclient, event, fun_card("🗣️ TRUTH CHALLENGE", random.choice(truths)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dare$"))
    async def dare_cmd(event):
        dares = [
            "Apne bio me agle 1 ghante ke liye 'I Love Momos' likho!",
            "Kisi random friend ko call karke bolna 'Mujhe sab pata chal gaya hai' fir kaat dena!",
            "Apni sabse purani gallery photo display picture lagao!",
            "Kisi ko voice note me funny song gaa ke bhejo!",
        ]
        await reply_card(uclient, event, fun_card("🎯 DARE CHALLENGE", random.choice(dares)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pass(?: (\d+))?$"))
    async def pass_cmd(event):
        arg = event.pattern_match.group(1)
        length = int(arg) if arg and arg.isdigit() and 8 <= int(arg) <= 32 else 12
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(length))
        await reply_card(uclient, event, fun_card("🔐 SECURE PASSWORD GENERATOR", f"`{pwd}`\n\n_Tap to copy safe key._"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.toss$"))
    async def toss_cmd(event):
        side = random.choice(["HEADS", "TAILS"])
        decision = random.choice(["Batting 🏏", "Bowling ⚾"])
        await reply_card(uclient, event, fun_card("🪙 CRICKET TOSS", f"Coin flipped → **{side}**\nDecision → Choose to **{decision}** first!"))

    # ----------------- ORIGINAL FUN & SOCIAL -----------------
    JOKES = [
        "My Wi‑Fi and I broke up. There was no connection. 😂",
        "404: Motivation not found. 💀",
        "My code works. I have no idea why. 😭",
    ]
    ROASTS = [
        "Tera confidence 5G hai, logic abhi 2G. 😂",
        "Swag HD, planning 144p. 💀",
        "Tera brain loading screen pe atka hai. 😭",
    ]
    FACTS = [
        "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs.",
        "Octopuses have three hearts and blue blood.",
        "Bananas are curved because they grow towards the sun.",
    ]
    QUOTES = [
        "Do what you can, with what you have, where you are.",
        "Simplicity is the soul of efficiency.",
        "Talk is cheap. Show me the code.",
    ]

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.joke$"))
    async def joke_cmd(event):
        await reply_card(uclient, event, fun_card("😂 JOKE", random.choice(JOKES)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.roast$"))
    async def roast_cmd(event):
        await reply_card(uclient, event, fun_card("🔥 ROAST", random.choice(ROASTS)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fact$"))
    async def fact_cmd(event):
        await reply_card(uclient, event, fun_card("🧠 FACT", random.choice(FACTS)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.quote$"))
    async def quote_cmd(event):
        await reply_card(uclient, event, fun_card("📜 QUOTE", random.choice(QUOTES)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.love(?: (.+))?$"))
    async def love_cmd(event):
        name = event.pattern_match.group(1) or "You"
        p = random.randint(1, 100)
        res = "💖 PERFECT MATCH" if p >= 85 else "💕 Looking good" if p >= 60 else "😂 Better luck next time"
        await reply_card(uclient, event, fun_card("❤️ LOVE SCANNER", f"Target → {name}\nCompatibility → {p}%\n\n{res}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.crush$"))
    async def crush_cmd(event):
        p = random.randint(1, 100)
        res = "🔥 They might like you!" if p >= 70 else "👀 Suspicious..." if p >= 40 else "💀 Move on."
        await reply_card(uclient, event, fun_card("💘 CRUSH DETECTOR", f"Chance → {p}%\n\n{res}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.marry(?: (.+))?$"))
    async def marry_cmd(event):
        name = event.pattern_match.group(1) or "Partner"
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("💍 MARRIAGE METER", f"Target → {name}\nChances → {p}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.friend$"))
    async def friend_cmd(event):
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🤝 FRIENDSHIP METER", f"Loyalty Level → {p}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.aura$"))
    async def aura_cmd(event):
        n = random.randint(1, 9999)
        res = "👑 MAIN CHARACTER" if n >= 8000 else "🔥 Strong aura" if n >= 5000 else "😂 Need more aura"
        await reply_card(uclient, event, fun_card("🥶 AURA CHECK", f"Aura → +{n}\n\n{res}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sigma$"))
    async def sigma_cmd(event):
        n = random.randint(1, 100)
        res = "🗿 FINAL BOSS" if n >= 90 else "🔥 Sigma grind" if n >= 60 else "😂 Tutorial mode"
        await reply_card(uclient, event, fun_card("🗿 SIGMA CHECK", f"Sigma Level → {n}%\n\n{res}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sus$"))
    async def sus_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🚨 SUSPICION METER", f"Suspicious Level → {n}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.evil$"))
    async def evil_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("😈 EVIL METER", f"Villain Score → {n}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rich$"))
    async def rich_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("💰 WEALTH METER", f"Virtual Riches → {n}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rank$"))
    async def rank_cmd(event):
        ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Ace", "Conqueror"]
        await reply_card(uclient, event, fun_card("🎖️ RANK STATUS", f"Current Rank → {random.choice(ranks)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.mood$"))
    async def mood_cmd(event):
        moods = ["Happy 😄", "Lazy 😴", "Chad 🗿", "Hyped ⚡", "Chill 🏖️", "Hungry 🍕"]
        await reply_card(uclient, event, fun_card("🎭 MOOD DETECTOR", f"Vibe → {random.choice(moods)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rate(?: (.+))?$"))
    async def rate_cmd(event):
        thing = event.pattern_match.group(1) or "This"
        r = random.randint(1, 10)
        await reply_card(uclient, event, fun_card("⭐ RATING", f"Subject → {thing}\nScore → {r}/10"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.luck$"))
    async def luck_cmd(event):
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🍀 LUCK METER", f"Luck Today → {p}%"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.predict$"))
    async def predict_cmd(event):
        outcomes = ["Sab sahi hoga!", "Chances kam hain.", "Bilkul pakka!", "Thoda wait karo."]
        await reply_card(uclient, event, fun_card("🔮 PREDICTION", random.choice(outcomes)))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.8ball(?: (.+))?$"))
    async def eightball_cmd(event):
        q = event.pattern_match.group(1) or "Question"
        ans = ["Yes definitely.", "No way.", "Ask again later.", "Outlook good.", "Doubtful."]
        await reply_card(uclient, event, fun_card("🎱 MAGIC 8-BALL", f"Q: {q}\nA: {random.choice(ans)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.choose(?: (.+))?$"))
    async def choose_cmd(event):
        raw = event.pattern_match.group(1)
        if not raw or "|" not in raw:
            await reply_card(uclient, event, "⚠️ Usage: `.choose Option A | Option B | Option C`")
            return
        options = [x.strip() for x in raw.split("|") if x.strip()]
        await reply_card(uclient, event, fun_card("🎯 DECISION MAKER", f"Selected → **{random.choice(options)}**"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dice$"))
    async def dice_cmd(event):
        await reply_card(uclient, event, fun_card("🎲 DICE ROLL", f"Result → {random.randint(1, 6)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.flip$"))
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.coin$"))
    async def coin_cmd(event):
        await reply_card(uclient, event, fun_card("🪙 COIN TOSS", f"Outcome → {random.choice(['🟡 HEADS', '⚪ TAILS'])}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rps(?: (.+))?$"))
    async def rps_cmd(event):
        user_choice = event.pattern_match.group(1)
        bot_choice = random.choice(["Rock 🪨", "Paper 📄", "Scissors ✂️"])
        body = f"My Pick → {bot_choice}" + (f"\nYour Pick → {user_choice}" if user_choice else "")
        await reply_card(uclient, event, fun_card("✂️ ROCK PAPER SCISSORS", body))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.slot$"))
    async def slot_cmd(event):
        emojis = ["🍒", "🍋", "🍇", "🍉", "⭐", "🔔", "7️⃣"]
        line = [random.choice(emojis) for _ in range(3)]
        win = "🎉 JACKPOT!" if line[0] == line[1] == line[2] else "Try again!"
        await reply_card(uclient, event, fun_card("🎰 SLOT MACHINE", f"[ {' | '.join(line)} ]\n\n{win}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.number$"))
    async def number_cmd(event):
        await reply_card(uclient, event, fun_card("🔢 LUCKY NUMBER", f"Number → {random.randint(1, 100)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.guess$"))
    async def guess_cmd(event):
        await reply_card(uclient, event, fun_card("❓ GUESS CHALLENGE", f"Guess between 1 and 10! Answer: {random.randint(1, 10)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.trivia$"))
    async def trivia_cmd(event):
        trivias = [
            ("Which planet is closest to the sun?", "Mercury"),
            ("What is the capital of Japan?", "Tokyo"),
            ("How many continents are there?", "7"),
        ]
        q, a = random.choice(trivias)
        await reply_card(uclient, event, fun_card("💡 MINI TRIVIA", f"Question: {q}\nAnswer: {a}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.animal$"))
    async def animal_cmd(event):
        animals = ["🦁 Lion", "🐯 Tiger", "🐼 Panda", "🦅 Eagle", "🐺 Wolf", "🦊 Fox"]
        await reply_card(uclient, event, fun_card("🐾 RANDOM ANIMAL", f"Spawned: {random.choice(animals)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pick$"))
    async def pick_cmd(event):
        colors = ["🔴 Crimson Red", "🔵 Sapphire Blue", "🟢 Emerald Green", "🟡 Golden Yellow", "🟣 Royal Purple"]
        await reply_card(uclient, event, fun_card("🎨 COLOR PICKER", f"Picked: {random.choice(colors)}"))

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.coffee$"))
    async def coffee_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        steps = [
            "Heating water...",
            "Grinding beans...",
            "Brewing ▰▱▱▱▱",
            "Brewing ▰▰▰▱▱",
            "Brewing ▰▰▰▰▰",
            "☕ Coffee ready! Enjoy 😎",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n☕ COFFEE MACHINE\n\n{steps[0]}\n\n{footer()}", collapsed=False)
        for s in steps[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"{header()}\n\n☕ COFFEE MACHINE\n\n{s}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.launch$"))
    async def launch_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["🚀 3...", "🚀 2...", "🚀 1...", "🔥 IGNITION!", "🌌 IN ORBIT!"]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n🚀 ROCKET LAUNCH\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.4)
            await edit_card(msg, f"{header()}\n\n🚀 ROCKET LAUNCH\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.scan$"))
    async def scan_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["Analyzing cache...", "Checking network sockets...", "Verifying database link...", "✅ System Clean & Optimal!"]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n🛡️ SAFE DIAGNOSTIC\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"{header()}\n\n🛡️ SAFE DIAGNOSTIC\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.matrix$"))
    async def matrix_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["01000001 01010011", "01001000 01001001", "01010011 01001000", "🟢 MATRIX STABLE"]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n💻 MATRIX\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.3)
            await edit_card(msg, f"{header()}\n\n💻 MATRIX\n\n{f}\n\n{footer()}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.hack$"))
    async def hack_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Bypassing mainframe proxy...",
            "Decrypting RSA 4096-bit keys...",
            "Overriding local permissions...",
            "Access Granted: Master Level 🔑",
        ]
        msg = await send_card(uclient, event.chat_id, f"{header()}\n\n💻 TERMINAL EMULATION\n\n{frames[0]}\n\n{footer()}", collapsed=False)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"{header()}\n\n💻 TERMINAL EMULATION\n\n{f}\n\n{footer()}", collapsed=False)


# ============================================================
#         RENDER HTTP WEB SERVER (PORT BINDING)
# ============================================================

async def handle_ping(request):
    return web.Response(text="ASHISH X HOSTER • ONLINE", status=200)

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"Web server bound to port {port} for Render Web Service.")
    except OSError:
        print("Port 8080 already in use, skipping port bind.")


# ============================================================
#               SYSTEM STARTUP & AUTO-RELOAD
# ============================================================

async def load_saved_sessions():
    cursor = sessions_col.find({})
    count = 0
    async for row in cursor:
        uid = row["user_id"]
        s_str = row["session"]
        try:
            cl = TelegramClient(StringSession(s_str), API_ID, API_HASH)
            await cl.connect()
            if await cl.is_user_authorized():
                register_userbot_handlers(cl, uid)
                active_clients[uid] = cl
                asyncio.create_task(cl.run_until_disconnected())
                count += 1
            else:
                await sessions_col.delete_one({"user_id": uid})
        except Exception as e:
            print(f"[Error loading user {uid}]: {e}")
    print(f"Loaded {count} active userbot clients from MongoDB.")

async def main():
    print("=" * 50)
    print("      ASHISH X HOSTER MULTI-USERBOT V5 (RENDER)")
    print("=" * 50)

    await start_web_server()
    await bot.start(bot_token=BOT_TOKEN)
    print("Main Telegram Bot is ONLINE.")

    await load_saved_sessions()
    print("All subsystems running perfectly.")

    asyncio.create_task(log_to_channel(f"⚡ **{BRAND} Server Re-deployed & Online!**"))

    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
