from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

from database import find_user_data


def make_reply_keyboard(params):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if params == "main_menu":
        keyboard.add("⚙️Параметры", "📊Статистика")

    elif params == "back_to_main_menu":
        keyboard.add("Вернуться в главное меню")

    elif params == "exit_test":
        keyboard.add("Выход")

    return keyboard


def make_inline_keyboard(data, user_id):
    user_data = find_user_data(user_id)

    keyboard = InlineKeyboardMarkup(row_width=1)

    place_button = InlineKeyboardButton(text="―", callback_data="empty_button")

    if data in ['settings', 'go_back'] or "recognise_voice_answer" in data:
        btn1 = InlineKeyboardButton(text="💭Параметры текстового запроса💭", callback_data="text_to")
        btn2 = InlineKeyboardButton(text="🎤Параметры голосового запроса🎤", callback_data="speech_to")

        if user_data["recognise_voice_answer"]:
            btn_3 = InlineKeyboardButton(text="Расшифровка голосовых сообщений ✅",
                                         callback_data="recognise_voice_answer off")
        else:
            btn_3 = InlineKeyboardButton(text="Расшифровка голосовых сообщений ❌",
                                         callback_data="recognise_voice_answer on")

        keyboard.add(btn1, btn2, place_button, btn_3)

    if data in ["text_to", "speech_to"] or "text_conf" in data or "speech_conf" in data:
        btn1_text = "📜Текст"
        btn2_text = "🗣️Речь"

        back_btn = InlineKeyboardButton(text="Вернуться назад", callback_data="go_back")

        if data == "text_to" or "text_conf" in data:
            general_configuration = "text_conf"
            current_configuration = user_data["text_to"]

        else:
            general_configuration = "speech_conf"
            current_configuration = user_data["speech_to"]

        if current_configuration == "text":
            btn1_text += "          ✅"

        elif current_configuration == "speech":
            btn2_text += "          ✅"

        btn1 = InlineKeyboardButton(text=btn1_text, callback_data=general_configuration + " text")
        btn2 = InlineKeyboardButton(text=btn2_text, callback_data=general_configuration + " speech")

        keyboard.add(btn1, btn2, place_button, back_btn)
    return keyboard
