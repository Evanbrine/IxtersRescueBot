# -*- coding: cp1251 -*-

import json
import telebot
import time
from logger_setup import setup_loggers

bot = telebot.TeleBot('7700621878:AAF2bmL1zNP6CWtAlCuquVO9_pr1ww21Y7Q')

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

# Обработка команды /logs
@bot.message_handler(commands=['logs'])
def flush_logs(message):
    # Принудительно записываем логи в файл
    for handler in command_logger.handlers:
        handler.flush()
    for handler in chat_logger.handlers:
        handler.flush()
    bot.reply_to(message, "Логи записаны в файл.")

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я пришёл спасти икстеров от ПИДОРЫ. Напиши /help, чтобы узнать, что я умею.")
    log_user_action(message, "запустил команду /start")

# Обработка команды /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "/kick - кикнуть пользователя")
    log_user_action(message, "запустил команду /help")

# Пасхалк0
@bot.message_handler(commands=['xyu'])
def xyu(message):
    bot.reply_to(message, "оставь это для жопы рекламщиков")
    log_user_action(message, "запустил команду /xyu")

#Обработка кика
@bot.message_handler(commands=['kick'])
def kick_user(message):
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

#Приветственное сообщение при входе в чат нового пользователя
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    for new_member in message.new_chat_members:
        # Отправляем сообщение в группу
        bot.send_message(
            message.chat.id,
            f"Привет, {new_member.first_name}! Если ты не ПИДОРЫ, то прочти эти правила https://telegra.ph/ixtersrules-09-04."
        )

'''
@bot.message_handler(commands=['info'])
def send_chat_info(message):
    try:
        # Получаем информацию о чате
        chat_info = bot.get_chat(message.chat.id)
        
        # Отправляем информацию пользователю
        bot.reply_to(message, f"Информация о чате:\n"
                              f"ID: {chat_info.id}\n"
                              f"Тип: {chat_info.type}\n"
                              f"Название: {chat_info.title}\n"
                              f"Имя пользователя: {chat_info.username}\n"
                              f"Описание: {chat_info.description}\n"
                              f"Ссылка-приглашение: {chat_info.invite_link}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")
'''


'''
#Повторялка
@bot.message_handler(func=lambda message: True) 
def echo_all(message): 
    bot.reply_to(message, message.text)
'''   
'''
    # Открываем файл для чтения
    with open("message%20ratios.txt", "r") as file:
        for line in file:  # Читаем файл построчно
            if len(line) > 2: 
                stripped_line = line[:-3]  # Отрезаем последние два символа
                if stripped_line in line: # Проверяем входит ли вторая строка в первую
                    line_number = line.replace(stripped_line, '') # Заменяем вторую строку на пустоту
                    bot.reply_to(message, line_number)
                bot.reply_to(message, stripped_line)
                time.sleep(4)
'''

# Чтение файла с запрещёнными словами
try:
    with open('forbidden_message.txt', 'r', encoding='cp1251') as file:  # Указываем кодировку cp1251
        forbidden_dict = json.load(file)
        print("Содержимое файла:", forbidden_dict)  # Отладка
except Exception as e:
    print(f"Ошибка при чтении файла: {e}")
    forbidden_dict = {}  # Если файл не удалось прочитать, используем пустой словарь

# Словарь для хранения статистики
stats = {}

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

# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def chat_stats(message):
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
@bot.message_handler(commands=['mystats'])
def user_stats(message):
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
@bot.message_handler(func=lambda message: True)
def handle_message(message):
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






#Проверка на правильность введённой команды
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_other_commands(message):
    if message.text != '/start':  # Проверяем, что это не /start
        bot.reply_to(message, "ПИДОРЫ, я не знаю таких комманд, пиши /help, чтобы узнать.")

#Передача сообщений боту из телеграма
bot.polling(none_stop=True, interval=0)

