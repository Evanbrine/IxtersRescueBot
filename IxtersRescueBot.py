import json
import telebot
import time
from logger_setup import setup_loggers
from handlers import start, help, flush_logs, kick_user, greet_new_members, chat_stats, user_stats, handle_message, is_admin, morph, lemmatize_words, handle_response  # Импортируем обработчики
from telebot import types
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
# Регистрация обработчиков команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message, bot)

@bot.message_handler(commands=['help'])
def handle_help(message):
    help(message, bot)

@bot.message_handler(commands=['logs'])
def handle_flush_logs(message):
    flush_logs(message, bot)

@bot.message_handler(commands=['kick'])
def handle_kick(message):
    if not is_admin(bot, message.chat.id, message.from_user.id):
        return
    kick_user(message, bot)

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    greet_new_members(message, bot)

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    chat_stats(message, bot)

@bot.message_handler(commands=['mystats'])
def handle_mystats(message):
    user_stats(message, bot)

# Обработчик ответов "Да" и "Нет"
@bot.message_handler(func=lambda message: message.text in ["Да", "Нет"])
def handle_response_message(message):
    handle_response(message, bot)

# Функция для логирования действий пользователя
def log_user_action(message, action):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    command_logger.info(f"{user_info} {action}")

# Функция для логирования сообщений чата
def log_chat_message(message):
    user_info = f"Пользователь {message.from_user.username} (ID: {message.from_user.id})"
    chat_logger.info(f"{user_info} отправил сообщение: {message.text}")

# Чтение файла с запрещёнными словами
try:
    with open('forbidden_message.json', 'r', encoding='utf-8') as file:
        forbidden_dict = json.load(file)
        print("Содержимое файла с запрещёнными словами:", forbidden_dict)  # Отладка
except Exception as e:
    print(f"Ошибка при чтении файла с запрещёнными словами: {e}")
    forbidden_dict = {}  # Если файл не удалось прочитать, используем пустой словарь

# Чтение файла с фразами
try:
    with open('forbidden_phrases.json', 'r', encoding='utf-8') as file:
        forbidden_phrases = json.load(file)
        print("Содержимое файла с фразами:", forbidden_phrases)  # Отладка
except Exception as e:
    print(f"Ошибка при чтении файла с фразами: {e}")
    forbidden_phrases = []  # Если файл не удалось прочитать, используем пустой список

# Функция для расчёта риска
def calculate_risk(message):
    print("Начинаем расчёт риска для сообщения:", message.text)  # Отладка
    words = message.text.lower().split()  # Переводим сообщение в нижний регистр и разделяем на слова
    lemmatized_words = lemmatize_words(words)  # Применяем лемматизацию к каждому слову
    print(f"Сообщение в начальной форме: {lemmatized_words}")

    total_risk = 0

    # Сначала проверяем фразы
    for phrase in forbidden_phrases:
        phrase_words = phrase["words"]
        if all(word in lemmatized_words for word in phrase_words):  # Если все слова из фразы есть в сообщении
            total_risk += phrase["multiplier"]  # Увеличиваем риск на указанный множитель
            print(f"Найдена фраза: {phrase_words}, риск увеличен на {phrase['multiplier']}")  # Отладка
    
    # Затем проверяем отдельные слова
    for word in lemmatized_words:
        if word in forbidden_dict:
            total_risk += forbidden_dict[word]
            print(f"Найдено запрещённое слово: {word}, риск увеличен на {forbidden_dict[word]}")  # Отладка
    
    # Возвращаем средний риск (общий риск / количество слов)
    average_risk = total_risk / len(lemmatized_words) if len(lemmatized_words) > 0 else 0
    print(f"Средний риск сообщения: {average_risk}")  # Отладка
    return average_risk

# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    print("Новое сообщение получено!")  # Отладка
    print("Текст сообщения:", message.text)  # Отладка
    
    # Обновляем статистику через handle_message
    handle_message(message, bot)
    
    # Проверяем длину сообщения
    words = message.text.split()
    if len(words) < 5:  # Если сообщение меньше 5 слов, игнорируем
        print(f"Сообщение от {message.from_user.username} содержит меньше 5 слов. Пропускаем.")  # Отладка
        return
    
    # Рассчитываем средний риск
    average_risk = calculate_risk(message)
    
    # Проверяем, превышает ли риск порог
    if average_risk >= 2.5:  # Порог риска
        print(f"Сообщение от {message.from_user.username} превысило порог риска.")  # Отладка
        try:
            # Удаляем сообщение
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(chat_id=message.chat.id, text=f"Сообщение удалено за подозрение на рекламу.")
            print(f"Сообщение {message.message_id} удалено.")  # Отладка
            
            # Кикаем пользователя с помощью функции kick_user
            #kick_user(message, bot)
        except Exception as e:
            print(f"Ошибка: {e}")  # Отладка
    else:
        print("Сообщение безопасно.")  # Отладка

bot.polling(none_stop=True, interval=0)