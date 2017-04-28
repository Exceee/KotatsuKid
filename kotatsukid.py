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
from config import *

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

with open('settings/bear.txt', 'r', encoding="utf8") as bearfile:
    bears = bearfile.read().splitlines()

with open('settings/ofcourse.txt', 'r', encoding="utf8") as ofcoursefile:
    ofcourseWordList = ofcoursefile.read().splitlines()

with open('settings/answers.txt', 'r', encoding="utf8") as answersfile:
    answerslist = answersfile.read().splitlines()

with open('settings/good_evening.txt', 'r', encoding="utf8") as eveningfile:
    good_evening = eveningfile.read()

with open('settings/imhere.txt', 'r', encoding="utf8") as imherefile:
    imherelist = imherefile.read().splitlines()

with open('settings/streamnames.txt', 'r', encoding="utf8") as streamnamesfile:
    streamnames = streamnamesfile.read().splitlines()

with open('settings/tema.txt', 'r', encoding="utf8") as temafile:
    temas = temafile.read()

with open('settings/fact18.txt', 'r', encoding="utf8") as fact18file:
    fact18 = fact18file.read().splitlines()

with open('settings/fact26.txt', 'r', encoding="utf8") as fact26file:
    fact26 = fact26file.read().splitlines()

global lasttime
lasttime = {'Fact18': datetime.datetime(2016, 1, 1, 0, 0, 0, 0),
            'Fact26': datetime.datetime(2016, 1, 1, 0, 0, 0, 0)}


def remove_spec_char(text):
    return ''.join(e for e in text if e.isalnum())


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


