import logging
import re
from enum import Enum

from environs import Env
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

from text_qa_parser import get_questions_and_answer
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


def ask_answer(redis, user_id, questions):
    question_num = int(redis.r.hget(user_id, 'question_counter'))
    answer = redis.get_answer(questions, user_id, question_num)
    return answer


async def start(update, context) -> BotActions:
    redis = context.bot_data['redis']
    user = update.effective_user
    context.bot_data['user_id'] = user.id
    redis.r.hset(user.id, 'question_counter', 0)
    await update.message.reply_text(
        rf'Привет {user.first_name}! Я бот для викторины!',
        reply_markup=markup,
    )

    return BotActions.CHOOSING


async def ask_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id
    question_num = redis.increment_counter(questions, user_id)
    question = redis.get_question(questions, user_id, question_num)
    await update.message.reply_text(question)

    return BotActions.CHOOSING


async def handle_give_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id
    answer = ask_answer(redis, user_id, questions)

    await update.message.reply_text(f'Вот тебе правлиьный ответ: {answer} \n'
                              f'Чтобы продолжить нажми "Новый вопрос"')
    return BotActions.CHOOSING


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> BotActions:
    redis = context.bot_data['redis']
    questions = context.bot_data['questions']
    user_id = update.effective_user.id
    answer = ask_answer(redis, user_id, questions)
    answer = re.sub(r'( \(.+\))|\.$', '', answer)
    if update.message.text.lower() == answer.lower():
        await update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"')
    else:
        await update.message.reply_text('Не верно, попробуй еще!')

    return BotActions.CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        'Пока! Надеюсь, мы ещё сыграем с тобой в викторину!'
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
    questions = get_questions_and_answer()
    application = Application.builder().token(tg_bot_api_key).build()
    application.bot_data['redis'] = redis
    application.bot_data['questions'] = questions
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