import sqlite3
import logging  # модуль для сбора логов
# подтягиваем константы из config-файла
from config import LOGS, DB_FILE

# настраиваем запись логов в файл
logging.basicConfig(filename=LOGS,
                    level=logging.INFO,
                    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
                    filemode="w",
                    force=True)
path_to_db = DB_FILE  # файл базы данных


def process_query(query, params: None | tuple):
    try:
        # подключаемся к базе данных
        with sqlite3.connect(path_to_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if params:
                if "SELECT" in query:
                    result = cursor.execute(query, params)
                    return result

                cursor.execute(query, params)

            else:
                cursor.execute(query)

    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return


# создаём базу данных и таблицы
def create_database():
    messages_query = ('''
        CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        message TEXT,
        role TEXT,
        total_gpt_tokens INTEGER,
        tts_symbols INTEGER,
        stt_blocks INTEGER)
    ''')

    users_query = ('''
             CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY,
             user_id INTEGER UNIQUE,
             text_to TEXT DEFAULT "text",
             speech_to TEXT DEFAULT "speech",
             recognise_voice_answer INTEGER DEFAULT 1,
             processing_answer INTEGER DEFAULT 0,
             settings_msg_id INTEGER DEFAULT -1);
         ''')

    for query in [messages_query, users_query]:
        process_query(query, None)

    logging.info("DATABASE: База данных создана")  # делаем запись в логах


# добавляем новое сообщение в таблицу messages
def add_message(user_id, full_message):
    # записываем в таблицу новое сообщение
    query = ('''INSERT INTO messages (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks) 
            VALUES (?, ?, ?, ?, ?, ?)''')

    process_query(query, (user_id, *full_message))

    logging.info("DATABASE: сообщение пользователя успешно добавлено в базу данных.")


# считаем количество пользователей помимо самого пользователя
def count_users(user_id):
    # получаем количество пользователей помимо самого пользователя
    query = '''SELECT COUNT(user_id) FROM users WHERE user_id <> ?'''
    count = process_query(query, (user_id,)).fetchone()[0]
    logging.info(f"DATABASE: Количество пользователей успешно посчитано: {count}")
    return count


# Находим данные пользователя в таблице users
def find_user_data(user_id):
    query = '''SELECT * FROM users WHERE user_id = ?;'''

    result = list(process_query(query, (user_id,)))

    if result:
        logging.info(f"DATABASE: Данные пользователя с user_id {user_id} успешно найдены.")

        return result[0]

    logging.error("DATABASE: Не получилось собрать данные пользователя.")
    return result


# Добавляем пользователя в таблицу users
def add_user_to_database(user_id):
    query = '''INSERT INTO users (user_id) VALUES (?);'''

    process_query(query, (user_id,))

    logging.info(f"DATABASE: Пользователь с user_id = {user_id} успешно добавлен в базу данных")


# Обновляем данные пользователя
def update_user_data(user_id, column_name, value):
    query = f'''UPDATE users SET {column_name} = ? WHERE user_id = ?; '''

    process_query(query, (value, user_id))

    logging.info(f"DATABASE: База данных успешно обновлена, таблица: users, колонка: {column_name}, user_id: {user_id}")


# получаем последние <n_last_messages> сообщения
def select_n_last_messages(user_id, n_last_messages=4):
    messages = []  # список с сообщениями
    total_spent_tokens = 0  # количество потраченных токенов за всё время общения

    query = '''SELECT message, role, total_gpt_tokens FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?'''

    # получаем последние <n_last_messages> сообщения для пользователя
    data = process_query(query, (user_id, n_last_messages)).fetchall()

    # проверяем data на наличие хоть какого-то полученного результата запроса
    # и на то, что в результате запроса есть хотя бы одно сообщение - data[0]
    if data and data[0]:
        # формируем список сообщений
        for message in reversed(data):
            messages.append({'text': message[0], 'role': message[1]})
            total_spent_tokens = max(total_spent_tokens, message[2])

        logging.info(f"DATABASE: Данные о последних сообщениях ({n_last_messages}) для пользователя "
                     f"с user_id={user_id} успешно найдены")

    # если результата нет, так как у нас ещё нет сообщений - возвращаем значения по умолчанию
    return messages, total_spent_tokens


# подсчитываем количество потраченных пользователем ресурсов (<limit_type> - символы или аудио-блоки)
def count_all_limits(user_id, limit_type):

    # считаем лимиты по <limit_type>, которые использовал пользователь
    query = f'''SELECT SUM({limit_type}) FROM messages WHERE user_id=?'''

    data = process_query(query, (user_id,)).fetchone()

    # проверяем data на наличие хоть какого-то полученного результата запроса
    # и на то, что в результате запроса мы получили какое-то число в data[0]
    if data and data[0]:
        # если результат есть и data[0] == какому-то числу, то:
        logging.info(f"DATABASE: У user_id={user_id} использовано {data[0]} {limit_type}")

        return data[0]  # возвращаем это число - сумму всех потраченных <limit_type>

    else:
        # результата нет, так как у нас ещё нет записей о потраченных <limit_type>
        return 0  # возвращаем 0
