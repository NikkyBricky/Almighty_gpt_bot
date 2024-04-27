import logging
import time

import telebot
from keyboards import make_inline_keyboard, make_reply_keyboard
from config import (BOT_TOKEN, ADMIN_ID, LOGS, COUNT_LAST_MSG, CONTENT_TYPES, BOT_NAME, BOT_DESCRIPTION, COMMANDS,
                    USE_GRAMMAR_CHECK, MAX_USER_GPT_TOKENS, MAX_USER_TTS_SYMBOLS, MAX_USER_STT_BLOCKS, ABOUT_BOT,
                    IS_PROCESSING_ANSWER_MSG, START_MSG)
from database import (create_database, add_message, select_n_last_messages, find_user_data, add_user_to_database,
                      update_user_data, count_all_limits)
from validators import is_gpt_token_limit, is_stt_block_limit, is_tts_symbol_limit, check_number_of_users
from yandex_gpt import ask_gpt
from speech_kit import speech_to_text, text_to_speech
from grammar_check import check_grammar

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS,
                    level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
                    filemode="w",
                    force=True)


create_database()

bot = telebot.TeleBot(token=BOT_TOKEN)


# обрабатываем команду /debug - отправляем файл с логами
@bot.message_handler(commands=['debug'])
def debug(message):
    user_id = message.from_user.id

    is_processing_answer = check_processing_answer(message, user_id)

    if is_processing_answer:
        return

    if user_id == int(ADMIN_ID):
        check_user_exists(user_id)

        with open(LOGS, "rb") as f:
            bot.send_document(message.chat.id, f)

    else:
        bot.send_message(message.chat.id, "В доступе отказано!")


# Данная функция есть везде, где используется таблица users,
# т.к. в случае, если у пользователя уже есть чат с ботом, а база данных удалена, могут возникнуть ошибки.
def check_user_exists(user_id):
    is_user = find_user_data(user_id)

    if not is_user:  # Если пользователя нет в базе данных
        add_user_to_database(user_id)


def check_processing_answer(message, user_id):
    if find_user_data(user_id)["processing_answer"]:
        bot.reply_to(message, text=IS_PROCESSING_ANSWER_MSG)
        return True


@bot.message_handler(commands=["start"])
def get_started(message):
    user_id = message.from_user.id

    # Проверка на максимальное количество пользователей
    status_check_users, error_message = check_number_of_users(user_id)

    if not status_check_users:
        bot.send_message(message.chat.id, error_message)
        return

    check_user_exists(user_id)

    is_processing_answer = check_processing_answer(message, user_id)

    if is_processing_answer:
        return

    keyboard = make_reply_keyboard("main_menu")
    bot.send_message(message.chat.id, text=START_MSG, reply_markup=keyboard)


@bot.message_handler(commands=["help"])
def about_bot(message):
    bot.send_message(message.chat.id, text=ABOUT_BOT, parse_mode="html")


def process_stt(message, user_id):
    # Проверка на доступность аудио-блоков
    stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)

    if error_message:
        bot.send_message(message.chat.id, error_message, parse_mode="html")
        return

    # Обработка голосового сообщения
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)

    update_user_data(user_id, column_name="processing_answer", value=1)

    status_stt, stt_text = speech_to_text(file)

    update_user_data(user_id, column_name="processing_answer", value=0)

    if not status_stt:
        bot.send_message(message.chat.id, stt_text)
        return

    if USE_GRAMMAR_CHECK:
        stt_text = check_grammar(stt_text)

    # Запись в БД
    add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

    return stt_text


def process_tts(message, user_id, text, total_gpt_tokens, testing=False):
    # Проверка на лимит символов для SpeechKit
    tts_symbols, error_message = is_tts_symbol_limit(user_id, text)

    # Запись ответа GPT в БД
    add_message(user_id=user_id, full_message=[text, 'assistant', total_gpt_tokens, tts_symbols, 0])

    if error_message:
        bot.send_message(message.chat.id, error_message)
        return

    # Преобразование ответа в аудио и отправка
    update_user_data(user_id, column_name="processing_answer", value=1)

    status_tts, voice_response = text_to_speech(text)

    update_user_data(user_id, column_name="processing_answer", value=0)

    if status_tts:
        gpt_voice_answer = bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)

        user_data = find_user_data(user_id)

        if not testing and user_data["recognise_voice_answer"]:
            time.sleep(2)

            bot.send_message(
                chat_id=message.chat.id,
                reply_to_message_id=gpt_voice_answer.message_id,
                text=f"<b>Расшифровка ответа нейросети</b>\n\n{text}",
                parse_mode="html")

    else:
        bot.send_message(user_id, text, reply_to_message_id=message.id)


