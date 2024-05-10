import logging

import requests
from config import FOLDER_ID, LOGS
from make_gpt_token import get_token

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS,
                    level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
                    filemode="w",
                    force=True)

IAM_TOKEN = get_token()


def speech_to_text(data):
    # Указываем параметры запроса
    params = "&".join([
        "topic=general",  # используем основную версию модели
        f"folderId={FOLDER_ID}",
        "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
    ])

    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }

    # Выполняем запрос
    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        logging.info("SPEECHKIT/STT: голосовое сообщение успешно распознано")
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        logging.error(f"SPEECHKIT/STT: {decoded_data['error_message']}")
        return False, "При запросе в SpeechKit возникла ошибка"


def text_to_speech(text: str):

    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }
    data = {
        'text': text,  # текст, который нужно преобразовать в голосовое сообщение
        'voice': "marina",
        'speed': 0.9,
        'folderId': FOLDER_ID,
    }
    # Выполняем запрос
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)

    if response.status_code == 200:
        logging.info("SPEECHKIT/TTS: текст успешно озвучен")
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        logging.error(f"SPEECHKIT/TTS: {response.json()['error_message']}")
        return False, "При запросе к SpeechKit произошла ошибка"
