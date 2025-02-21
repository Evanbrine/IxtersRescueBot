from functools import wraps
from logger_setup import setup_loggers
from telebot import types
from pymorphy3 import MorphAnalyzer
from telebot.types import ReplyKeyboardMarkup
import threading

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

# Словарь для хранения данных о пользователях
user_data = {}

# Глобальная переменная для хранения статистики
stats = {}

morph = MorphAnalyzer()

# Функция для логирования действий пользователя
def log_user_action(message, action):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# Обработка команды /start
def start(message, bot):
    bot.reply_to(message, "Привет! Я пришла спасти икстеров. Напиши /help, чтобы узнать, что я умею.")
    log_user_action(message, "запустил команду /start")

# Обработка команды /help
def help(message, bot):
    bot.reply_to(message, "/kick - кикнуть пользователя\n/stats - общая статистика чата\n/mystats - личная статистика")
    log_user_action(message, "запустил команду /help")

# Обработка команды /logs
def flush_logs(message, bot):
    # Принудительно записываем логи в файл
    for handler in command_logger.handlers:
        handler.flush()
    for handler in chat_logger.handlers:
        handler.flush()
    bot.reply_to(message, "Логи записаны в файл.")

# Приведение слов к изначальной форме
def lemmatize_words(words):
    return [morph.parse(word)[0].normal_form for word in words]

def kick_user(message, bot):
    # Если сообщение является ответом на другое сообщение
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
    else:
        # Если сообщение не является ответом, используем отправителя текущего сообщения
        user_id = message.from_user.id
        chat_id = message.chat.id

    # Проверяем, является ли пользователь администратором
    user_status = bot.get_chat_member(chat_id, user_id).status
    if user_status in ['administrator', 'creator']:
        bot.reply_to(message, "Невозможно кикнуть администратора.")
        return

    # Кикаем пользователя
    try:
        bot.kick_chat_member(chat_id, user_id)
        bot.reply_to(message, f"Пользователь {user_id} был кикнут за подозрение в спаме")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# Проверка, является ли пользователь администратором чата.
def is_admin(bot, chat_id, user_id):
    """
    :param bot: Объект бота.
    :param chat_id: ID чата.
    :param user_id: ID пользователя.
    :return: True, если пользователь администратор или создатель, иначе False.
    """
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except Exception as e:
        print(f"Ошибка при проверке статуса пользователя: {e}")
        return False

# Обработчик команды /stats
def chat_stats(message, bot):
    chat_id = message.chat.id
    
    # Если статистика для этого чата отсутствует, создаём её
    if chat_id not in stats:
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,  # Счётчик удалённых сообщений
            "users": {}  # Словарь для статистики пользователей
        }
        bot.reply_to(message, "Статистика чата инициализирована.")
    else:
        # Если статистика есть, выводим её
        bot.reply_to(message, f"Статистика чата:\n"
                              f"Сообщений: {stats[chat_id]['message_count']}\n"
                              f"Пользователей: {stats[chat_id]['user_count']}\n"
                              f"Удалённых сообщений: {stats[chat_id]['deleted_messages_count']}")
        log_user_action(message, "запустил команду /stats")

# Обработчик команды /mystats (показывает статистику пользователя)
def user_stats(message, bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем, есть ли статистика для этого чата и пользователя
    if chat_id in stats and user_id in stats[chat_id]["users"]:
        user_stat = stats[chat_id]["users"][user_id]
        bot.reply_to(message, f"Ваша статистика:\n"
                              f"Сообщений: {user_stat['message_count']}\n"
                              f"Последнее сообщение: {user_stat['last_message']}")
    else:
        bot.reply_to(message, "Ваша статистика отсутствует.")
    log_user_action(message, "запустил команду /mystats")

# Обработчик всех сообщений (обновляет статистику)
def handle_message(message, bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Если статистика для этого чата отсутствует, создаём её
    if chat_id not in stats:
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,  # Счётчик удалённых сообщений
            "users": {}  # Словарь для статистики пользователей
        }
    
    # Обновляем статистику чата
    stats[chat_id]["message_count"] += 1
    
    # Обновляем статистику пользователя
    if user_id not in stats[chat_id]["users"]:
        stats[chat_id]["users"][user_id] = {
            "message_count": 0,
            "last_message": None
        }
        stats[chat_id]["user_count"] += 1
    
    stats[chat_id]["users"][user_id]["message_count"] += 1
    stats[chat_id]["users"][user_id]["last_message"] = message.text