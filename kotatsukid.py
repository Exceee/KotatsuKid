#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import datetime
import random
import re
import hashlib
import requests
import json
import threading

import telepot

# Load the parameters from text files
with open('settings/bot.txt', 'r', encoding="utf8") as botfile:
    botParams = botfile.read().splitlines()
botname = botParams[0]
botKey = botParams[1]
admin_chat_id = int(botParams[2])
group_chat_id = int(botParams[3])
twitch_client_id = botParams[4]

with open('settings/emotions.txt', 'r', encoding="utf8") as emojifile:
    emotions = emojifile.read().splitlines()

with open('settings/yoba.txt', 'r', encoding="utf8") as yobafile:
    yobas = yobafile.read().splitlines()

with open('settings/replies.txt', 'r', encoding="utf8") as repliesfile:
    replies = repliesfile.read().splitlines()

with open('settings/sports.txt', 'r', encoding="utf8") as sportfile:
    sports = sportfile.read().splitlines()

with open('settings/casino.txt', 'r', encoding="utf8") as casinofile:
    casinos = casinofile.read().splitlines()

with open('settings/ofcourse.txt', 'r', encoding="utf8") as ofcoursefile:
    ofcourseWordList = ofcoursefile.read().splitlines()

with open('settings/answers.txt', 'r', encoding="utf8") as answersfile:
    answerslist = answersfile.read().splitlines()

with open('settings/good_evening.txt', 'r', encoding="utf8") as eveningfile:
    good_evening = eveningfile.read()

with open('settings/imhere.txt', 'r', encoding="utf8") as imherefile:
    imherelist = imherefile.read().splitlines()

with open('settings/streamnames.txt', 'r', encoding="utf8") as streamnamesfile:
    STREAMNAMES = streamnamesfile.read().splitlines()


