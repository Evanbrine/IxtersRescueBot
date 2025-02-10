# -*- coding: cp1251 -*-

#print("���")

import telebot
import time

bot = telebot.TeleBot('7700621878:AAF2bmL1zNP6CWtAlCuquVO9_pr1ww21Y7Q')

#���������� ������� /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "������! � ������ ������ �������� �� ������. ������ /help, ����� ������, ��� � ����. ")

#���������� ������� /help
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "/kick - ������� ������������")

#��������
@bot.message_handler(commands=['xyu'])
def help(message):
    bot.reply_to(message, "������ ��� ��� ���� �����������")

#��������� ����
@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.reply_to_message:
        chat_id = message.chat.id
        user_id = message.reply_to_message.from_user.id
        user_status = bot.get_chat_member(chat_id, user_id).status
        if user_status == 'administrator' or user_status == 'creator':
            bot.reply_to(message, "���������� ������� ��������������.")
        else:
            bot.kick_chat_member(chat_id, user_id)
            bot.reply_to(message, f"������������ {message.reply_to_message.from_user.username} ��� ������.")
    else:
        bot.reply_to(message, "��� ������� ������ ���� ������������ � ����� �� ��������� ������������, �������� �� ������ �������.")

@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    for new_member in message.new_chat_members:
        # ���������� ��������� � ������
        bot.send_message(
            message.chat.id,
            f"������, {new_member.first_name}! ���� �� �� ������, �� ������ ��� ������� https://telegra.ph/ixtersrules-09-04."
        )

#�������� �� ������������ �������� �������
@bot.message_handler(func=lambda message: message.text.startswith('/'))
def handle_other_commands(message):
    if message.text != '/start':  # ���������, ��� ��� �� /start
        bot.reply_to(message, "������, � �� ���� ����� �������, ���� /help, ����� ������.")

@bot.message_handler(func=lambda message: True) 
def echo_all(message): 
    bot.reply_to(message, message.text)
    
    words = []
# ��������� ���� ��� ������
    with open("message%20ratios.txt", "r") as file:
        for line in file:  # ������ ���� ���������
            # ��������� ������ �� ����� � ��������� �� � ����� ������
            words.extend(line.split())
            list_test_words = words.extend(line.split())
            list_test_words = list_test_words[:-1]
            #������: s = "������, ���!". s_new = s[:-1]
            bot.reply_to(message, line.strip())

# ������� ������ ����
#print(words)
    






#�������� ��������� ���� �� ���������
bot.polling(none_stop=True, interval=0)

