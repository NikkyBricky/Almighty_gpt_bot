import logging
import requests
from config import basic_url, lang, LOGS, GRAMMAR_API_KEY

logging.basicConfig(filename=LOGS,
                    level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
                    filemode="w",
                    force=True)


# Для использования нужен токен, который можно получить бесплатно,
# зарегистрировавшись на сайте (https://textgears.com/ru/signup?shutupandgiveme=thekey)
def check_grammar(text):
    params = {
        "key": GRAMMAR_API_KEY,  # ключ для взаимодействия с API
        "text": text,
        "language": lang,  # язык, на котором написан текст для проверки
        }

    result = requests.get(
        url=basic_url,
        params=params
    ).json()

    if result["status"]:  # Если не возникло ошибки с апи-ключом или чем-то еще. В ином случае отправляем тот же текст
        text = text.split()  # Со списком проще взаимодействовать
        errors_list = result["response"]["errors"]

        for error in errors_list:
            bad_words = error["bad"].split()  # Список слов, в которых замечена ошибка
            correct_words = error["better"][0].split()  # Список слов, с исправленными ошибками

            for i, word in enumerate(text):  # Проходимся по словам в тексте
                if correct_words:
                    if word in bad_words:  # Если слово из текста есть в списке слов с ошибками
                        text.pop(i)  # Удаляем это слово
                        bad_word_index = bad_words.index(word)  # Находим его индекс в списке слов с ошибками

                    # Берем из списка correct_words исправленное слово по индексу и добавляем его в текст в нужном месте
                        text.insert(i, correct_words[bad_word_index])

                        # Удаляем из обоих списков проверенное слово
                        bad_words.pop(bad_word_index)

                        if "-" in correct_words[bad_word_index]:
                            bad_words.pop(bad_word_index)

                        correct_words.pop(bad_word_index)
        text = ' '.join(text)  # преобразовываем получившийся список корректных слов в строку
    return text


#  На самом деле у Яндекса есть такая функция в SpeechKit, но не для синхронной версии v1, которую используем мы.
