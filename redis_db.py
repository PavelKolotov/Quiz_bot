import redis


class RedisDB:
    def __init__(self, host, port, db, username, password):
        self.r = redis.Redis(host=host, port=port, db=db, username=username, password=password)

    def get_question(self, questions, user_id, question_num):
        question = questions[f'{question_num}']['q']
        self.r.hset(user_id, f'q:{question_num}', question)
        return question

    def get_answer(self, questions, user_id, question_num):
        answer = questions[f'{question_num}']['a']
        self.r.hset(user_id, f'a:{question_num}', answer)
        return answer

    def increment_counter(self, questions, user_id):
        if int(self.r.hget(user_id, 'question_counter')) < len(questions):
            question_num = self.r.hincrby(user_id, 'question_counter', 1)
        else:
            question_num = self.r.hset(user_id, 'question_counter', 0)
        return question_num

