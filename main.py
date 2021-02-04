from aiogram import Bot, Dispatcher, executor, types
from db import DataBase
import settings

# Initialize global vars
db = DataBase("db.db")
bot = Bot(token=settings.bot_api_token)
dispatcher = Dispatcher(bot)


# Inline keyboard for choosing language
langs_panel = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Русский", callback_data="rus_lang"),
                                               types.InlineKeyboardButton("English", callback_data="eng_lang"))

# Keyboard for choosing currency
currency_panel = types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton("$"),
                                                                     types.KeyboardButton("€"),
                                                                     types.KeyboardButton("£"))

# (For admin) Accept user payment
accept_pay_panel = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Pay", callback_data="pay_accept"),
                                                    types.InlineKeyboardButton("Cancel", callback_data="pay_cancel"))


# Welcome
@dispatcher.message_handler(commands=["start"])
async def welcome(message: types.Message):
    user_id = message.from_user.id
    if user_id != settings.admin_id:
        if db.user_exists(user_id):
            await message.answer("Hello again!")
        else:
            await message.answer("Welcome")
            db.new_user(user_id)
            msg = await message.answer("Please select a language", reply_markup=langs_panel)
            db.cursor.execute(f"UPDATE users SET lang_msg_id = {msg.message_id} WHERE tg_id = {user_id}")
            db.db.commit()


# Command /help
@dispatcher.message_handler(commands=["help"])
async def helper(message: types.Message):
    user_id = message.from_user.id
    if user_id == settings.admin_id:
        await message.answer(settings.admin_help)
    else:
        await message.answer(settings.user_help_eng)


# Get balance
@dispatcher.message_handler(commands=["balance"])
async def return_balance(message: types.Message):
    user_id = message.from_user.id
    if user_id != settings.admin_id:
        if db.user_exists(user_id) and db.get_state(user_id) == 0:
            await message.answer(f"{db.get_balance(user_id)}{db.get_currency(user_id)}")


# Commands to work with payment's
@dispatcher.message_handler(commands=["replen", "pay"])
async def payment_work(message: types.Message):
    user_id = message.from_user.id
    if "/pay" in message.text:
        db.change_state(user_id, 7)
        await message.answer("Введите сумму вывода" if db.get_lang(user_id) == "rus" else "Enter withdrawal amount")
    elif "/replen" in message.text:
        db.change_state(user_id, 8)
        await message.answer("Введите сумму пополнения" if db.get_lang(user_id) == "rus" else "Enter the top-up amount")


# Admin commands
@dispatcher.message_handler(commands=["users_list", "edit"])
async def admin_panel(message: types.Message):
    if message.from_user.id == settings.admin_id:
        divided_msg = message.text.split(" ")
        if "/users_list" in message.text:
            users_list = "tg_id|full_name|state|birthday|residence_place|study_work|balance|lang\n"
            for user in db.get_users():
                users_list += f"<b>{user[0]}</b>|{user[1]}|{user[2]}|{user[3]}|{user[4]}|{user[5]}|{user[6]}{user[7]}|{user[8]}\n"
            await message.answer(users_list, parse_mode=types.ParseMode.HTML)
        elif "/edit" in message.text and divided_msg[1].isdigit():
            insert_data = f"\"{divided_msg[3]}\"" if divided_msg[2] != "balance" else f"{divided_msg[3]}"
            db.cursor.execute(f"UPDATE users SET {divided_msg[2]} = " + insert_data + f" WHERE tg_id = {divided_msg[1]}")
            db.db.commit()
    else:
        await message.answer("Вы не являетесь админом!\nYou are not an admin!")


