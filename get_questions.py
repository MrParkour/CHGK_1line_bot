import requests
from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.is_question = False
        self.questions = []
        self.is_answer = False
        self.answers = []

    def handle_data(self, data):
        if 'Вопрос ' in data:
            self.is_question = True
        elif self.is_question:
            self.questions.append(data.replace('\n', ' '))
            self.is_question = False
        elif 'Ответ:' in data:
            self.is_answer = True
        elif self.is_answer:
            self.answers.append(data)
            self.is_answer = False
        else:
            self.is_question = False
            self.is_answer = False


def refind_question(level):
    responce = requests.get(
        f'https://db.chgk.info/random/types1/complexity{level}/1334519980/limit{1}').text.replace('</br>',
                                                                                                  '').replace(
        '<br>', '').replace('<br/>', '').replace('<br />', '')
    parser = MyHTMLParser()
    parser.feed(responce)
    return parser.questions[0], parser.answers[0]


def find_questions(num, level):
    complexity = {"очень легко": 1, "легко": 2, "средне": 3, "сложно": 4, "очень сложно": 5}
    if level not in complexity.keys():
        level = 'средне'
    responce = requests.get(
        f'https://db.chgk.info/random/types1/complexity{complexity[level]}/1334519980/limit{num}').text.replace('</br>',
                                                                                                                '').replace(
        '<br>', '').replace('<br/>', '').replace('<br />', '')
    parser = MyHTMLParser()
    parser.feed(responce)
    ans = {}
    for k, x in zip(parser.questions, parser.answers):
        if k != ' ':
            ans[k] = x
        else:
            a, b = refind_question(level)
            while a == ' ':
                a, b = refind_question(level)
            ans[a] = b
    parser.close()
    return ans