def text_contains_any(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return any(x in msg['text'] for x in text)
        else:
            return False
    return tester


def text_contains_any_strict(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            for word in text:
                mo = (re.compile(r'\b{:s}\b'.format(word), re.IGNORECASE)
                      .search(msg['text']))
                if mo:
                    return True
            return False
        else:
            return False
    return tester


def text_contains_any_strict_start(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            for word in text:
                mo = (re.compile(r'\b{:s}'.format(word), re.IGNORECASE)
                      .search(msg['text']))
                if mo:
                    return True
            return False
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
        content_type, chat_type, chat_id = telepot.glance(msg)
        for num, item in enumerate(file):
            if (
                    content_type == 'text' and
                    remove_spec_char(item).lower().strip('?!.')
                    .replace('ё', 'е') in
                    remove_spec_char(msg['text']).lower().strip('?!.')
                    .replace('ё', 'е') and
                    not num == len(file) - 1
            ):
                return num + 1
        return False
    return tester


def is_message_replied_to(name):
    def tester(msg):
        if 'reply_to_message' in msg:
            return msg['reply_to_message']['from']['username'] == name
        else:
            return False
    return tester


def is_message_forwarded_from(message_id):
    def tester(msg):
        if 'forward_from_chat' in msg:
            return msg['forward_from_chat']['id'] == message_id
        elif 'forward_from' in msg:
            return msg['forward_from']['id'] == message_id
        else:
            return False
    return tester


# Handlers
def or_choice(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # search for choices in the message
    choicesRegex = re.compile(r'\@?{:s},? (.+) или (.+)'.format(botname))
    mo = choicesRegex.search(msg['text'])
    if mo:
        # sort the choices (also strip the '?')
        choicesList = sorted(
            [mo.group(1).rstrip('?'), mo.group(2).rstrip('?')]
        )
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
        msgsent = bot.sendMessage(
            chat_id, '{:s} {:s}!'
            .format(ofcourseWordList[random.randint(0, len(ofcourseWordList) - 1)],
            choicesList[mainChoice]), None, None, None, msg['message_id']
        )
    return msgsent


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
        msgsent = bot.sendMessage(
            chat_id, answer, None, None, None, msg['message_id']
        )
        if answer == 'НИКОГДА':
            bot.sendSticker(chat_id, 'CAADAgADKQADdy_1D4KPXrwAAcuj6gI')
    return msgsent


def send_text(text):
    def handler(msg):
        msgsent = bot.sendMessage(msg['chat']['id'], text)
        return msgsent
    return handler


def send_text_with_reply(text):
    def handler(msg):
        msgsent = bot.sendMessage(
            msg['chat']['id'], text, None, None, None, msg['message_id']
        )
        return msgsent
    return handler


def send_text_with_reply_random(text, p):
    def handler(msg):
        if random.random() > p:
            msgsent = bot.sendMessage(
                msg['chat']['id'], text, None, None, None, msg['message_id']
            )
            return msgsent
        else:
            return False
    return handler


def send_sticker(sticker):
    def handler(msg):
        msgsent = bot.sendSticker(msg['chat']['id'], sticker)
        return msgsent
    return handler


def send_sticker_with_reply(sticker):
    def handler(msg):
        msgsent = bot.sendSticker(
            msg['chat']['id'], sticker, None, msg['message_id']
        )
        return msgsent
    return handler


def repeat(msg):
    msgsent = bot.sendMessage(msg['chat']['id'], msg['text'])
    return msgsent


def long_text_post(casinos):
    def handler(msg):
        tester = long_text_scan(casinos)
        msgsent = bot.sendMessage(
            msg['chat']['id'], casinos[tester(msg)], None, None, None,
            msg['message_id']
        )
        return msgsent
    return handler


def send_image(filename):
    def handler(msg):
        msgsent = bot.sendPhoto(msg['chat']['id'], filename)
        return msgsent
    return handler


def send_image_with_reply(filename):
    def handler(msg):
        msgsent = bot.sendPhoto(
            msg['chat']['id'], filename, None, None, msg['message_id']
        )
        return msgsent
    return handler


def send_image_with_reply_timer_fact18(filename):
    def handler(msg):
        global lasttime
        time_diff = datetime.datetime.now() - lasttime['Fact18']
        if time_diff.total_seconds() > 3600:
            msgsent = bot.sendPhoto(
                msg['chat']['id'], filename, None, None, msg['message_id']
            )
            lasttime['Fact18'] = datetime.datetime.now()
            return msgsent
    return handler


def send_image_with_reply_timer_fact26(filename):
    def handler(msg):
        global lasttime
        time_diff = datetime.datetime.now() - lasttime['Fact26']
        if time_diff.total_seconds() > 3600:
            msgsent = bot.sendPhoto(
                msg['chat']['id'], filename, None, None, msg['message_id']
            )
            lasttime['Fact26'] = datetime.datetime.now()
        return msgsent
    return handler


def handle(msg):
    startTime = datetime.datetime.now()
    content_type, chat_type, chat_id = telepot.glance(msg)
    # print(content_type)
    print(msg)

    if ((chat_id == group_chat_id or chat_id == admin_chat_id) and
            ('edit_date' not in msg)):
        handlers = [
            [is_message_replied_to(botname),
             send_text_with_reply(
                 replies[random.randint(0, len(replies) - 1)])],

            [is_message_forwarded_from(253025219),
             send_text_with_reply_random(
                 emotions[random.randint(0, len(emotions) - 1)], 0.7)],

            [is_message_forwarded_from(-1001056948674),
             send_text_with_reply_random(
                 emotions[random.randint(0, len(emotions) - 1)], 0.7)],

            [text_match('👌'), repeat],
            [text_match('/start'),
             send_sticker_with_reply(
                 yobas[random.randint(0, len(yobas) - 1)])],

            [text_match('/stop'),
             send_sticker_with_reply(yobas[random.randint(0, len(yobas) - 1)])],

            [text_contains_all(['в хату']), send_text(good_evening)],

            [text_contains_all([botname, 'здес']),
             send_text_with_reply(
                 imherelist[random.randint(0, len(imherelist) - 1)])],

            [text_contains_all([botname, 'тут']),
             send_text_with_reply(
                 imherelist[random.randint(0, len(imherelist) - 1)])],

            [text_contains_all([botname, 'или']), or_choice],

            [text_contains_all([botname, '?']), question],

            [long_text_scan(casinos), long_text_post(casinos)],

            [long_text_scan(bears), long_text_post(bears)],

            [text_contains_all_random([' аниме '], 0.95),
             send_text_with_reply(sports[random.randint(0, len(sports) - 1)])],

            [text_contains_all_random([' спорт '], 0.95),
             send_text_with_reply(sports[random.randint(0, len(sports) - 1)])],

            [text_contains_any_strict_start(['Наваль']),
             send_text_with_reply(temas)],

            [text_contains_any_strict(fact18),
             send_image_with_reply_timer_fact18(
                 'http://i.imgur.com/CC3dOEH.jpg')],

            [text_contains_any_strict(fact26),
             send_image_with_reply_timer_fact26(
                 'http://i.imgur.com/qa9SHgv.jpg')],
        ]
        for tester, handler in handlers:
            if tester(msg):
                msgsent = handler(msg)
                break
    print(datetime.datetime.now() - startTime)


def check_stream(streams, bot):
    print('Twitch stream check: {:s}'.format(datetime.datetime.now()
          .strftime('%Y-%m-%d %H:%M:%S')))
    new_streams = []
    for stream in streams:
        new_stream = stream
        try:
            stream_data = requests.get(
                "https://api.twitch.tv/kraken/streams/{:s}?client_id={:s}"
                .format(stream['name'], twitch_client_id)
            )
        except:
            print(stream_data.status_code)
            print(stream_data.text)

        user_info = json.loads(stream_data.text)
        if user_info['stream']:
            stream_name = user_info['stream']['channel']['display_name']
            print('{:s} is online'.format(stream['name']))
            if new_stream['status'] == False:
                msgsent = bot.sendMessage(
                    group_chat_id,
                    'https://www.twitch.tv/{:s}'.format(stream['name'])
                )
                new_stream['status'] = True
        else:
            print('{:s} is offline'.format(stream['name']))
            new_stream['status'] = False
        new_streams.append(new_stream)
    threading.Timer(300, check_stream, [streams, bot]).start()
    return new_streams

bot = telepot.Bot(botKey)
bot.message_loop(handle)
print('I am {:s}, nice to meet you!'.format(botname))

streams = []
for stream in streamnames:
    streams.append({'name': stream, 'status': None})
streams = check_stream(streams, bot)

while 1:
    time.sleep(10)
