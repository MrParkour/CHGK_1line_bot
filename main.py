import asyncio
import logging
from aiogram import Bot, Dispatcher, types
import get_questions
import random
import background
import datetime
import sqlite3
from config import API_TOKEN

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
users = []

con = sqlite3.connect("leaderboard.sqlite")
cur = con.cursor()


class User:
    def __init__(self, id):
        self.answer = ''
        self.score = 0
        self.is_run = True
        self.is_answer = False
        self.id = id
        self.is_count_enter = False
        self.is_complexity_enter = False
        self.count_of_questions = 0
        self.complexity = ''
        self.is_game_started = False

    def incriment_db_column(self, column):
        sql_req = f"SELECT {column} FROM scores WHERE id = {self.id.id}"
        q = cur.execute(sql_req).fetchone()[0]
        cur.execute(f"UPDATE scores SET {column} = {1 + q} WHERE id = {self.id.id}")
        con.commit()

    def regist(self):
        if not cur.execute(f'Select * from scores where id = {self.id.id}').fetchall():
            cur.execute(f"INSERT INTO scores(id, name, questCount, correctAns) VALUES({self.id.id}, {self.id.title}, 0, 0)")
            con.commit()

    async def send_stats(self, message: types.Message):
        result = cur.execute(f"SELECT * FROM scores WHERE id == {self.id.id}").fetchall()[0]
        command_name = result[1]
        questions = result[2]
        answ_questions = result[3]
        if questions != 0:
            await message.answer(
                f"Из заданных <b>{questions}</b> вопросов командой <u>{command_name}</u> взято <b>{answ_questions}</b>.\nПроцент взятия - <b>{round(100 * answ_questions / questions)}%</b>", parse_mode='HTML')
        else:
            await message.answer(
                f"Вы ещё не провели ни одной игры!")


def user_from_chatId(chatId):
    for k in users:
        if k.id == chatId:
            return k
    return False

@dp.message_handler(commands="stats")
async def start_stats(message: types.Message):
    u = user_from_chatId(message.chat)
    if u:
       await u.send_stats(message)
    else:
        await message.answer('Для отсчёта статистики проведите хотя бы одну игру!')

