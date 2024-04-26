import logging  # модуль для сбора логов
import math  # математический модуль для округления
# подтягиваем константы из config файла
from config import LOGS, MAX_USERS, MAX_USER_GPT_TOKENS, MAX_AUDIO_DURATION, MAX_USER_STT_BLOCKS, MAX_USER_TTS_SYMBOLS,\
    SYSTEM_PROMPT
# подтягиваем функции для работы с БД
from database import count_users, count_all_limits
# подтягиваем функцию для подсчета токенов в списке сообщений
from yandex_gpt import count_gpt_tokens

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS,
                    level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
                    filemode="w",
                    force=True)


# получаем количество уникальных пользователей, кроме самого пользователя
def check_number_of_users(user_id):
    count = count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


# проверяем, не превысил ли пользователь лимиты на общение с GPT
def is_gpt_token_limit(messages, total_spent_tokens):
    all_tokens = count_gpt_tokens(messages + SYSTEM_PROMPT) + total_spent_tokens
    if all_tokens > MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {MAX_USER_GPT_TOKENS}"
    return all_tokens, ""


# проверяем, не превысил ли пользователь лимиты на преобразование аудио в текст
def is_stt_block_limit(user_id, duration):
    current_stt_blocks = count_all_limits(user_id, "stt_blocks")
    audio_blocks = math.ceil(duration / 15)

    all_blocks = current_stt_blocks + audio_blocks

    if duration > MAX_AUDIO_DURATION:
        return all_blocks, ("Кажется, длительность вашего сообщения <b>превышает лимит в 30 секунд</b>. "
                            "Попробуйте снова, уменьшив длительность голосового сообщения.")

    if all_blocks == MAX_USER_STT_BLOCKS:
        return all_blocks, "Вы достигли лимита аудио-блоков. Опция распознавания текста для вас теперь недоступна."

    return audio_blocks, ""


# проверяем, не превысил ли пользователь лимиты на преобразование текста в аудио
def is_tts_symbol_limit(user_id, text):
    tts_symbols = len(text)
    all_tts_symbols = count_all_limits(user_id, "tts_symbols") + tts_symbols

    if all_tts_symbols >= MAX_USER_TTS_SYMBOLS:
        return all_tts_symbols, ("Вы достигли лимита символов для синтеза речи. "
                                 "Данная опция для вас теперь недоступна.")

    return tts_symbols, ""
