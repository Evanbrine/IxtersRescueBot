import json
import telebot
import time
from logger_setup import setup_loggers
from handlers import start, help, flush_logs, kick_user, chat_stats, user_stats, handle_message, is_admin, morph, lemmatize_words, delete_message_after_delay, handle_restart  # Импортируем обработчики
from telebot import types
from config import TOKEN
import threading

bot = telebot.TeleBot(TOKEN)

# Инициализация логгеров
command_logger, chat_logger = setup_loggers()

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

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    chat_stats(message, bot)

@bot.message_handler(commands=['mystats'])
def handle_mystats(message):
    user_stats(message, bot)

@bot.message_handler(commands=['restart'])
def restart_command(message):
    if not is_admin(bot, message.chat.id, message.from_user.id):
        return
    handle_restart(message, bot)

# Флаг для режима ожидания
is_paused = False

# Команда /off
@bot.message_handler(commands=['off'])
def turn_off(message):
    global is_paused
    if not is_admin(bot, message.chat.id, message.from_user.id):  # Проверка прав администратора
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
    is_paused = True
    bot.reply_to(message, "Бот переведён в режим ожидания. Используйте /on, чтобы включить его снова.")
        

# Команда /on
@bot.message_handler(commands=['on'])
def turn_on(message):
    global is_paused
    if not is_admin(bot, message.chat.id, message.from_user.id):  # Проверка прав администратора
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")
    is_paused = False
    bot.reply_to(message, "Бот снова активен!")

new_user_data = {}

# Функция для генерации уникального callback_data, нужно для нажатия кнопок
def generate_callback_data(user_id):
    return f"verify_{user_id}"

def get_user_name(user_id, chat_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)

        # Проверяем username
        if member.user.username:
            return f"@{member.user.username}"

        # Если нет username, используем first_name и last_name
        if member.user.first_name and member.user.last_name:
            return f"{member.user.first_name} {member.user.last_name}".replace(" ", "_")  # Заменяем пробелы на подчеркивание для корректного форматирования

        elif member.user.first_name:
            return member.user.first_name.replace(" ", "_")

        # Если нет имени, возвращаем цифровой идентификатор
        return f"ID_{user_id}"

    except Exception as e:
        print(f"Ошибка при получении имени пользователя {user_id}: {e}")
        return f"ID_{user_id}"

# Функция для отправки сообщения с кнопкой
def send_verification_message(chat_id, user_id):
    # Создаем кнопку с уникальным callback_data
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Я не бот!", callback_data=generate_callback_data(user_id))
    markup.add(button)

    # Получаем имя пользователя для формирования сообщения
    user_name = get_user_name(user_id, chat_id)

    # Отправляем сообщение в чат
    msg = bot.send_message(
        chat_id,
        f"👋 <a href='tg://user?id={user_id}'>{user_name}</a>, подтвердите, что вы не бот! У вас 30 секунд",
        parse_mode="HTML",
        reply_markup=markup, # для кнопок
        disable_notification=True # отключение уведомления для остальных участников
    )

    # Сохраняем данные о пользователе
    new_user_data[user_id] = {
        "chat_id": chat_id,
        "message_id": msg.message_id,
        "timer": None,
        "msg_object": msg  # Добавляем объект сообщения для удаления
    }

    # Запускаем таймер на 30 секунд
    timer = threading.Timer(30.0, kick_user_if_no_response, args=[chat_id, user_id])
    new_user_data[user_id]["timer"] = timer
    timer.start()

# Функция для кика пользователя, если он не ответил
def kick_user_if_no_response(chat_id, user_id):
    if user_id in new_user_data:
        # Кикаем пользователя
        bot.kick_chat_member(chat_id, user_id)
        msg1 = bot.send_message(chat_id, f"Пользователь {get_user_name(user_id, chat_id)} был кикнут за неактивность.", parse_mode="HTML")
        
        # Удаляем сообщение с кнопкой "Я не бот!"
        msg2 = new_user_data[user_id]["msg_object"]
        bot.delete_message(msg1.chat.id, msg1.message_id)
        # Удаляем сообщение "был кикнут за неактивность"
        bot.delete_message(msg2.chat.id, msg2.message_id)

        # Удаляем данные пользователя
        del new_user_data[user_id]

# Обработчик новых участников чата
@bot.message_handler(content_types=['new_chat_members'])
def handle_new_members(message):
    for new_user in message.new_chat_members:
        # Отправляем сообщение с кнопкой
        send_verification_message(message.chat.id, new_user.id)

