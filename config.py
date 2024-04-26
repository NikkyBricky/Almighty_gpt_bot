from dotenv import load_dotenv
import os
from telebot.types import BotCommand
from make_gpt_token import get_creds
load_dotenv()

# Общие настройки
LOGS = 'logs.txt'  # файл для логов
DB_FILE = 'user_data.db'  # файл для базы данных

# Общие настройки для сервера
# HOME_DIR = '/home/student/gpt_bot'  # путь к папке с проектом
# LOGS = f'{HOME_DIR}/logs.txt'  # файл для логов
# DB_FILE = f'{HOME_DIR}/user_data.db'  # файл для базы данных

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
MAX_USERS = 3  # максимальное кол-во пользователей
COMMANDS = [BotCommand(command="/start", description="Запуск бота"),
            BotCommand(command="/help", description="Подробное описание бота"),
            BotCommand(command="/settings", description="Настройка взаимодействия с ботом"),
            BotCommand(command="/stats", description="Статистика расходов пользователя"),
            BotCommand(command="/stt", description="Проверка распознавания речи (админ)"),
            BotCommand(command="/tts", description="Проверка синтеза речи (админ)"),
            BotCommand(command="/debug", description="Проверка ошибок (админ)")]

BOT_NAME = "Бот Всемогущий"
BOT_DESCRIPTION = ("Данный бот поможет вам в любом вопросе, ведь использует yandexgpt под капотом! "
                   "Он также умеет слушать и разговаривать, "
                   "так что обязательно попробуйте отправить ему голосовое сообщение!")

CONTENT_TYPES = ["audio", "document", "photo", "sticker", "video", "video_note"]

# Настройки для gpt
IAM_TOKEN = os.getenv("IAM_TOKEN")  # для локального запуска

if not IAM_TOKEN:  # для запуска на сервере
    IAM_TOKEN = get_creds()

FOLDER_ID = os.getenv("FOLDER_ID")
MODEL = "yandexgpt"
MAX_GPT_TOKENS = 150  # максимальное кол-во токенов в ответе GPT
COUNT_LAST_MSG = 4  # кол-во последних сообщений из диалога

# список с системным промптом
SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты вежливый ассистент. Ты специалист во всех областях знания. '
                                            'Отвечай на все вопросы подробно. '
                                            'Используй форматирование.'
                                            'Не рассказывай о том, что ты можешь и умеешь.'
                                            'Не пиши больше 5 предложений.'}]


# Лимиты для пользователя
MAX_USER_STT_BLOCKS = 10  # 10 аудио-блоков
MAX_USER_TTS_SYMBOLS = 5_000  # 5 000 символов
MAX_USER_GPT_TOKENS = 2_000  # 2 000 токенов
MAX_AUDIO_DURATION = 30  # 30 секунд

# Грамматика
GRAMMAR_API_KEY = os.getenv("GRAMMAR_API_KEY")
USE_GRAMMAR_CHECK = False
basic_url = "https://api.textgears.com/grammar"
lang = "ru-RU"


# Константы для бота
START_MSG = ("Привет, друг! Я бот, который поможет вам в любом вопросе, "
             "ведь я использую yandexgpt! Я также умею слушать и разговаривать, "
             "так что обязательно попробуйте отправить мне голосовое сообщение!")

ABOUT_BOT = ("<b>Добро пожаловать в путеводитель по Всемогущему Боту</b>!\n\n"
             "У него такое имя, "
             "потому что он использует <b>одну из самых мощных нейросетей</b> yandexgpt "
             "для выполнения ваших задач.\n\n"
             "Его предназначение состоит в том, чтобы помогать "
             "людям с возникающими у них вопросами и сложностями. Если вы хотите что-то узнать"
             " или понять, то просто <b>напишите ваш вопрос в чат с ботом или запишите "
             "голосовое сообщение</b>. Бот ответит <b>в любом случае</b>!\n"
             "Кстати, разговаривать он и сам умеет :)\n\n"
             "<b>О функционале</b>\n\n"
             "/start - Команда для начала работы с ботом.\n\n"
             "/help - основная информация о боте.\n\n"
             '/settings <b>или кнопка "⚙️Параметры"</b> - позволяет изменить '
             'вашу текущую конфигурацию параметров общения с ботом. Здесь вы можете выбрать, '
             'в каком виде хотите получать ответ нейросети, в зависимости от того, текстовый '
             'или голосовой запрос вы используете. Также вы можете включить/выключить '
             'расшифровку голосовых сообщений. Расшифровано будет как ваше сообщение, так и '
             'ответ нейросети. Если при выборе конфигурации вам что-то непонятно, то после '
             'возврата в главное меню, вы сможете увидеть вашу текущую конфигурацию в более '
             'наглядной форме.\n\n'
             '/stats <b>или кнопка "📊Статистика"</b> - покажет вашу текущую '
             'статистику <b>расходов</b>.\n\n'
             '<b>О расходах</b>\n\n'
             'Так как разработка новейших технологий довольно трудоемкий процесс, то, конечно,'
             ' их использование <b>не является бесплатным</b>.'
             ' Поэтому каждому пользователю дается '
             '<b>ограниченное</b> количество ресурсов,'
             ' которые он может потратить на работу с ботом. '
             'Все лимиты и расходы как раз и находятся в <b>статистике.</b>\n\n'
             'После превышения одного из лимитов, '
             'функция связанная с ним <b>станет недоступна</b>.\n\n'
             'Но, если, например, у вас закончатся '
             'символы для синтеза речи, вы всегда можете поменять в <b>параметрах</b>'
             ' конфигурацию ответа нейросети с голосовой '
             'на текстовую и продолжить работу с ботом.\n\n'
             'Остальные имеющиеся команды нужны <b>только админам</b>, '
             'поэтому <b>использоваться могут только ими</b>.\n\n'
             '<b>Желаю приятного времяпрепровождения!</b>')

IS_PROCESSING_ANSWER_MSG = ("Нейросеть уже отвечает на Ваш вопрос. Прежде чем задать следующий, "
                            "дождитесь ответа на предыдущий.")