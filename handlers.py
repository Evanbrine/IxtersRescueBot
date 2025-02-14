import re
from functools import wraps
from logger_setup import setup_loggers

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

# Функция для логирования действий пользователя
def log_user_action(message, action):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# Обработка команды /start
def start(message, bot):
    bot.reply_to(message, "Привет! Я пришёл спасти икстеров от ПИДОРЫ. Напиши /help, чтобы узнать, что я умею.")
    log_user_action(message, "запустил команду /start")

# Обработка команды /help
def help(message, bot):
    bot.reply_to(message, "/kick - кикнуть пользователя")
    bot.reply_to(message, "/stats - общая статистика чата")
    bot.reply_to(message, "/mystats - личная статистика")
    log_user_action(message, "запустил команду /help")

# Обработка команды /logs
def flush_logs(message, bot):
    # Принудительно записываем логи в файл
    for handler in command_logger.handlers:
        handler.flush()
    for handler in chat_logger.handlers:
        handler.flush()
    bot.reply_to(message, "Логи записаны в файл.")

# Обработка кика
def kick_user(message, bot):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "Невозможно кикнуть администратора.")
        else:
            bot.kick_chat_member(chat_id, user_id)
            bot.reply_to(message, f"Пользователь {message.reply_to_message.from_user.username} был кикнут.")
    else:
        bot.reply_to(message, "Эта команда должна быть использована в ответ на сообщение пользователя, которого вы хотите кикнуть.")

# Приветственное сообщение при входе в чат нового пользователя
def greet_new_members(message, bot):
    for new_member in message.new_chat_members:
        # Отправляем сообщение в группу
        bot.send_message(
            message.chat.id,
            f"Привет, {new_member.first_name}! Если ты не ПИДОРЫ, то прочти эти правила https://telegra.ph/ixtersrules-09-04."
        )

# Глобальная переменная для хранения статистики
stats = {}

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

# Обработчик всех сообщений
def handle_message(message, bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    message_id = message.message_id  # ID сообщения для удаления
    
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