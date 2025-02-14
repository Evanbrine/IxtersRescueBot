import json
import telebot
import time
from logger_setup import setup_loggers
from handlers import start, help, flush_logs, kick_user, greet_new_members, chat_stats, user_stats, handle_message  # Импортируем обработчики
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

# Функция для логирования действий пользователя
def log_user_action(message, action):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# Функция для логирования сообщений чата
def log_chat_message(message):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    chat_logger.info(f"{user_info} отправил сообщение: {message.text}")

# Регистрация обработчиков команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message, bot)  # Вызов обработчика из handlers.py

@bot.message_handler(commands=['help'])
def handle_help(message):
    help(message, bot)  # Вызов обработчика из handlers.py

@bot.message_handler(commands=['logs'])
def handle_flush_logs(message):
    flush_logs(message, bot)  # Вызов обработчика из handlers.py

@bot.message_handler(commands=['kick'])
def kick_user(message):
   kick_user(message, bot)   # Вызов обработчика из handlers.py

#Приветственное сообщение при входе в чат нового пользователя
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    greet_new_members(message)   # Вызов обработчика из handlers.py

# Регистрация обработчиков команд
@bot.message_handler(commands=['stats'])
def handle_stats(message):
    chat_stats(message, bot)  # Вызов обработчика /stats

@bot.message_handler(commands=['mystats'])
def handle_mystats(message):
    user_stats(message, bot)  # Вызов обработчика /mystats

# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    handle_message(message, bot)  # Вызов обработчика всех сообщений

# Чтение файла с запрещёнными словами
try:
    with open('forbidden_message.txt', 'r', encoding='cp1251') as file:  # Указываем кодировку cp1251
        forbidden_dict = json.load(file)
        print("Содержимое файла:", forbidden_dict)  # Отладка
except Exception as e:
    print(f"Ошибка при чтении файла: {e}")
    forbidden_dict = {}  # Если файл не удалось прочитать, используем пустой словарь

# Функция для расчёта риска
def calculate_risk(message):
    words = message.text.lower().split()  # Разделяем сообщение на слова
    total_risk = 0
    
    # Считаем общий риск
    for word in words:
        if word in forbidden_dict:
            total_risk += forbidden_dict[word]
    
    # Возвращаем средний риск (общий риск / количество слов)
    return total_risk / len(words) if len(words) > 0 else 0

    # Проверяем длину сообщения
    words = message.text.split()
    if len(words) < 10:  # Если сообщение меньше 10 слов, игнорируем
        print(f"Сообщение от {message.from_user.username} содержит меньше 10 слов. Пропускаем.")  # Отладка
        return
    
    # Рассчитываем средний риск
    average_risk = calculate_risk(message)
    print(f"Средний риск сообщения: {average_risk}")  # Отладка
    
    # Проверяем, превышает ли риск порог
    if average_risk > 10:  # Порог риска
        print(f"Сообщение от {message.from_user.username} превысило порог риска.")  # Отладка
        try:
            # Увеличиваем счётчик удалённых сообщений
            stats[chat_id]["deleted_messages_count"] += 1
            
            # Удаляем сообщение
            bot.delete_message(chat_id, message_id)
            print(f"Сообщение {message_id} удалено.")  # Отладка
            
            # Кикаем пользователя
            bot.kick_chat_member(chat_id, user_id)
            bot.send_message(chat_id, f"Пользователь {message.from_user.username} был удален из чата за нарушение правил.")
            
            # Логируем кик пользователя
            log_user_action(message, "был кикнут из чата за нарушение правил")
        except Exception as e:
            print(f"Ошибка: {e}")  # Отладка
    else:
        print("Сообщение безопасно.")  # Отладка




#Передача сообщений боту из телеграма
bot.polling(none_stop=True, interval=0)

