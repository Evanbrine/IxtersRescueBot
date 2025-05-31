from functools import wraps
from logger_setup import setup_loggers
from telebot import types
from pymorphy3 import MorphAnalyzer
from telebot.types import ReplyKeyboardMarkup
import threading
import sys
import subprocess
import os

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

# Функция для остановки бота
def stop_bot(bot):
    bot.stop_polling()
    print("Бот остановлен.")

# Функция для перезапуска бота
def restart_bot():
    print("Перезапуск бота...")
    # Запуск нового процесса бота
    subprocess.Popen([sys.executable, "IxtersRescueBot.py"])
    # Завершение текущего процесса
    os._exit(0)

# Обработчик команды /restart
def handle_restart(message, bot=None):
    if bot is None:
        raise ValueError("Бот не передан в функцию handle_restart")

    # Даем время боту завершить текущие операции
    import time
    time.sleep(1)

    # Останавливаем бота
    stop_bot(bot)

    # Перезапускаем бота
    restart_bot()

# Приведение слов к изначальной форме
def lemmatize_words(words):
    return [morph.parse(word)[0].normal_form for word in words]

def kick_user(message, bot, get_user_name):
    # Если сообщение является ответом на другое сообщение
    if message.reply_to_message:
        user_id = message.from_user.id
        chat_id = message.chat.id
    else:
        # Если сообщение не является ответом, используем отправителя текущего сообщения
        user_id = message.from_user.id
        chat_id = message.chat.id

    # Проверяем, является ли пользователь администратором
    user_status = bot.get_chat_member(chat_id, user_id).status
    if user_status in ['administrator', 'creator']:
        #bot.reply_to(message, "Невозможно кикнуть администратора.")
        return

    # Кикаем пользователя
    try:
        bot.kick_chat_member(chat_id, user_id)
        bot.reply_to(message, f"Пользователь {get_user_name(user_id, chat_id)} был кикнут за подозрение в спаме", disable_notification=True, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

def delete_message_after_delay(chat_id, message_id, bot, delay=10):
    def delete_message():
        try:
            print(f"Попытка удалить сообщение {message_id} в чате {chat_id}.")
            bot.delete_message(chat_id, message_id)
            print(f"Сообщение {message_id} удалено.")
        except Exception as e:
            print(f"Ошибка при удалении сообщения {message_id}: {e}")

    # Запускаем таймер
    print(f"Таймер запущен для сообщения {message_id}.")
    timer = threading.Timer(delay, delete_message)
    timer.start()

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
        msg = bot.reply_to(message, "Статистика чата инициализирована.")
    else:
        # Если статистика есть, выводим её
        msg = bot.reply_to(message, f"Статистика чата:\n"
                              f"Сообщений: {stats[chat_id]['message_count']}\n"
                              f"Пользователей: {stats[chat_id]['user_count']}\n"
                              f"Удалённых сообщений: {stats[chat_id]['deleted_messages_count']}")
        log_user_action(message, "запустил команду /stats")
    
    # Удаляем сообщение со статистикой через 20 секунд
    delete_message_after_delay(chat_id, msg.message_id, bot, delay=20)

# Обработчик команды /mystats (показывает статистику пользователя)
def user_stats(message, bot):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Проверяем, есть ли статистика для этого чата и пользователя
    if chat_id in stats and user_id in stats[chat_id]["users"]:
        user_stat = stats[chat_id]["users"][user_id]
        msg = bot.reply_to(message, f"Ваша статистика:\n"
                              f"Сообщений: {user_stat['message_count']}\n"
                              f"Последнее сообщение: {user_stat['last_message']}")
    else:
        msg = bot.reply_to(message, "Ваша статистика отсутствует.")
    
    log_user_action(message, "запустил команду /mystats")
    
    # Удаляем сообщение со статистикой через 20 секунд
    delete_message_after_delay(chat_id, msg.message_id, bot, delay=20)

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



    