@bot.message_handler(content_types=['text'], func=lambda message: False not in
                     [symbol not in message.text for symbol in ["/", "📊Статистика", "⚙️Параметры"]])
@bot.message_handler(content_types=['voice'])
def talk_with_gpt(message):
    user_id = message.from_user.id
    try:
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)

        if not status_check_users:
            bot.send_message(message.chat.id, error_message)
            return

        check_user_exists(user_id)

        # Проверка на то, что нейросеть уже отвечает на вопрос пользователя
        is_processing_answer = check_processing_answer(message, user_id)

        if is_processing_answer:
            return

        user_data = find_user_data(user_id)  # получаем данные пользователя (не о сообщениях) из таблицы users

        if message.text:
            text = message.text

            if USE_GRAMMAR_CHECK:
                text = check_grammar(text)
            # добавляем сообщение пользователя и его роль в базу данных
            full_user_message = [text, 'user', 0, 0, 0]
            add_message(user_id=user_id, full_message=full_user_message)

            configure_stmt = user_data["text_to"]  # пригодится ниже

        else:
            text = process_stt(message, user_id)
            if not text:
                return

            if user_data["recognise_voice_answer"]:  # если нужно показывать распознанный текст пользователя
                bot.send_message(message.chat.id, f"<b>Распознанный текст</b>\n\n{text}", parse_mode="html")

            configure_stmt = user_data["speech_to"]  # пригодится ниже
        # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)

        if error_message:
            bot.send_message(message.chat.id, error_message)
            return

        update_user_data(user_id, column_name="processing_answer", value=1)

        wait_msg = bot.send_message(message.chat.id, "Отправил ваш запрос нейросети. Ожидайте...")

        # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)

        update_user_data(user_id, column_name="processing_answer", value=0)

        bot.delete_message(message.chat.id, message_id=wait_msg.message_id)

        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return

        total_gpt_tokens += tokens_in_answer

        if configure_stmt == "speech":
            process_tts(message, user_id, answer_gpt, total_gpt_tokens)
            return

        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(message.chat.id, answer_gpt,
                         reply_to_message_id=message.id, parse_mode="Markdown")  # отвечаем пользователю текстом

    except Exception as e:
        logging.error(e)
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")


@bot.message_handler(commands=['settings'])
@bot.message_handler(content_types=['text'], func=lambda message: message.text == "⚙️Параметры")
def settings(message):
    c_id = message.chat.id

    user_id = message.from_user.id

    # Проверка на максимальное количество пользователей
    status_check_users, error_message = check_number_of_users(user_id)

    if not status_check_users:
        return

    check_user_exists(user_id)

    # Проверка на то, что нейросеть уже отвечает на вопрос пользователя
    is_processing_answer = check_processing_answer(message, user_id)

    if is_processing_answer:
        return

    user_data = find_user_data(user_id)
    previous_msg = user_data['settings_msg_id']

    if message.text.lower() == "вернуться в главное меню":
        keyboard = make_reply_keyboard("main_menu")

        user_text_configuration = user_data["text_to"]
        user_speech_configuration = user_data["speech_to"]

        if user_text_configuration == "text":
            user_text_configuration = "Текстовый"

        elif user_text_configuration == "speech":
            user_text_configuration = "Голосовой"

        if user_speech_configuration == "text":
            user_speech_configuration = "Текстовый"

        elif user_speech_configuration == "speech":
            user_speech_configuration = "Голосовой"

        recognise_voice_answers = user_data["recognise_voice_answer"]

        if recognise_voice_answers:
            recognise_voice_answers = "включена"

        else:
            recognise_voice_answers = "выключена"

        bot.send_message(c_id, "Теперь можете начать диалог с нейросетью, "
                               "просто отправив текстовое или голосовое сообщение.\n\n"
                               "Ваша конфигурация на данный момент:\n\n"
                               "<b>Текстовые</b> запросы → " + f"<b>{user_text_configuration}</b>" + " ответ\n"
                               "<b>Голосовые</b> запросы → " + f"<b>{user_speech_configuration}</b>" + " ответ\n\n"
                               f"Расшифровка голосовых сообщений: <b>{recognise_voice_answers}</b>",
                         reply_markup=keyboard, parse_mode="html")

        for i in range(0, 3):  # удаляем предыдущие сообщения, связанные с параметрами во избежание ошибок
            m_id = previous_msg - i
            bot.delete_message(chat_id=c_id, message_id=m_id)
            update_user_data(user_id, "settings_msg_id", -1)

        return

