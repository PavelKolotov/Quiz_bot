import logging
import re

from environs import Env

import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from telegram_handler import TelegramLoggingHandler

from text_qa_parser import get_questions_and_answer, ask_answer
from redis_db import RedisDB


logger = logging.getLogger('VK_BOT')

NEW_QUESTION = 'Новый вопрос'
GIVE_UP = 'Сдаться'
SCORE = 'Мой счет'


def send_message(user_id, message, keyboard, vk_api):
    vk_api.messages.send(
        peer_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=message,
    )


def main():
    env = Env()
    env.read_env()
    dev_chat_id = env.int('DEVELOPER_CHAT_ID')
    tg_bot_api_key = env.str('TG_BOT_API_KEY')
    vk_api_key = env.str('VK_API_KEY')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    redis_db = env.int('REDIS_DB')
    redis_username = env.str('REDIS_USERNAME')
    redis_password = env.str('REDIS_PASSWORD')
    message = 'Привет! Я бот для викторины!'
    redis = RedisDB(redis_host, redis_port, redis_db, redis_username, redis_password)
    telegram_log_handler = TelegramLoggingHandler(tg_bot_api_key, dev_chat_id)
    logging.basicConfig(
        handlers=[telegram_log_handler],
        level=logging.ERROR,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    vk_session = vk.VkApi(token=vk_api_key)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)
    questions = get_questions_and_answer()

    for event in longpoll.listen():


        answer = ask_answer(redis, event.user_id, questions)
        answer = re.sub(r'( \(.+\))|\.$', '', answer)
        try:
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text != answer:
                    send_message(event.user_id, message, keyboard, vk_api)
                elif event.text == NEW_QUESTION:
                    message = 'asdfsadfkj'
                    send_message(event.user_id, message, keyboard, vk_api)
                elif event.text == GIVE_UP:
                    message = 'asdfsaasdfaasfasfdfkj'
                    send_message(event.user_id, message, keyboard, vk_api)

        except KeyError:
            send_message(event.user_id, message, keyboard, vk_api)
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    main()