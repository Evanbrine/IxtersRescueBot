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

#Проверка на правильность введённой команды
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_other_commands(message):
    if message.text != '/start':  # Проверяем, что это не /start
        bot.reply_to(message, "ПИДОРЫ, я не знаю таких комманд, пиши /help, чтобы узнать.")

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


#Передача сообщений боту из телеграма
bot.polling(none_stop=True, interval=0)