# Обработчик нажатия на кнопку
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = int(call.data.split('_')[1])
    if user_id == call.from_user.id:
        # Получаем корректное имя пользователя
        user_name = get_user_name(user_id, call.message.chat.id)

        # Отправляем подтверждение и удаляем кнопку
        bot.send_message(call.message.chat.id, f"Привет, {user_name}! Вы успешно подтвердили, что вы не бот.", disable_notification=True)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        # Останавливаем таймер
        if user_id in new_user_data:
            new_user_data[user_id]['timer'].cancel()
            del new_user_data[user_id]

    # Отвечаем на callback (чтобы убрать "часики" на кнопке)
    bot.answer_callback_query(call.id)

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
    forbidden_dict = {}

# Чтение файла с фразами
try:
    with open('forbidden_phrases.json', 'r', encoding='utf-8') as file:
        forbidden_phrases = json.load(file)
        print("Содержимое файла с фразами:", forbidden_phrases)
except Exception as e:
    print(f"Ошибка при чтении файла с фразами: {e}")
    forbidden_phrases = []

def save_forbidden_phrases():
    try:
        with open('forbidden_phrases.json', 'w', encoding='utf-8') as file:
            json.dump(forbidden_phrases, file, ensure_ascii=False, indent=4)
        print("Фразы успешно сохранены в файл.")
    except Exception as e:
        print(f"Ошибка при сохранении файла с фразами: {e}")

def save_forbidden_dict():
    try:
        with open('forbidden_message.json', 'w', encoding='utf-8') as file:
            json.dump(forbidden_dict, file, ensure_ascii=False, indent=4)
        print("Словарь успешно сохранён в файл.")
    except Exception as e:
        print(f"Ошибка при сохранении словаря: {e}")

last_matched_words = []
last_matched_phrases = []
last_message_chat_id = None
last_message_id = None
last_message_deleted = False
last_message_text = ""
last_all_words = []
message_repeat_count = 0

def calculate_risk_with_tracking(message):
    global last_matched_words, last_matched_phrases, last_message_chat_id, last_message_id, last_message_deleted, last_message_text, message_repeat_count, last_all_words

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
    global is_paused, last_message_deleted, deleted_messages_log
    if is_paused:
        return
    else:
        print("Новое сообщение получено!")
        print("Текст сообщения:", message.text)
    
        # Обновляем статистику через handle_message
        handle_message(message, bot)
    
        # Проверяем длину сообщения
        words = message.text.split()
        if len(words) < 5:
            print(f"Сообщение от {message.from_user.username} содержит меньше 5 слов. Пропускаем.")
            #Проверка, есть ли сдохнуть в сообщении
            check_death_word_and_respond(message)
            return
    
        # Рассчитываем средний риск (включает проверку повторений)
        average_risk = calculate_risk_with_tracking(message)
    
        # Проверяем, превышает ли риск порог
        if average_risk >= 2.5:
            print(f"Сообщение от {message.from_user.username} превысило порог риска.")
            try:
                # Сохраняем информацию об удаляемом сообщении
                deleted_messages_log[message.message_id] = {
                    "text": message.text,
                    "user_id": message.from_user.id,
                    "timestamp": datetime.now(),
                    "words": last_all_words.copy()
                }

                # Удаляем сообщение
                bot.delete_message(message.chat.id, message.message_id)
                
                # Отправляем сообщение с кнопкой жалобы
                keyboard = create_complaint_keyboard(message.message_id)
                msg = bot.send_message(
                    chat_id=message.chat.id, 
                    text=f"Сообщение удалено за подозрение на рекламу.\n"
                         f"Если это ошибка, нажмите кнопку ниже:", 
                    reply_markup=keyboard,
                    disable_notification=True
                )

                # Удаляем сообщение с кнопкой через 30 секунд
                delete_message_after_delay(message.chat.id, msg.message_id, bot, delay=30)

                print(f"Сообщение {message.message_id} удалено.")
                last_message_deleted = True
                message_repeat_count = 0

                # Положительное обучение
                if last_matched_words or last_matched_phrases:
                    print("Автообучение: подтверждаем правильность удаления")
                    manual_learn(positive_feedback=True, multiplier=0.5)

                print(f"Сообщение {message.message_id} удалено.")  # Отладка
            except Exception as e:
                print(f"Ошибка при удалении: {e}")
                last_message_deleted = False
        else:
            print("Сообщение безопасно.")
            last_message_deleted = False
            #Проверка, есть ли сдохнуть в сообщении
            check_death_word_and_respond(message)

# Функция для очистки старых записей из лога (вызывать периодически)
def cleanup_old_logs():
    """Удаляет записи старше 1 часа из лога удаленных сообщений"""
    global deleted_messages_log
    current_time = datetime.now()
    to_delete = []
    
    for msg_id, info in deleted_messages_log.items():
        if current_time - info["timestamp"] > timedelta(hours=1):
            to_delete.append(msg_id)
    
    for msg_id in to_delete:
        del deleted_messages_log[msg_id]
    
    print(f"Очищено {len(to_delete)} старых записей из лога")

bot.polling(none_stop=True, interval=0)