import config
import telebot
import requests
from json import JSONEncoder
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

class Coauthor:
    def __init__(self):
        self.name = ''
        self.surname = ''
        self.patronymic = ''

class Application:
    def __init__(self):
        self.id = 0
        self.telegram_id = 0
        self.discord_id = 0
        self.email = ''
        self.phone = ''
        self.name = ''
        self.surname = ''
        self.patronymic = ''
        self.university = ''
        self.student_group = ''
        self.title = ''
        self.adviser = ''
        self.coauthors = []

class ApplicationEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

class MyStates(StatesGroup):
    main_menu = State()
    create_application = State()
    my_applications = State()

user_data = {}

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.TOKEN, state_storage=state_storage)

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    create_button = types.InlineKeyboardButton("Создать", callback_data='create_application')
    list_button = types.InlineKeyboardButton("Список моих заявок", callback_data='list_applications')
    markup.add(create_button, list_button)

    bot.set_state(user_id, MyStates.main_menu)

    bot.send_message(user_id, 'Привет, с чего начнем?', reply_markup=markup)

def show_application(user_id):
    markup = types.InlineKeyboardMarkup()
    post_button = types.InlineKeyboardButton("Отправить заявку", callback_data='post_application')
    delete_button = types.InlineKeyboardButton("Удалить черновик", callback_data='delete_data')
    add_coauthor_button = types.InlineKeyboardButton("Добавить соавтора", callback_data='add_coauthor')
    rm_coauthor_button = types.InlineKeyboardButton("Удалить соавтора", callback_data='rm_coauthor')
    back_to_main_manu_button = types.InlineKeyboardButton("В главное меню", callback_data='main_menu')
    markup.add(post_button, delete_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    msg = ("Ready, take a look:\n<b>"
            f"Title: {user_data[user_id].title}\n"
            f"Advisor: {user_data[user_id].adviser}\n"
            f"University: {user_data[user_id].university}\n"
            f"Group: {user_data[user_id].student_group}\n"
            f"Name: {user_data[user_id].name}\n"
            f"Surname: {user_data[user_id].surname}\n"
            f"Patronymic: {user_data[user_id].patronymic}\n"
            f"Email: {user_data[user_id].email}\n"
            f"Phone: {user_data[user_id].phone}\n</b>")
    bot.send_message(user_id, msg, parse_mode="html", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.from_user.id)
                             
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == 'main_menu':
            main_menu(call.from_user.id)
        elif call.data == 'create_application':
            if call.from_user.id in user_data:
                show_application(call.from_user.id)
            else:
                bot.send_message(call.from_user.id, 'Введите тему')
                bot.register_next_step_handler(call.message, get_title)
        elif call.data == 'post_application':
            user_data[call.from_user.id].telegram_id = call.from_user.id
            response = requests.post(config.BACKEND_BASE_URL + '/applications', json=user_data[call.from_user.id].__dict__)
            if response.status_code == 200:
                bot.send_message(call.from_user.id, 'Спасибо за заявку')

        elif call.data == 'delete_data':
            del user_data[call.from_user.id]
            main_menu(call.from_user.id)
        elif call.data == 'list_applications':
            response = requests.get(config.BACKEND_BASE_URL + '/applications', params={
                'telegram_id': call.from_user.id
            })
            print(response.json())

def get_title(message):
    user_data[message.from_user.id] = Application()
    user_data[message.from_user.id].title = message.text

    bot.send_message(message.chat.id, 'Введите советника')
    bot.register_next_step_handler(message, get_adviser)

def get_adviser(message):
    user_data[message.from_user.id].adviser = message.text

    bot.send_message(message.chat.id, 'Введите ваш университет')
    bot.register_next_step_handler(message, get_university)

def get_university(message):
    user_data[message.from_user.id].university = message.text

    bot.send_message(message.chat.id, 'Введите вашу группу')
    bot.register_next_step_handler(message, get_group)

def get_group(message):
    user_data[message.from_user.id].student_group = message.text

    bot.send_message(message.chat.id, 'Введите ваше имя')
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data[message.from_user.id].name = message.text

    bot.send_message(message.chat.id, 'Введите вашу фамилию')
    bot.register_next_step_handler(message, get_surname)
 
def get_surname(message):
    user_data[message.from_user.id].surname = message.text

    bot.send_message(message.chat.id, "Введите ваше отчество (при наличии)")
    bot.register_next_step_handler(message, get_patronymic)

def get_patronymic(message):
    user_data[message.from_user.id].patronymic = message.text

    bot.send_message(message.chat.id, "Введите ваш email")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    user_data[message.from_user.id].email = message.text

    bot.send_message(message.chat.id, "Введите ваш номер телефона")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data[message.from_user.id].phone = message.text
    show_application(message.from_user.id)

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()
