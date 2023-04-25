Проект Тelegram бота, Шемчук, Софронов. 
Идея. Онлайн бот для проведения игр Что Где Когда. Пользователь регестрирует по tg никнеймам от 0 до 5 пользователей в команду, автоматически становясь капитаном (он может играть и один). В любое время капитан может начать игру - тогда создаётся чат команды, в котором происходит текстовое обсуждение. Когда участники команды нажали кнопку "начать" у всех в диалоге с ботом появлется первый вопрос и таймер на одну минуту, за которую они должны написать свою версию и отправить её боту. По истечении минуты капитан должен выбрать из всех отправленных в бота версий версий одну. Игра заканчивается при достижении 6 правильных или 6 неправлиьных ответов. 
Технологии. Api telegram, Api сайтов предоставляющих базу вопросов, асинхронное программирование на python, создание и изменение базы данных через python 
Задачи. 
1. Интерфейс управления командой - удаление и добавление игроков 
2. База данных, постоянно обновляющаяся из интернета чтобы избежать повторов вопросов 
3. Процедура сбора вопрсов и выбора правильного ответа 
4. Таймер на решение каждого вопроса