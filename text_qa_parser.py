import os
import random
import re


def open_random_qitz_questions(path):
    files = [file for file in os.listdir(path) if file.endswith('.txt')]
    if files:
        random_file = random.choice(files)
        file_path = os.path.join(path, random_file)
        try:
            with open(file_path, 'r', encoding='koi8-r') as file:
                content = file.read()
                return content
        except IOError:
            print('Ошибка при открытии файла.')
    else:
        print('В папке не найдено ни одного текстового файла (.txt)')


def get_questions_and_answer():
    questions_text = open_random_qitz_questions('quiz-questions')
    pattern = r'Вопрос (\d+):\n(.*?)\nОтвет:\n(.*?)\n'
    questions = {}

    for match in re.finditer(pattern, questions_text, re.DOTALL):
        num, question, answer = match.groups()
        questions[f'question {num}'] = {'q': question.strip(), 'a': answer.strip()}

    return questions