# добавил два сообщения для настроек, так как у одного и того же нельзя менять reply и inline клавиатуры одновременно
    if message.text.lower() in ["/settings", "⚙️параметры"]:
        keyboard = make_reply_keyboard("back_to_main_menu")

        bot.send_message(c_id, "Перехожу в режим настроек...", reply_markup=keyboard)
        time.sleep(0.5)

        keyboard = make_inline_keyboard('settings', user_id)  # меняем inline клавиатуру

        msg = bot.send_message(chat_id=c_id, text="Какой параметр вы хотите изменить?", reply_markup=keyboard)

        if previous_msg != -1:  # удаляем предыдущие сообщения, связанные с параметрами во избежание ошибок
            for i in range(0, 3):
                m_id = previous_msg - i
                bot.delete_message(chat_id=c_id, message_id=m_id)

        update_user_data(user_id, "settings_msg_id", msg.message_id)

    else:
        bot.delete_message(chat_id=c_id, message_id=message.message_id)

    bot.register_next_step_handler(message, settings)


@bot.callback_query_handler(func=lambda call: True)
def process_calls(call):
    c_id = call.message.chat.id
    m_id = call.message.message_id
    user_id = call.from_user.id

    # Проверка на то, что нейросеть уже отвечает на вопрос пользователя
    is_processing_answer = check_processing_answer(call.message, user_id)

    if is_processing_answer:
        return

    bot.answer_callback_query(callback_query_id=call.id)  # убираем долгую загрузку кнопки

    data = call.data
    text = "Какой параметр вы хотите изменить?"

    if data == "recognise_voice_answer on":
        update_user_data(user_id, "recognise_voice_answer", value=1)

    elif data == "recognise_voice_answer off":
        update_user_data(user_id, "recognise_voice_answer", value=0)

    elif data == "text_to" or "text_conf" in data:
        text = "Каким вы хотите видеть ответ нейросети на текстовый запрос:"

        if "text_conf" in data:
            data = data.split()
            update_user_data(user_id, "text_to", value=data[1])

    elif data == "speech_to" or "speech_conf" in data:
        text = "Каким вы хотите видеть ответ нейросети на голосовой запрос:"

        if "speech_conf" in data:
            data = data.split()
            update_user_data(user_id, "speech_to", value=data[1])

    if data != "empty_button":
        keyboard = make_inline_keyboard(data, user_id=user_id)
        try:
            bot.edit_message_text(chat_id=c_id, message_id=m_id, text=text, reply_markup=keyboard)
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(e)