@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    users.append(User(message.from_user))
    with open('users.txt', 'r') as f:
        text = f.read()
    with open('users.txt', 'w') as f:
        f.write(text + f'\n{message.from_user} {datetime.datetime.now()}')

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Играть одному", "Играть в команде"]
    keyboard.add(*buttons)

    await message.answer(
        'Здравствуйте! Это бот для тренировок по игре Что? Где? Когда?\nПоиграем?',
        reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Остановить")
async def cmd_break(message: types.Message):
    u = user_from_chatId(message.from_user)
    if u:
        u.is_run = False


@dp.message_handler(lambda message: message.text == "Играть одному" or message.text == "Играть ещё")
async def cmd_play(message: types.Message):
    with open('sessionLog.txt', 'r') as f:
        text = f.read()
    with open('sessionLog.txt', 'w') as f:
        f.write(text + f'\n{message.from_user}')
    await message.answer('Сколько вопросов вы хотите разыграть? (не более 20)',
                         reply_markup=types.ReplyKeyboardRemove())
    if not user_from_chatId(message.from_user):
        users.append(User(message.from_user))
    user_from_chatId(message.from_user).is_count_enter = True


@dp.message_handler(lambda message: message.text == "Играть в команде")
async def cmd_break(message: types.Message):
    await message.answer(
        'Для того, чтобы играть в команде:\n1) <b>Добавьте</b> этого бота в телеграм беседу вашей команды\n'
        '2)Отправьте команду <b>/start_game</b>\n3)Чтобы ответить на вопрос, наберите команду <b>/answer *ваш ответ*</b> (например: /answer Пушкин)\n*рекомендуем отправлять ответ только <b>капитану</b>\n*обычные сообщения <b>без</b> ключевого слова /answer используйте для обсуждения, бот их не принимает\n'
        '4)Игра будет вестись до <b>6</b> правильных или неправильных ответов', parse_mode='HTML')


@dp.message_handler(commands="start_game")
async def command_game(message: types.Message):
    u = user_from_chatId(message.chat)
    if u:
        user = u
    else:
        user = User(message.chat)
        users.append(user)
        user.regist()

    if not user.is_game_started:
        user.is_game_started = True
        score = 0
        dict_quests = get_questions.find_questions(12, 'легко')
        for k, x in enumerate(dict_quests):
            if score == 6 or k - score == 6:
                break
            user.incriment_db_column('questCount')
            await message.answer(f'<b>Вопрос {k + 1}</b>: {x}', parse_mode='HTML')
            timer = await message.answer('Время')
            for j in range(6):
                await timer.edit_text(f'Осталось <b>{60 - j * 10}</b> секунд...', parse_mode="HTML")
                if user.answer:
                    break
                else:
                    if j == 3:
                        await message.answer('Осталось <b>30</b> секунд!', parse_mode="HTML")
                    elif j == 5:
                        await message.answer('Осталось <b>10</b> секунд!', parse_mode="HTML")
                await asyncio.sleep(10)

            if not user.answer:
                await message.answer('Пару секунд для записи ответа...')
                await asyncio.sleep(5)

            if user.answer.lower() == dict_quests[x].lower().rstrip('.').lstrip(' '):
                await message.answer(f'<b>Правильно!</b> Команда знатоков получает балл', parse_mode="HTML")
                score += 1
                user.incriment_db_column('correctAns')
                user.answer = ''
            else:
                await message.answer(f'Неверно.\n<b>Ответ: {dict_quests[x]}</b>',
                                     parse_mode="HTML")
                user.answer = ''
            await message.answer(f'<u>Счёт</u> <b>{score}</b>:<b>{k - score + 1}</b>', parse_mode='HTML')

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["/start_game", '/stats']
        keyboard.add(*buttons)

        if score == 6:
            await message.answer(f'Победа знатоков!', reply_markup=keyboard)
        elif score == 5:
            await message.answer(f'А победа была так близко!', reply_markup=keyboard)
        elif score == 3:
            await message.answer(f'Неплохой результат для такой сложности!', reply_markup=keyboard)
        elif score == 0:
            await message.answer(f'Вам стоит тренироваться ещё!', reply_markup=keyboard)
        else:
            await message.answer(f'Поражение команды знатоков!', reply_markup=keyboard)
        user.is_game_started = False
    else:
        await message.answer('Игра уже начата!')


@dp.message_handler(commands="answer")
async def command_game(message: types.Message):
    user = user_from_chatId(message.chat)
    user.answer = message.text[8:]


async def cmd_questions_request(message: types.Message, user: User):
    user.score = 0
    dict_quests = get_questions.find_questions(user.count_of_questions, user.complexity)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Остановить"]
    keyboard.add(*buttons)

    quest_phrases = ['Отправьте ваш ответ', 'Отправьте ответ через минуту', 'Ваш ответ...', 'Ждём ваш ответ']
    incor_phrases = ['Неверно', 'К сожалению нет', 'Мимо', 'Близко, но нет', 'И это неправильно']
    cor_phrases = ['Это правильный ответ', 'И вы получаете балл!', 'Совершенно правильно', 'Именно так!', 'Ну конечно!']
    k = 0
    for k, x in enumerate(dict_quests):
        if user.is_run:
            await message.answer(f'<b>Вопрос {k + 1}</b>: {x}\n{random.choice(quest_phrases)}',
                                 reply_markup=keyboard, parse_mode='HTML')
            timer = await message.answer('Время')
            user.is_answer = True
            for j in range(60):
                await timer.edit_text(f'Осталось <b>{60 - j}</b> секунд...', parse_mode="HTML")
                if user.answer or not user.is_run:
                    break
                await asyncio.sleep(1)

            if user.answer.lower() == dict_quests[x].lower().rstrip('.').lstrip(' '):
                await message.answer(f'{random.choice(cor_phrases)}')
                user.answer = ''
                user.score += 1
            else:
                await message.answer(f'{random.choice(incor_phrases)}.\n<b>Ответ: {dict_quests[x]}</b>',
                                     parse_mode="HTML")
                user.answer = ''
        else:
            user.is_run = True
            break
    else:
        k += 1
    user.is_answer = False
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Играть ещё", "Играть в команде"]
    keyboard.add(*buttons)
    await message.answer(f'Ваш результат <b>{user.score}</b> из <b>{k}</b>', parse_mode="HTML",
                         reply_markup=keyboard)


@dp.message_handler()
async def cmd_answer_processing(message: types.Message):
    user = user_from_chatId(message.from_user)
    if user:
        if user.is_answer:
            user.answer = message.text
            user.is_answer = False
        elif user.is_count_enter:
            user.is_count_enter = False
            num = message.text
            if num.isdigit():
                if int(num) <= 20:
                    user.count_of_questions = num
                else:
                    await message.answer(f'Слишком большое число! Будет отправлено 20 вопросов')
                    num = 20
            else:
                user.count_of_questions = 6
            keyboard = types.ReplyKeyboardMarkup()
            buttons = ["очень легко", "легко", "средне", "сложно", "очень сложно"]
            keyboard.add(*buttons)

            await message.answer('Выберите сложность вопросов', reply_markup=keyboard)
            user.is_complexity_enter = True
        elif user.is_complexity_enter:
            user.is_complexity_enter = False
            user.complexity = message.text
            await cmd_questions_request(message, user)
    else:
        if message.chat not in [x.id for x in users]:
            await cmd_start(message)


async def main():
    background.keep_alive()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
