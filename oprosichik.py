import telebot 
from telebot import types
from loguru import logger
import db
import time
from logtail import LogtailHandler
Logtailhandler = LogtailHandler("token")
#logger.remove()
#logger.add("log.log",level="DEBUG",compression="zip",rotation="1 hour",retention="1 week")
#logger.add("war.log",level="WARNING",rotation="1 hour",delay=True)
logger.add(Logtailhandler)

bot = telebot.TeleBot("token")
temp = {}

logger.info("Экземпляр бота создан")

m = types.Message

@bot.message_handler(commands=["start"])
def start(msg:m):
    logger.info(f"ПОльзователь {msg.chat.id} нажал на /start")
    old = db.db.s.get(db.Tablicha,msg.chat.id)
    if not old:
        user = db.Tablicha(id = msg.chat.id,name = msg.from_user.full_name,answers = None,admin = False)
        db.db.merge(user)
        db.db.commit()
    bot.send_message( msg.chat.id, "пройти опрос - /letsgo")
@bot.message_handler(commands=["letsgo"])
def go(msg:m):
    question = check_question()
    id = []
    kb = telebot.types.ReplyKeyboardMarkup(True,False)
    for q in question:
        id.append(q[0])
        kb.row(str(q[0]))
    text = "выбери опрос:\m"
    for q in question:
        text += telebot.formatting.hbold(F"номер {q[0]}. {q[1]}\n")
    bot.send_message(msg.chat.id,text,parse_mode="HTML",reply_markup=kb)
    bot.register_next_step_handler(msg,first_question,id)
def first_question(msg:m,ids):
    if not msg.text.isnumeric():
            logger.warning(f"Пользователь {msg.chat.id} написал не тот номер")
            bot.send_message(msg.chat.id,"такого списка не существует")
            adminpanel(msg)
            return
    if int(msg.text) not in ids:
            logger.warning(f"Пользователь {msg.chat.id} выбрал список несуществующих вопросов")
            bot.send_message(msg.chat.id,"такого списка вопросов не существует")
            adminpanel(msg)
            return
    temp[msg.chat.id] = {"list":msg.text,"quare":0,"answers":[]}
    logger.info(F"пользователь {msg.chat.id} инцилизирвал {temp[msg.chat.id]}")
    questions = db.db.s.get(db.Questions,int(msg.text)).question
    bot.send_message(msg.chat.id,questions[0])
    bot.register_next_step_handler(msg,next_question,questions)
def next_question(msg:m,questions):
    global temp
    temp[msg.chat.id]["answers"].append(msg.text)
    logger.info(f"пользователь {msg.chat.id} ответил на вопрос №{temp[msg.chat.id]["queue"]} списка №{temp[msg.chat.id]["list"]}")
    if temp[msg.chat.id]["queue"] == len(questions) -1:
        bot.send_message("спасибо за ответы!")
        logger.success(f"Пользователь {msg.chat.id} завершил опрос")
        save_client(msg)
        return
    temp[msg.chat.id]["queue"] += 1
    question = questions[temp[msg.chat.id]["queue"]]
    bot.send_message(msg.chat.id,question)
    bot.register_next_step_handler(msg, next_question,questions)


def save_client(msg:m):
    user = db.db.s.get(db.Tablicha,msg.chat.id)
    if user.answers is None:
        answers = [temp[msg.chat.id]["answers"]]
    else:
        answers = user.answers
        answers.append(temp[msg.chat.id]["answers"])
    db.db.s.query(db.Tablicha).filter(db.Tablicha.id == msg.chat.id).update({"answers":answers})
    db.db.commit()


def write(msg:m):
    data = db.Questions(id = 1,name = "ананас",question = ["Твоя любимая погода?","какой у тебя знак задиака?"])
    db.db.merge(data)
    db.db.commit()
    logger.info(F"админ {msg.chat.id} записал вопросы в таблицу {data.id}")
@bot.message_handler(commands=["admin"])
def admin(msg:m):
    user = db.db.s.get(db.Tablicha,msg.chat.id)
    if user.admin:
        logger.info(f"админ {msg.chat.id} зашел в меню администратора")
        adminpanel(msg)
    else:
        logger.warning(f"user {msg.chat.id} пытается зайди в админ панель")
        start(msg)

