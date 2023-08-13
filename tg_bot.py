import logging
import re
from enum import Enum

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from text_qa_parser import get_questions_and_answer, ask_answer
from redis_db import RedisDB


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('TG_BOT')


class BotActions(Enum):
    CHOOSING = 'TEXT'
    NEW_QUESTION = 'Новый вопрос'
    GIVE_UP = 'Сдаться'
    SCORE = 'Мой счет'


quiz_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет']
]
markup = ReplyKeyboardMarkup(quiz_keyboard, one_time_keyboard=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает ошибки, возникающие во время выполнения бота.

    При возникновении KeyError сообщает пользователю о том, что вопросы закончились.
    Для всех других ошибок отправляет уведомление разработчику.

    Args:
    - update: объект Update, предоставляемый Telegram API.
    - context: контекст, предоставляемый telegram.ext.

    Returns:
    - None
    """
    user_id = context.bot_data['user_id']
    dev_chat_id = context.bot_data['dev_chat_id']
    if isinstance(context.error, KeyError):
        context.bot_data['questions'] = get_questions_and_answer()
        await context.bot.send_message(user_id, f'Вопросы данной викторины закончились! '
                                       f'Чтобы начать новую нажми "Новый вопрос"')
    elif isinstance(context.error, Exception):
        error_class = context.error.__class__.__name__
        error_text = str(context.error)
        error_message = f"{error_class}: {error_text}"
        await context.bot.send_message(dev_chat_id, error_message)


async def start(update, context) -> BotActions:
    """
    Запускает бота и приветствует пользователя.

    Инициирует счетчик вопросов для пользователя в базе данных Redis и
    отправляет приветственное сообщение.

    Args:
    - update: объект Update, предоставляемый Telegram API.
    - context: контекст, предоставляемый telegram.ext.

    Returns:
    - BotActions.CHOOSING: следующее состояние бота.
    """
    redis = context.bot_data['redis']
    user = update.effective_user
    context.bot_data['user_id'] = user.id
    context.bot_data['questions'] = get_questions_and_answer()
    redis.r.hset(user.id, 'question_counter', 0)
    await update.message.reply_text(
        rf'Привет {user.first_name}! Я бот для викторины!',
        reply_markup=markup,
    )

    return BotActions.CHOOSING


async def ask_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    """
    Задает пользователю новый вопрос из викторины.
    """
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id
    question_num = redis.increment_counter(questions, user_id)
    question = redis.get_question(questions, user_id, question_num)

    logger.info(f"Asked question number {question_num} to user {user_id}")

    await update.message.reply_text(question)
    return BotActions.CHOOSING


async def handle_give_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    """
    Обрабатывает действие пользователя, чтобы отказаться от вопроса.
    """
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id

    # Try to get answer only once
    answer = ask_answer(redis, user_id, questions)

    if answer:
        await update.message.reply_text(f'Правильный ответ: {answer} \n'
                                        f'Чтобы продолжить нажми "Новый вопрос"')
    else:
        await context.bot.send_message(user_id, f'Вопросы данной викторины закончились! '
                                                f'Чтобы начать новую нажми "Новый вопрос"')
    logger.info(f"User {user_id} gave up on the question.")
    return BotActions.CHOOSING


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    """
    Сравнивает ответ пользователя с правильным ответом.
    """
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id

    # Try to get answer only once
    correct_answer = ask_answer(redis, user_id, questions)
    given_answer = update.message.text.lower()
    correct_answer = re.sub(r'( \(.+\))|\.$', '', correct_answer)

    if given_answer == correct_answer.lower():
        await update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"')
        logger.info(f"User {user_id} answered correctly.")
    else:
        await update.message.reply_text('Не верно, попробуй еще!')
        logger.info(f"User {user_id} answered incorrectly.")

    return BotActions.CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменяет и завершает разговор.
    """
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        'Пока! Надеюсь, мы ещё сыграем с тобой в викторину! Для начала игры нажми /start'
    )
    return ConversationHandler.END


def main() -> None:
    env = Env()
    env.read_env()
    tg_bot_api_key = env.str('TG_BOT_API_KEY')
    redis_host = env.str('REDIS_HOST')
    redis_port = env.int('REDIS_PORT')
    redis_db = env.int('REDIS_DB')
    redis_username = env.str('REDIS_USERNAME')
    redis_password = env.str('REDIS_PASSWORD')
    redis = RedisDB(redis_host, redis_port, redis_db, redis_username, redis_password)
    application = Application.builder().token(tg_bot_api_key).build()
    application.bot_data['redis'] = redis
    application.bot_data['dev_chat_id'] = env.int('DEVELOPER_CHAT_ID')

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            BotActions.CHOOSING: [
                MessageHandler(filters.Regex(f"^{BotActions.NEW_QUESTION.value}$"), ask_new_question),
                MessageHandler(filters.Regex(f"^{BotActions.GIVE_UP.value}$"), handle_give_up),
                MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()