# Prints the message to Python console
def print_log(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        print('{:s} {:s}: {:s}'.format(datetime.datetime.fromtimestamp(int(msg['date'])).
                                       strftime('%Y-%m-%d %H:%M:%S'), msg['from']['username'], msg['text']))
    elif content_type == 'sticker':
        print('{:s} {:s}: [sticker]'.format(datetime.datetime.fromtimestamp(int(msg['date'])).
                                            strftime('%Y-%m-%d %H:%M:%S'), msg['from']['username']))
    elif content_type == 'photo':
        print('{:s} {:s}: [photo]'.format(datetime.datetime.fromtimestamp(int(msg['date'])).
                                          strftime('%Y-%m-%d %H:%M:%S'), msg['from']['username']))
    elif content_type == 'document':
        print('{:s} {:s}: [document]'.format(datetime.datetime.fromtimestamp(int(msg['date'])).
                                             strftime('%Y-%m-%d %H:%M:%S'), msg['from']['username']))


# Makes the hard decision
def or_choice(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # search for choices in the message
    choicesRegex = re.compile(r'\@?{:s},? (.+) или (.+)'.format(botname))
    mo = choicesRegex.search(msg['text'])
    if mo:
        # sort the choices (also strip the '?')
        choicesList = sorted([mo.group(1).rstrip('?'), mo.group(2).rstrip('?')])
        print(choicesList)
        # form a string containing both choices in lower case
        result = (choicesList[0] + choicesList[1]).lower().encode('utf-8')
        # calculate the hash of the string
        m = hashlib.md5(result)
        m.update(result)
        # and use it in seed
        random.seed(m.hexdigest())
        # make the main choice
        mainChoice = random.randint(0, 1)
        # reset the seed
        random.seed()
        # send the message
        msgsent = bot.sendMessage(chat_id,
                                  '{:s} {:s}!'.format(ofcourseWordList[random.randint(0, len(ofcourseWordList) - 1)],
                                                      choicesList[mainChoice]), None, None, None, msg['message_id'])


# Answers the question
def question(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # search for question in the message
    choicesRegex = re.compile(r'\@?{:s},? (.+)\?'.format(botname))
    mo = choicesRegex.search(msg['text'])
    if mo:
        result = msg['text'].lower().rstrip('?').encode('utf-8')
        m = hashlib.md5()
        m.update(result)
        random.seed(m.hexdigest())
        answer = answerslist[random.randint(0, len(answerslist) - 1)]
        msgsent = bot.sendMessage(chat_id, answer, None, None, None, msg['message_id'])
        if answer == 'НИКОГДА':
            bot.sendSticker(chat_id, 'CAADAgADKQADdy_1D4KPXrwAAcuj6gI')


# Testers
def text_match(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return text == msg['text']
        else:
            return False
    return tester


def text_contains_all(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return all(x in msg['text'] for x in text)
        else:
            return False
    return tester


def text_contains_all_random(text, p):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return all(x in msg['text'] for x in text) and random.random() > p
        else:
            return False
    return tester


def long_text_scan(file):
    def tester(msg):
        for num, item in enumerate(file):
            if item.lower().strip('?!.') in msg['text'].lower().strip('?!.'):
                if not num == len(file) - 1:
                    return num
        return False
    return tester


def is_message_replied_to(name):
    def tester(msg):
        if 'reply_to_message' in msg:
            return msg['reply_to_message']['from']['username'] == name
        else:
            return False
    return tester


def is_message_forwarded_from_random(message_id, p):
    def tester(msg):
        if 'forward_from_chat' in msg:
            return msg['forward_from_chat']['id'] == message_id and random.random() > p
        elif 'forward_from' in msg:
            return msg['forward_from']['id'] == message_id and random.random() > p
        else:
            return False
    return tester


# Handlers	
def send_text(text):
    def handler(msg):
        msgsent = bot.sendMessage(msg['chat']['id'], text)
        return msgsent
    return handler


def send_text_with_reply(text):
    def handler(msg):
        msgsent = bot.sendMessage(msg['chat']['id'], text, None, None, None, msg['message_id'])
        return msgsent
    return handler


def send_sticker(sticker):
    def handler(msg):
        msgsent = bot.sendSticker(msg['chat']['id'], sticker)
        return msgsent
    return handler


def send_sticker_with_reply(sticker):
    def handler(msg):
        msgsent = bot.sendSticker(msg['chat']['id'], sticker, None, msg['message_id'])
        return msgsent
    return handler		


def repeat(msg):
    msgsent = bot.sendMessage(msg['chat']['id'], msg['text'])
    return msgsent


def long_text_post(casinos):
    def handler(msg):
        tester = long_text_scan(casinos)
        num = tester(msg)
        msgsent = bot.sendMessage(msg['chat']['id'], casinos[num + 1], None, None, None, msg['message_id'])
        return msgsent
    return handler


handlers = [
            [is_message_replied_to(botname), send_text_with_reply(replies[random.randint(0, len(replies) - 1)])],
            [is_message_forwarded_from_random(253025219, 0.7), send_text_with_reply(emotions[random.randint(0, len(emotions) - 1)])],
            [is_message_forwarded_from_random(-1001056948674, 0.7), send_text_with_reply(emotions[random.randint(0, len(emotions) - 1)])],
            [text_match('👌'), repeat],
            [text_match('/start'), send_sticker_with_reply(yobas[random.randint(0, len(yobas) - 1)])],
            [text_match('/stop'), send_sticker_with_reply(yobas[random.randint(0, len(yobas) - 1)])],
            [text_contains_all(['в хату']), send_text(good_evening)],
            [text_contains_all([botname, 'или']), or_choice],
            [text_contains_all([botname, '?']), question],
            [text_contains_all([botname, 'здес']), send_text_with_reply(imherelist[random.randint(0, len(imherelist) - 1)])],
            [text_contains_all([botname, 'тут']), send_text_with_reply(imherelist[random.randint(0, len(imherelist) - 1)])],
            [long_text_scan(casinos), long_text_post(casinos)],
            [text_contains_all_random(['аниме'], 0.95), send_text_with_reply(sports[random.randint(0, len(sports) - 1)])],
            [text_contains_all_random(['спорт'], 0.95), send_text_with_reply(sports[random.randint(0, len(sports) - 1)])],
            ]


def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # print(content_type)
    print(msg)

    if (chat_id == group_chat_id or chat_id == admin_chat_id) and (not 'edit_date' in msg):
        for tester, handler in handlers:
            if tester(msg):
                handler(msg)
                break


def check_stream(streams, bot):
    new_streams = []
    for stream in streams:
        new_stream = stream
        try:
            stream_data = requests.get("https://api.twitch.tv/kraken/streams/{:s}?client_id={:s}"\
                                       .format(stream['name'], twitch_client_id))
        except:
            print(stream_data.status_code)
            print(stream_data.text)

        user_info = json.loads(stream_data.text)  # load user data json into user_info
        #print(user_info)
        try:
            stream_name = user_info['stream']['channel']['display_name']
            print('{:s} is online'.format(stream['name']))
            if new_stream['status'] == False:
                msgsent = bot.sendMessage(group_chat_id, 'https://www.twitch.tv/{:s}'.format(stream['name']))
                new_stream['status'] = True
        except TypeError:
            print('{:s} is offline'.format(stream['name']))
            new_stream['status'] = False
        new_streams.append(new_stream)
    threading.Timer(300, check_stream, [streams, bot]).start()
    return new_streams

bot = telepot.Bot(botKey)
bot.message_loop(handle)
print('I am {:s}, nice to meet you!'.format(botname))

streams = []
for STREAMNAME in STREAMNAMES:
    streams.append({'name': STREAMNAME, 'status': None})
streams = check_stream(streams, bot)

while 1:
    time.sleep(10)
