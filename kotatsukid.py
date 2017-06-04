#! /usr/bin/env python3

import datetime
import hashlib
import json
import logging
import random
import re
import requests
import time
import threading

import telepot

import config


def open_textfile_and_splitlines(path):
    with open(path, 'r', encoding='utf8') as file:
        result = file.read().splitlines()
    return result


def remove_spec_char_and_normalize(text):
    result = ''.join(e for e in text if e.isalnum())
    return result.lower().strip('?!.').replace('ё', 'е')


# Testers
def text_match(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return text == msg['text']
        return False
    return tester


def contains_all(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return all(x in msg['text'] for x in text)
        return False
    return tester


def contains_any(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return any(x in msg['text'] for x in text)
        return False
    return tester


def contains_word(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            for word in text:
                mo = (re.compile(r'\b{:s}\b'.format(re.escape(word)), re.IGNORECASE)
                      .search(msg['text']))
                if mo:
                    return True
        return False
    return tester


def contains_word_on_the_beginning(text):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            for word in text:
                mo = (re.compile(r'\b{:s}'.format(word), re.IGNORECASE)
                      .search(msg['text']))
                if mo:
                    return True
        return False
    return tester


def contains_all_with_probability(text, p):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            return all(x in msg['text'] for x in text) and random.random() > p
        return False
    return tester


def scan_long_text(file):
    def tester(msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            for num, item in enumerate(file):
                print(remove_spec_char_and_normalize(item))
                print(remove_spec_char_and_normalize(msg['text']))
                if (
                        not num == len(file) - 1 and
                        (remove_spec_char_and_normalize(item) in
                         remove_spec_char_and_normalize(msg['text']))
                ):
                    return num + 1
        return False
    return tester


def replied_to(name):
    def tester(msg):
        if ('reply_to_message' in msg and
                'username' in msg['reply_to_message']['from']):
            return msg['reply_to_message']['from']['username'] == name
        return False
    return tester


def forwarded_from(message_id):
    def tester(msg):
        if 'forward_from_chat' in msg:
            return msg['forward_from_chat']['id'] == message_id
        elif 'forward_from' in msg:
            return msg['forward_from']['id'] == message_id
        return False
    return tester


# Handlers
def make_or_choice(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # search for choices in the message
    choicesRegex = re.compile(r'\@?{:s},? (.+) или (.+)'.format(config.botname))
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
        m = md5(result)
        m.update(result)
        # and use it in seed
        random.seed(m.hexdigest())
        # make the main choice
        mainChoice = random.randint(0, 1)
        # reset the seed
        random.seed()
        # send the message
        msgsent = bot.sendMessage(
            chat_id,
            '{:s} {:s}!'.format(random.choice(ofcourseWordList),
            choicesList[mainChoice]),
            parse_mode=None,
            disable_web_page_preview=None,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
        )
    return msgsent


def answer_the_quesion(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    # search for question in the message
    choicesRegex = re.compile(r'\@?{:s},? (.+)\?'.format(config.botname))
    mo = choicesRegex.search(msg['text'])
    if mo:
        result = msg['text'].lower().rstrip('?').encode('utf-8')
        m = hashlib.md5()
        m.update(result)
        random.seed(m.hexdigest())
        answer = random.choice(answerslist)
        msgsent = bot.sendMessage(
            chat_id,
            answer,
            parse_mode=None,
            disable_web_page_preview=None,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
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
            msg['chat']['id'],
            text,
            parse_mode=None,
            disable_web_page_preview=None,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
        )
        return msgsent
    return handler


def send_text_with_reply_with_probability(text, p):
    def handler(msg):
        if random.random() > p:
            msgsent = bot.sendMessage(
                msg['chat']['id'],
                text,
                parse_mode=None,
                disable_web_page_preview=None,
                disable_notification=None,
                reply_to_message_id=msg['message_id']
            )
            return msgsent
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
            msg['chat']['id'],
            sticker,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
        )
        return msgsent
    return handler


def repeat(msg):
    msgsent = bot.sendMessage(msg['chat']['id'], msg['text'])
    return msgsent


def post_long_text(casinos):
    def handler(msg):
        tester = scan_long_text(casinos)
        msgsent = bot.sendMessage(
            msg['chat']['id'],
            casinos[tester(msg)],
            parse_mode=None,
            disable_web_page_preview=None,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
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
            msg['chat']['id'],
            filename,
            caption=None,
            disable_notification=None,
            reply_to_message_id=msg['message_id']
        )
        return msgsent
    return handler


def send_image_with_reply_timer_fact18(filename):
    def handler(msg):
        global lasttime
        time_diff = datetime.datetime.now() - lasttime['Fact18']
        if time_diff.total_seconds() > 3600:
            msgsent = bot.sendPhoto(
                msg['chat']['id'],
                filename,
                caption=None,
                disable_notification=None,
                reply_to_message_id=msg['message_id']
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
                msg['chat']['id'],
                filename,
                caption=None,
                disable_notification=None,
                reply_to_message_id=msg['message_id']
            )
            lasttime['Fact26'] = datetime.datetime.now()
        return msgsent
    return handler


def relay(send_to_chat_id, msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        text = (
              '{:s} {:s}: {:s}'
              .format(datetime.datetime.fromtimestamp(int(msg['date']))
                      .strftime('%Y-%m-%d %H:%M:%S'),
                      msg['from']['first_name'],
                      msg['text'])
        )
        bot.sendMessage(send_to_chat_id, text)
    elif content_type == 'sticker':
        text = (
              '{:s} {:s}:'
              .format(datetime.datetime.fromtimestamp(int(msg['date']))
                      .strftime('%Y-%m-%d %H:%M:%S'),
                      msg['from']['first_name'])
        )
        bot.sendMessage(send_to_chat_id, text)
        bot.sendSticker(send_to_chat_id, msg['sticker']['file_id'])
    elif content_type == 'photo':
        text = (
             '{:s} {:s}:'
             .format(datetime.datetime.fromtimestamp(int(msg['date']))
                     .strftime('%Y-%m-%d %H:%M:%S'),
                     msg['from']['first_name'])
        )
        bot.sendMessage(send_to_chat_id, text)
        bot.sendPhoto(send_to_chat_id, msg['photo'][2]['file_id'])

    elif content_type == 'document':
        text = (
              '{:s} {:s}: [document]'
              .format(datetime.datetime.fromtimestamp(int(msg['date']))
                      .strftime('%Y-%m-%d %H:%M:%S'),
                      msg['from']['first_name'])
        )
        bot.sendMessage(send_to_chat_id, text)


def handle(msg):
    startTime = datetime.datetime.now()
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(msg)

    if ((chat_id == config.group_chat_id or
                 chat_id == config.admin_chat_id) and
                'edit_date' not in msg):
        #relay(config.user_chat_id, msg)
        #relay(config.admin_chat_id, msg)

        handlers = [
            [replied_to(config.botname),
             send_text_with_reply(random.choice(replies)),

            [forwarded_from(config.yumoreski_chat_id_1),
             send_text_with_reply_with_probability(
                 random.choice(emotions), 0.7)],

            [forwarded_from(config.yumoreski_chat_id_2),
             send_text_with_reply_with_probability(
                 random.choice(emotions), 0.7)],

            [text_match('👌'), repeat],
            [text_match('/start'),
             send_sticker_with_reply(random.choice(yobas)],

            [text_match('/stop'),
             send_sticker_with_reply(random.choice(yobas))],

            [contains_all(['в хату']), send_text(good_evening[0])],

            [contains_all([config.botname, 'здес']),
             send_text_with_reply(random.choice(imherelist))],

            [contains_all([config.botname, 'тут']),
             send_text_with_reply(random.choice(imherelist)],

            [contains_all([config.botname, 'или']), make_or_choice],

            [contains_all([config.botname, '?']), answer_the_quesion],

            [scan_long_text(casinos), post_long_text(casinos)],

            [scan_long_text(bears), post_long_text(bears)],

            [contains_all_with_probability([' аниме '], 0.95),
             send_text_with_reply(random.choice(sports)],

            [contains_all_with_probability([' спорт '], 0.95),
             send_text_with_reply(random.choice(sports)],

            [contains_word(fact18),
             send_image_with_reply_timer_fact18(
                 'http://i.imgur.com/CC3dOEH.jpg')],

            [contains_word(fact26),
             send_image_with_reply_timer_fact26(
                 'http://i.imgur.com/qa9SHgv.jpg')],
        ]
        for tester, handler in handlers:
            if tester(msg):
                msgsent = handler(msg)
                break

    print(datetime.datetime.now() - startTime)


def check_stream(stream_list, bot):
    print('Twitch stream check: {:s}'.format(datetime.datetime.now()
          .strftime('%Y-%m-%d %H:%M:%S')))
    new_streams = []
    for stream in stream_list:
        new_stream = stream
        try:
            stream_data = requests.get(
                "https://api.twitch.tv/kraken/streams/{:s}?client_id={:s}"
                .format(stream['name'], config.twitch_client_id)
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
                    config.group_chat_id,
                    'https://www.twitch.tv/{:s}'.format(stream['name'])
                )
                new_stream['status'] = True
        else:
            print('{:s} is offline'.format(stream['name']))
            new_stream['status'] = False
        new_streams.append(new_stream)
    threading.Timer(300, check_stream, [stream_list, bot]).start()
    return new_streams


if __name__ == '__main__':
    emotions = open_textfile_and_splitlines('settings/emotions.txt')
    yobas = open_textfile_and_splitlines('settings/emotions.txt')
    replies = open_textfile_and_splitlines('settings/replies.txt')
    sports = open_textfile_and_splitlines('settings/sports.txt')
    casinos = open_textfile_and_splitlines('settings/casino.txt')
    bears = open_textfile_and_splitlines('settings/bear.txt')
    ofcourseWordList = open_textfile_and_splitlines('settings/ofcourse.txt')
    answerslist = open_textfile_and_splitlines('settings/answers.txt')
    good_evening = open_textfile_and_splitlines('settings/good_evening.txt')
    imherelist = open_textfile_and_splitlines('settings/imhere.txt')
    fact18 = open_textfile_and_splitlines('settings/fact18.txt')
    fact26 = open_textfile_and_splitlines('settings/fact26.txt')

    lasttime = {'Fact18': datetime.datetime(2016, 1, 1, 0, 0, 0, 0),
                'Fact26': datetime.datetime(2016, 1, 1, 0, 0, 0, 0)}

    bot = telepot.Bot(config.botKey)
    bot.message_loop(handle, relax=0.5)
    print('I am {:s}, nice to meet you!'.format(config.botname))

    streams = []
    for stream in config.streamnames:
        streams.append({'name': stream, 'status': None})
    streams = check_stream(streams, bot)

    while 1:
        time.sleep(10)
