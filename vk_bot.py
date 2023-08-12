import logging
import re

from environs import Env
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from telegram_handler import TelegramLoggingHandler
from text_qa_parser import get_questions_and_answer, ask_answer
from redis_db import RedisDB


logger = logging.getLogger('VK_BOT')


class QuizBot:
    """Бот для проведения викторины в VK."""

    NEW_QUESTION = 'Новый вопрос'
    GIVE_UP = 'Сдаться'
    SCORE = 'Мой счет'
    START_MESSAGE = 'Привет! Я бот для викторины!'
    WRONG_ANSWER_MESSAGE = 'Не верно, попробуй еще!'

    def __init__(self):
        """Инициализация бота и загрузка вопросов."""
        self.questions = get_questions_and_answer()

    def send_message(self, user_id, message, keyboard, vk_api):
        """
        Отправка сообщения пользователю через VK API.

        :param user_id: ID пользователя
        :param message: Текст сообщения
        :param keyboard: Клавиатура
        :param vk_api: VK API
        """
        vk_api.messages.send(
            peer_id=user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message=message,
        )

    def get_next_question(self, redis, user_id):
        """
        Получение следующего вопроса из списка.

        :param redis: Экземпляр Redis
        :param user_id: ID пользователя
        :return: Следующий вопрос
        """
        question_count = len(self.questions)
        current_question_num = int(redis.r.hget(user_id, 'question_counter') or 0)

        if current_question_num >= question_count:
            self.questions = get_questions_and_answer()
            current_question_num = 0
            redis.r.hset(user_id, 'question_counter', current_question_num)

        question_num = current_question_num + 1
        question = redis.get_question(self.questions, user_id, question_num)
        redis.r.hincrby(user_id, 'question_counter', 1)

        return question

    def handle_event(self, event, redis, vk_api, questions, keyboard):
        """
        Обработка входящего события от пользователя.

        :param event: Событие
        :param redis: Экземпляр Redis
        :param vk_api: VK API
        :param questions: Список вопросов
        :param keyboard: Клавиатура
        """
        user_input = event.text
        correct_answer = re.sub(r'( \(.+\))|\.$', '', ask_answer(redis, event.user_id, questions) or '')

        if user_input == self.NEW_QUESTION:
            question = self.get_next_question(redis, event.user_id)
            self.send_message(event.user_id, question, keyboard, vk_api)
        elif user_input == self.GIVE_UP:
            if correct_answer:
                message = f'Правильный ответ: {correct_answer}\nЧтобы продолжить нажми "Новый вопрос"'
            else:
                message = f'Вопросы данной викторины закончились! Чтобы начать новую нажми "Новый вопрос"'
            self.send_message(event.user_id, message, keyboard, vk_api)
        elif user_input.lower() != correct_answer.lower():
            if correct_answer:
                message = self.WRONG_ANSWER_MESSAGE
            else:
                message = self.START_MESSAGE
            self.send_message(event.user_id, message, keyboard, vk_api)
        elif user_input.lower() == correct_answer.lower():
            message = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
            self.send_message(event.user_id, message, keyboard, vk_api)

    def main(self):
        """Основной метод для запуска и работы бота."""
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

        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    self.handle_event(event, redis, vk_api, self.questions, keyboard)
            except Exception as e:
                logger.error(e, exc_info=True)

if __name__ == '__main__':
    bot = QuizBot()
    bot.main()
