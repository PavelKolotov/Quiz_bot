import os
import random
import re


def get_questions_from_multiple_files(file_list):
    """
    Извлекает вопросы и ответы из списка файлов.

    :param file_list: Список путей к текстовым файлам
    :return: Словарь с вопросами и ответами или пустой словарь в случае ошибки
    """
    questions = {}
    question_number = 1

    for file_path in file_list:
        with open(file_path, 'r', encoding='koi8-r') as file:
            content = file.read()
            if not content:
                continue

            pattern = r'Вопрос (\d+):\n(.*?)\nОтвет:\n(.*?)\n'
            for match in re.finditer(pattern, content, re.DOTALL):
                num, question, answer = match.groups()
                questions[question_number] = {'q': question.strip(), 'a': answer.strip()}
                question_number += 1
    return questions


def get_random_files_from_directory(path, num_files):
    """
    Выбирает случайные файлы из указанной директории.

    :param path: Путь к директории с файлами
    :param num_files: Количество случайных файлов для выбора
    :return: Список путей к случайным файлам
    """
    files = [file for file in os.listdir(path) if file.endswith('.txt')]
    random_files = random.sample(files, num_files)
    return [os.path.join(path, file) for file in random_files]


def get_answer(redis, user_id, questions):
    """
    Извлекает ответ на текущий вопрос из Redis для указанного пользователя.

    :param redis: Экземпляр RedisDB
    :param user_id: ID пользователя
    :param questions: Словарь с вопросами и ответами
    :return: Текст ответа или False в случае ошибки
    """
    question_num = int(redis.r.hget(user_id, 'question_counter'))
    return redis.get_answer(questions, user_id, question_num)