def adminpanel(msg:m):
    kb = telebot.types.ReplyKeyboardMarkup(True,False)
    kb.row("Посмотреть список вопросов")
    kb.row("Удалить список вопросов","Добавить список вопросов")
    bot.send_message(msg.chat.id,"Выбери действие",reply_markup=kb)
    bot.register_next_step_handler(msg,adminpanelhandler)
def adminpanelhandler(msg:m):
    if msg.text.startswith("Посмотреть"):
        question = check_question()
        bot.send_message(msg.chat.id,question_format(question),parse_mode="HTML")
    elif msg.text.startswith("Удалить"):
        delete_questuion(msg)
    elif msg.text.startswith("Добавить"):
        ask_question(msg)
    else:
        adminpanel(msg)
    
@logger.catch    
def check_question():
    questions = []
    data = db.db.s.query(db.Questions)
    for d in data:
        questions.append([d.id,d.name,d.question])
    logger.success("Все вопросы успешно прочитаны")
    return questions

@logger.catch
def question_format(questions):
    text = "списки вопросов:\n\n"
    for qlist in questions:
        text += F"Список №{qlist[0]}\n"
        text +=telebot.formatting.hbold(qlist[1]) + "\n"
        text += "вопросы:\n"
        for n,q in enumerate(qlist[2]):
            text += f"Вопрос №{n + 1}. {q}\n"
        text += "\n"
    logger.info("Строчка отформантированна")
    return text
@logger.catch
def delete_questuion(msg:m):
    q = check_question(msg)
    if not q:
        bot.send_message(msg.chat.id,"вопросов нету")
        adminpanel(msg)
        return
    id = []
    kb = telebot.types.ReplyKeyboardMarkup(True,False)
    for question in q:
        id.append(question[0])
        kb.row(question[0])
    text = f"какой список удалить?:\n"
    for question in q:
        text += telebot.formatting.hbold(f"номер {question[0]}. {question[1]}\n")
    bot.send_message(msg.chat.id,text,parse_mode="HTML",reply_markup=kb)
    bot.register_next_step_handler(msg,delete_question_handler,id)

def delete_question_handler(msg:m,ids):
    if not msg.text.isnumeric():
        logger.warning(f"Админ {msg.chat.id} написал не тот номер")
        bot.send_message(msg.chat.id,"такого списка не существует")
        adminpanel(msg)
        return
    if int(msg.text) not in ids:
        logger.warning(f"админ {msg.chat.id} выбрал список несуществующих вопросов")
        bot.send_message(msg.chat.id,"такого списка вопросов не существует")
        adminpanel(msg)
        return
    kb = telebot.types.ReplyKeyboardMarkup(True,False)
    kb.row("отменить")
    kb.row("удалить")
    bot.send_message(msg.chat.id,f"вы точно хотите удалить список №{msg.text}")
@logger.catch
def delete(msg:m,num):
    if msg.text == "удалить":
        db.db.s.query(db.Questions).filter(db.Questions.id == num).delete()
        db.db.commit()
        bot.send_message(msg.chat.id,f"Список {msg.text} успешно удален")
        logger.success(f"Список {msg.text} успешно удален")
    else:
        bot.send_message("удаление отменено")
    adminpanel(msg)

@logger.catch
def ask_question(msg:m):
    global temp
    temp[msg.chat.id] = []
    bot.send_message(msg.chat.id,"введи свой первый вопрос")
    bot.register_next_step_handler(msg,ask_next_question)
def ask_next_question(msg:m):
    global temp
    if msg.text != "все":  
        temp[msg.chat.id].append(msg.text)
        bot.send_message(msg.chat,id,"напишите сделующий вопрос")
        bot.register_next_step_handler(msg,ask_next_question)
    else:
        logger.info(f"админ {msg.chat.id} создал новый список")
        bot.send_message(msg.chat.id,"Создайте короткое имя")
        bot.register_next_step_handler(msg,add_new_list)
def add_new_list(msg:m):
    question = check_question()
    id = []
    for q in question:
        id.append(q[0])
    num = max(id) + 1
    new = db.Questions(id=num,name = msg.text,question = temp(msg.chat.id)) 
    db.db.merge(new)
    db.db.commit()
    logger.success(f"Админ {msg.chat.id} создал новый список №{num}")
    bot.send_message(msg.chat.id,"список успешно создан")
    time.sleep(1)
    adminpanel(msg)


    
    
    




bot.infinity_polling()