# Main text handler
@dispatcher.message_handler(content_types=["text"])
async def text_answering(message: types.Message):
    user_id = message.from_user.id
    if db.get_state(user_id) != 0:
        # Fill data
        if db.get_state(user_id) == 2 and message.text.count(" ") >= 2:
            db.set_full_name(user_id, message.text)
            await message.answer("Отправьте мне своё место жительства" if db.get_lang(user_id) == "rus" else "Send me your place of residence")
            db.change_state(user_id, 3)
        elif db.get_state(user_id) == 3 and len(message.text) >= 3:
            db.set_place_of_residence(user_id, message.text)
            await message.answer("Отправьте мне своё место работы/учёбы" if db.get_lang(user_id) == "rus" else "Send me your place of work / study")
            db.change_state(user_id, 4)
        elif db.get_state(user_id) == 4 and len(message.text) >= 3:
            db.set_place_of_work(user_id, message.text)
            await message.answer("Отправьте мне дату своего рождения в формате день/месяц/год" if db.get_lang(user_id) == "rus" else "Send me your date of birth in day/month/year format")
            db.change_state(user_id, 5)
        elif db.get_state(user_id) == 5 and message.text.count(" ") == 0 and message.text.count("/") >= 2:
            db.set_birthday_date(user_id, message.text)
            await message.answer("Выберите валюту:" if db.get_lang(user_id) == "rus" else "Select currency:", reply_markup=currency_panel)
            db.change_state(user_id, 6)
        elif db.get_state(user_id) == 6 and message.text in ["$", "€", "£"]:
            db.set_currency(user_id, message.text)
            await message.answer("Данные успешно заполнены!" if db.get_lang(user_id) == "rus" else "The data has been filled in successfully!",
                                 reply_markup=types.ReplyKeyboardRemove())
            db.change_state(user_id, 0)
    else:
        await message.answer("Все данные заполнены" if db.get_lang(user_id) == "rus" else "All data is filled")
    if db.get_state(user_id) == 7:
        if message.text.isdigit():
            msg = await bot.send_message(settings.admin_id, f"{user_id} wants to withdraw {message.text}{db.get_currency(user_id)}", reply_markup=accept_pay_panel)
            db.cursor.execute(f"UPDATE users SET admin_pay_msg_id = {msg.message_id} WHERE tg_id = {message.from_user.id}")
            db.change_state(user_id, 0)
        else:
            await message.answer("Сообщение должно быть числом!" if db.get_lang(user_id) == "rus" else "The message must be a number!")
    elif db.get_state(user_id) == 8:
        if message.text.isdigit():
            db.add_balance(user_id, int(message.text))
            db.change_state(user_id, 0)
        else:
            await message.answer("Сообщение должно быть числом!" if db.get_lang(user_id) == "rus" else "The message must be a number!")

# ======= SELECT LANG CALLBACK HANDLE =======


# Choosed English language
@dispatcher.callback_query_handler(text="eng_lang")
async def eng_ans(message: types.Message):
    user_id = message.from_user.id
    db.cursor.execute(f"SELECT * FROM users WHERE tg_id = {user_id}")
    msg_id = db.cursor.fetchone()[9]
    await bot.delete_message(user_id, msg_id)
    await bot.send_message(user_id, "Selected english language")
    db.set_lang(user_id, "eng")
    db.change_state(user_id, 2)
    await bot.send_message(user_id, "Send your full name in the format \"LastName FirstName Patronymic\"")


# Choosed Russian language
@dispatcher.callback_query_handler(text="rus_lang")
async def eng_ans(message: types.Message):
    user_id = message.from_user.id
    db.cursor.execute(f"SELECT * FROM users WHERE tg_id = {user_id}")
    msg_id = db.cursor.fetchone()[9]
    await bot.delete_message(user_id, msg_id)
    await bot.send_message(user_id, "Выбран Русский язык")
    db.set_lang(user_id, "rus")
    db.change_state(user_id, 2)
    await bot.send_message(user_id, "Отправьте своё ФИО в формате \"Фамилия Имя Отчество\"")

# (Admin) accept user withdraw
@dispatcher.callback_query_handler(text="pay_accept")
async def accept_pay(query: types.CallbackQuery):
    message = query.message
    who_want_id = message.text.split(" ")[0]
    # db.cursor.execute(f"SELECT * FROM users WHERE tg_id = {who_want_id}")
    # print(db.cursor.fetchone()[-3])
    # msg_id = db.cursor.fetchone()[10]
    db.cursor.execute(f"UPDATE users SET balance = balance - {message.text.split('wants to withdraw ')[1].replace('$', '').replace('€', '').replace('£', '')}")
    db.db.commit()
    await bot.send_message(int(who_want_id), f"Payed {message.text.split(' ')[-1]}")
    # await bot.delete_message(settings.admin_id, msg_id)


# ===========================================


# Start bot
if __name__ == '__main__':
    executor.start_polling(dispatcher)
    exit()
