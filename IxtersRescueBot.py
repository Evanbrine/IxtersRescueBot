# -*- coding: cp1251 -*-

#print("хуй")

import telebot
import time

bot = telebot.TeleBot('7700621878:AAF2bmL1zNP6CWtAlCuquVO9_pr1ww21Y7Q')

#Обработака команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я пришёл спасти икстеров от ПИДОРЫ. Напиши /help, чтобы узнать, что я умею. ")

#Обработака команды /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "/kick - кикнуть пользователя")

#ПасхалкО
@bot.message_handler(commands=['xyu'])
def help(message):
    bot.reply_to(message, "оставь это для жопы рекламщиков")

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

@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    for new_member in message.new_chat_members:
        # Отправляем сообщение в группу
        bot.send_message(
            message.chat.id,
            f"Привет, {new_member.first_name}! Если ты не ПИДОРЫ, то прочти эти правила https://telegra.ph/ixtersrules-09-04."
        )

#Проверка на правильность введённой команды
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_other_commands(message):
    if message.text != '/start':  # Проверяем, что это не /start
        bot.reply_to(message, "ПИДОРЫ, я не знаю таких комманд, пиши /help, чтобы узнать.")

@bot.message_handler(func=lambda message: True) 
def echo_all(message): 
    bot.reply_to(message, message.text)
    
    words = []
# Открываем файл для чтения
    with open("message%20ratios.txt", "r") as file:
        for line in file:  # Читаем файл построчно
            # Разделяем строку на слова и добавляем их в общий список
            words.extend(line.split())
            list_test_words = words.extend(line.split())
            list_test_words = list_test_words[:-1]
            #Пример: s = "Привет, мир!". s_new = s[:-1]
            bot.reply_to(message, line.strip())

# Выводим список слов
#print(words)
    






#Передача сообщений боту из телеграма
bot.polling(none_stop=True, interval=0)

