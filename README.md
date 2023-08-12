# Викторина-бот для TG и VK

Бот, который предоставляет пользователю случайные вопросы из набора текстовых файлов и проверяет ответы на эти вопросы.

Пример:

![Телеграм бот](https://dvmn.org/filer/canonical/1569215494/324/)

## Основные функции:

- Чтение вопросов из случайного текстового файла в директории.
- Интеграция с TG API и VK API для отправки вопросов и приема ответов.
- Логирование ошибок и интеграция с Telegram для отправки уведомлений об ошибках.

## Установка и настройка:

1. Клонируйте репозиторий на свой локальный компьютер. 

```bash
$ git clone git@github.com:PavelKolotov/Quiz_bot.git
```

2. Установите виртуальное окружение

```bash
$ python3 -m venv env
```
В папке с проектом 

```bash
$ source env/bin/activate
```
3. Установите необходимые библиотеки, используя `pip install -r requirements.txt` (предполагается, что вы создадите файл с этим именем и добавите в него все необходимые библиотеки).

4. Настройте переменные окружения или файл `.env` с ключами и настройками для VK API, Telegram и Redis.
Доступные переменные:
- `TG_BOT_API_KEY=6601611393:AAHt6NXg...` - API ключ, который вы получаете при создании бота в Telegram
- `VK_API_KEY=vk1.a.9py4--kkSUgTo8u...` - API ключ, который вы получаете при создании группы в ВКонтакте
- `REDIS_HOST=` - host: Сервер Redis
- `REDIS_PORT=` - Порт
- `REDIS_DB=` - Номер базы данных
- `REDIS_USERNAME=` - Имя пользователя
- `REDIS_PASSWORD=` - Пароль
- `DEVELOPER_CHAT_ID=` - чат ИД разработчика для отправки уведомлений об ошибках.
- `QUESTIONS_PATH=` - путь к файлам с вопросами

5. Поместите текстовые файлы с вопросами и ответами в папку `quiz-questions` (или измените путь в соответствии с вашими настройками).

## Использование:

Запустите главные файл проекта:

- телеграм бот
```bash
$ python tg_bot.py
```
- бот ВКонтакте
```bash
$ python vk_bot.py
```

После этого бот начнет слушать новые сообщения в TG и VK, реагировать на команды.

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).