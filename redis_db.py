import redis


class RedisDB:
    """
    Класс для работы с базой данных Redis.

    Предоставляет методы для сохранения и извлечения вопросов и ответов викторины.
    """

    def __init__(self, host, port, db, username, password):
        """
        Инициализация подключения к базе данных Redis.

        :param host: Сервер Redis
        :param port: Порт
        :param db: Номер базы данных
        :param username: Имя пользователя
        :param password: Пароль
        """
        self.r = redis.Redis(host=host, port=port, db=db, username=username, password=password)

    def get_question(self, questions, user_id, question_num):
        """
        Извлечение вопроса из списка и сохранение его в Redis.

        :param questions: Список вопросов
        :param user_id: ID пользователя
        :param question_num: Номер вопроса
        :return: Текст вопроса
        """
        question = questions[question_num]['q']
        self.r.hset(user_id, f'q:{question_num}', question)
        return question

    def get_answer(self, questions, user_id, question_num):
        """
        Извлечение ответа из списка и сохранение его в Redis.

        :param questions: Список вопросов
        :param user_id: ID пользователя
        :param question_num: Номер вопроса
        :return: Текст ответа
        """
        answer = questions[question_num]['a']
        self.r.hset(user_id, f'a:{question_num}', answer)
        return answer

    def increment_counter(self, questions, user_id):
        """
        Увеличение счетчика вопросов для пользователя.

        Если счетчик достиг максимального значения, он сбрасывается.

        :param questions: Список вопросов
        :param user_id: ID пользователя
        :return: Значение счетчика после увеличения
        """
        if int(self.r.hget(user_id, 'question_counter')) < len(questions) - 1:
            question_num = self.r.hincrby(user_id, 'question_counter', 1)
        else:
            question_num = self.r.hincrby(user_id, 'question_counter', 1)
            self.r.hset(user_id, 'question_counter', 0)
        return question_num
