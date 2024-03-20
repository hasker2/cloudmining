import sqlite3
from aiogram.types import *
from aiogram.utils.keyboard import *
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, Text, CommandObject
from aiogram import Bot
import sys
import datetime
sys.path.append('..')
from databaseclass import *
from aiogram.utils.deep_linking import create_start_link
import aiohttp
import json

bot = Bot(token=token, parse_mode="HTML")
router = Router()

class Addr_set(StatesGroup):
    addr = State()


@router.message(Command(commands=['start']))
async def greets(message: Message, command: CommandObject):
    user = UserDb(message)
    kb = [
        [
            KeyboardButton(text="Account"),
        ],
        [
            KeyboardButton(text="🔋Mining")
        ],
        [
            KeyboardButton(text="Referals")
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    await bot.send_message(message.chat.id, f'⚡', reply_markup=keyboard)
    await account(message)
    if_new = await user.add_user()
    try:
        if command.args and if_new:
            if (command.args.isdigit()):
                await UserDb.increase(int(command.args))
                await bot.send_message(command.args, "You have got a referee.")
            else:
                await RefDb.increase(command.args)
    except sqlite3.IntegrityError as e:
        pass
    except Exception as e:
        print(e)

@router.message(Text(text="🔋Mining"))
async def mining(message: Message):
    kurs = []
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.coindesk.com/v1/bpi/currentprice/BTC.json') as response:
            kurs = await response.json()
    th = 0.00000006
    refs = await UserDb.get_refs(message.chat.id)
    hashrate = 50+(refs*5)
    data = await UserDb.get_creation_time(message.chat.id)
    balance = count_farm(data)
    active_mining = create_active_products_string(data)
    buttons = [[InlineKeyboardButton(text="📤Withdraw", callback_data="withdraw")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(f"Active miners:\n{active_mining}\nBalance is:\n{balance} BTC\n{round(float(balance)*float(kurs['bpi']['USD']['rate_float']), 2)}$", reply_markup=keyboard)

@router.message(Text(text="Account"))
async def account(message: Message):
    public_key = await UserDb.get_public_key(message.chat.id)
    buttons = [
        [
            InlineKeyboardButton(text="🔗Set Wallet", callback_data="set_wallet"),
        ],
        [
            InlineKeyboardButton(text="📥Deposit", callback_data="deposit"),
            InlineKeyboardButton(text="📤Withdraw", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton(text="⚡Buy power", callback_data="buy_power"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    refs = await UserDb.get_refs(message.chat.id)
    balance = await UserDb.get_balance(message.chat.id)
    addr = ""
    if public_key == None:
        addr = "You have not connected your BTC address yet"
    else:
        addr = f"Connected Address:\n<code>{public_key}</code>"
    await message.answer(f"🆔 <code>{message.chat.id}</code>\n\nDeposit: {balance}$\n\n{addr}", parse_mode="HTML", reply_markup=keyboard)

@router.message(Addr_set.addr)
async def getid(message: Message, state: FSMContext):
    await UserDb.add_wallet(message.chat.id, message.text)
    await message.answer("Your wallet has been successfully added")
    await state.clear()

@router.message(Text(text="Referals"))
async def refs(message: Message):
    refs = await UserDb.get_refs(message.chat.id)
    await message.answer(f"You can 20% of deposit of each friend you invite\n\nYou invited: {refs}\n\nYour referal link: {await create_start_link(bot, str(message.chat.id))}")
