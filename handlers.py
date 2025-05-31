from functools import wraps
from logger_setup import setup_loggers
from pymorphy3 import MorphAnalyzer
import threading
import sys
import subprocess
import os
import json
from datetime import datetime

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

# Словарь для хранения данных о пользователях
user_data = {}

# Глобальные переменные
stats = {}  # Словарь для хранения статистики

def get_stats():
    global stats
    return stats

def set_stats(new_stats):
    global stats
    stats = new_stats

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
    bot.reply_to(message, "Админ команды:\n/delete - удалить любое сообщение\n/ban - забанить пользователя и удалить сообщение\n/goodgirl - похвалить ботикс\n/badgirl - поругать ботикс\n/on - включить ботикс\n/off - отключить ботикс\n/restart - перезапуск ботикс\n\nПользовательские команды:\n/stats - общая статистика чата\n/mystats - личная статистика")
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

def handle_restart(message, bot=None):
    if bot is None:
        raise ValueError("Бот не передан в функцию handle_restart")

    save_stats()  # Сохраняем статистику перед рестартом
    
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

def save_stats():
    try:
        print("=== СОХРАНЕНИЕ СТАТИСТИКИ ===")
        print("Статистика перед сохранением:", stats)
        with open('chat_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
        print("Статистика успешно сохранена в файл")
        # Проверяем, что сохранилось
        with open('chat_statistics.json', 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            print("Проверка сохраненных данных:", saved_data)
        print("========================")
    except Exception as e:
        print(f"Ошибка при сохранении статистики: {e}")

def load_stats():
    global stats
    try:
        with open('chat_statistics.json', 'r', encoding='utf-8') as f:
            loaded_stats = json.load(f)
            stats = loaded_stats
            print("=== ЗАГРУЗКА СТАТИСТИКИ ===")
            print("Загруженная статистика:", loaded_stats)
            print("Текущая статистика после загрузки:", stats)
            print("========================")
    except FileNotFoundError:
        stats = {}
        print("Файл статистики не найден, создан новый словарь")
    except Exception as e:
        print(f"Ошибка при загрузке статистики: {e}")
        stats = {}
    return stats

# Обработчик команды /stats
def chat_stats(message, bot):
    global stats
    chat_id = str(message.chat.id)  # Преобразуем ID чата в строку
    
    # Удаляем команду /stats
    bot.delete_message(message.chat.id, message.message_id)
    
    print("=== ВЫВОД СТАТИСТИКИ ===")
    print("Текущая статистика:", stats)
    print("Запрошенный chat_id:", chat_id)
    print("Тип chat_id:", type(chat_id))
    print("========================")

    # Если статистика для этого чата отсутствует, создаём её
    if chat_id not in stats:
        print(f"Чат {chat_id} не найден в статистике")
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,
            "users": {}
        }
        msg = bot.send_message(message.chat.id, "Статистика чата инициализирована.")  # Заменил reply_to на send_message
    else:
        print(f"Найдена статистика для чата {chat_id}:", stats[chat_id])
        # Если статистика есть, выводим её
        msg = bot.send_message(message.chat.id,   # Заменил reply_to на send_message
                              f"Статистика чата:\n"
                              f"Сообщений: {stats[chat_id]['message_count']}\n"
                              f"Пользователей: {stats[chat_id]['user_count']}\n"
                              f"Удалённых сообщений: {stats[chat_id]['deleted_messages_count']}")
        log_user_action(message, "запустил команду /stats")
    
    # Удаляем сообщение со статистикой через 20 секунд
    delete_message_after_delay(chat_id, msg.message_id, bot, delay=20)

# Обработчик команды /mystats (показывает статистику пользователя)
def user_stats(message, bot, get_user_name_func):  # Добавляем параметр get_user_name_func
    global stats
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    # Получаем имя пользователя, используя переданную функцию
    user_name = get_user_name_func(message.from_user.id, message.chat.id)

    # Удаляем команду /mystats
    bot.delete_message(message.chat.id, message.message_id)

    print("=== ВЫВОД СТАТИСТИКИ ПОЛЬЗОВАТЕЛЯ ===")
    print("Текущая статистика:", stats)
    print("chat_id:", chat_id)
    print("user_id:", user_id)
    print("========================")

    # Проверяем, есть ли статистика для этого чата и пользователя
    if chat_id in stats and user_id in stats[chat_id]["users"]:
        user_stat = stats[chat_id]["users"][user_id]
        msg = bot.send_message(
            message.chat.id,
            f"Статистика пользователя {user_name}:\n"
            f"Сообщений: {user_stat['message_count']}\n"
            f"Последнее сообщение: {user_stat['last_message']}",
            parse_mode="HTML"
        )
    else:
        msg = bot.send_message(
            message.chat.id, 
            f"Статистика пользователя {user_name} отсутствует.",
            parse_mode="HTML"
        )

    log_user_action(message, "запустил команду /mystats")

    # Удаляем сообщение со статистикой через 20 секунд
    delete_message_after_delay(chat_id, msg.message_id, bot, delay=20)

# Обработчик всех сообщений (обновляет статистику)
def handle_message(message, bot):
    global stats
    chat_id = str(message.chat.id)  # Преобразуем ID чата в строку
    user_id = str(message.from_user.id)  # Преобразуем ID пользователя в строку

    print("=== ОБРАБОТКА СООБЩЕНИЯ ===")
    print("Текущая статистика до обновления:", stats)
    print("chat_id:", chat_id)
    print("user_id:", user_id)

    # Если статистика для этого чата отсутствует, создаём её
    if chat_id not in stats:
        stats[chat_id] = {
            "message_count": 0,
            "user_count": 0,
            "deleted_messages_count": 0,
            "users": {}
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

    print("Статистика после обновления:", stats)
    print("========================")

    # Сохраняем обновленную статистику
    save_stats()


    