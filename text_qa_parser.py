import os
import random
import re

from environs import Env


def open_random_quiz_questions(path):
    """
    Открывает случайный текстовый файл из указанной директории.

    :param path: Путь к директории с текстовыми файлами
    :return: Содержимое выбранного файла или None в случае ошибки или отсутствия содержимого
    """
    try:
        files = [file for file in os.listdir(path) if file.endswith('.txt')]

        if not files:
            print('В папке не найдено ни одного текстового файла (.txt)')
            return

        random_file = random.choice(files)
        file_path = os.path.join(path, random_file)

        with open(file_path, 'r', encoding='koi8-r') as file:
            content = file.read()
            if not content:
                print('Выбранный файл пуст.')
                return
            return content
    except (FileNotFoundError, PermissionError) as e:
        print(f'Ошибка при открытии файла: {e}')


def get_questions_and_answer():
    """
    Извлекает вопросы и ответы из случайного текстового файла из папки 'quiz-questions'.

    :return: Словарь с вопросами и ответами или пустой словарь в случае ошибки
    """
    env = Env()
    env.read_env()
    questions_path = env.str('QUESTIONS_PATH')
    questions_text = open_random_quiz_questions(questions_path)
    if not questions_text:
        return {}

    pattern = r'Вопрос (\d+):\n(.*?)\nОтвет:\n(.*?)\n'
    questions = {}

    for match in re.finditer(pattern, questions_text, re.DOTALL):
        num, question, answer = match.groups()
        questions[f'{num}'] = {'q': question.strip(), 'a': answer.strip()}

    return questions


def ask_answer(redis, user_id, questions):
    """
    Извлекает ответ на текущий вопрос из Redis для указанного пользователя.

    :param redis: Экземпляр RedisDB
    :param user_id: ID пользователя
    :param questions: Словарь с вопросами и ответами
    :return: Текст ответа или False в случае ошибки
    """
    try:
        question_num = int(redis.r.hget(user_id, 'question_counter'))
        return redis.get_answer(questions, user_id, question_num)
    except KeyError:
        return False