@bot.message_handler(commands=['stats'])
@bot.message_handler(content_types=['text'], func=lambda message: message.text == "📊Статистика")
def show_statistics(message):
    user_id = message.from_user.id

    # Проверка на максимальное количество пользователей
    status_check_users, error_message = check_number_of_users(user_id)

    if not status_check_users:
        return

    check_user_exists(user_id)

    # Проверка на то, что нейросеть уже отвечает на вопрос пользователя
    is_processing_answer = check_processing_answer(message, user_id)

    if is_processing_answer:
        return

    spent_gpt_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)[1]
    speechkit_limits = []

    for limit_type in ["stt_blocks", "tts_symbols"]:

        current_amount = count_all_limits(user_id, limit_type)

        speechkit_limits.append(current_amount)

    spent_stt_blocks, spent_tts_symbols = speechkit_limits

    bot.send_message(message.chat.id, "<b>Ваша статистика</b>\n\n"
                                      "<b>🤖Токены для GPT🤖</b>\n"
                                      f"<b>Лимит</b>: {MAX_USER_GPT_TOKENS}\n"
                                      f"<b>Потрачено</b>: {spent_gpt_tokens}\n"
                                      f"<b>Осталось</b>: {MAX_USER_GPT_TOKENS - spent_gpt_tokens}\n\n"
                                      "<b>🎧Символы для синтеза речи🎧</b>\n"
                                      f"<b>Лимит</b>: {MAX_USER_TTS_SYMBOLS}\n"
                                      f"<b>Потрачено</b>: {spent_tts_symbols}\n"
                                      f"<b>Осталось</b>: {MAX_USER_TTS_SYMBOLS - spent_tts_symbols}\n\n"
                                      "<b>🎤Аудио-блоки для распознавания речи🎤</b>\n"
                                      f"<b>Лимит</b>: {MAX_USER_STT_BLOCKS}\n"
                                      f"<b>Потрачено</b>: {spent_stt_blocks}\n"
                                      f"<b>Осталось</b>: {MAX_USER_STT_BLOCKS - spent_stt_blocks}",
                     parse_mode="html")


@bot.message_handler(commands=['stt', 'tts'])
def check_speechkit(message):
    user_id = message.from_user.id

    if user_id == int(ADMIN_ID):
        check_user_exists(user_id)

        is_processing_answer = check_processing_answer(message, user_id)

        if is_processing_answer:
            return

        command = message.text

        keyboard = make_reply_keyboard("exit_test")

        if command == "/stt":
            bot.send_message(message.chat.id, "Проверка режима распознавания речи. Отправьте голосовое сообщение.",
                             reply_markup=keyboard)
            bot.register_next_step_handler(message, send_test_stt, user_id)

        else:
            bot.send_message(message.chat.id, "Проверка режима синтеза речи. Отправьте текстовое сообщение.",
                             reply_markup=keyboard)
            bot.register_next_step_handler(message, send_test_tts, user_id)

    else:
        bot.send_message(message.chat.id, "В доступе отказано!")


def send_test_stt(message, user_id):
    if message.text and message.text == "Выход":
        bot.send_message(message.chat.id, "Перехожу в обычный режим.",
                         reply_markup=make_reply_keyboard("main_menu"))
        return

    elif message.voice:
        stt_text = process_stt(message, user_id)

        if not stt_text:
            return

        bot.send_message(message.chat.id, f"<b>Распознанный текст</b>\n\n{stt_text}", parse_mode="html")

        bot.send_message(message.chat.id, "Перехожу в обычный режим.",
                         reply_markup=make_reply_keyboard("main_menu"))

    else:
        bot.send_message(message.chat.id, "Кажется, вы отправили не голосовое сообщение. Попробуйте еще раз.")
        bot.register_next_step_handler(message, send_test_stt, user_id)


def send_test_tts(message, user_id):
    if message.text:
        if message.text == "Выход":
            bot.send_message(message.chat.id, "Перехожу в обычный режим.",
                             reply_markup=make_reply_keyboard("main_menu"))
            return

        process_tts(message, user_id, message.text, 0, True)

        bot.send_message(message.chat.id, "Перехожу в обычный режим.",
                         reply_markup=make_reply_keyboard("main_menu"))

    else:
        bot.send_message(message.chat.id, "Кажется, вы отправили не текстовое сообщение. Попробуйте еще раз.")
        bot.register_next_step_handler(message, send_test_tts, user_id)


@bot.message_handler(content_types=CONTENT_TYPES)
def any_msg(message):
    user_id = message.from_user.id

    is_processing_answer = check_processing_answer(message, user_id)

    if is_processing_answer:
        return

    else:

        bot.send_message(message.chat.id, 'Отлично сказано! Если хотите задать вопрос, то отправьте текстовое или '
                                          'голосовое сообщение.')


if __name__ == "__main__":
    try:  # Как я понял, эти методы нельзя слишком часто вызывать. В нашем случае, вызов происходит при перезапуске бота
        bot.set_my_commands(COMMANDS)
        bot.set_my_name(BOT_NAME)
        bot.set_my_description(BOT_DESCRIPTION)

    except telebot.apihelper.ApiTelegramException:
        pass
    logging.info("BOT: бот запущен")
    bot.infinity_polling()
