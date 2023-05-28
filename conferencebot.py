import config
import telebot
import requests
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot import apihelper

apihelper.ENABLE_MIDDLEWARE = True

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

class UserState:
    def __init__(self):
        self.application = None
        self.coauthor = {}

class MyStates(StatesGroup):
    removing_coauthour = State()

user_data = {}

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.TOKEN, state_storage=state_storage)

def main_menu(user_id):
    markup = types.InlineKeyboardMarkup()
    create_button = types.InlineKeyboardButton("Создать", callback_data='create_application')
    list_button = types.InlineKeyboardButton("Список моих заявок", callback_data='list_applications')
    markup.add(create_button, list_button)

    bot.send_message(user_id, 'Привет, с чего начнем?', reply_markup=markup)

def show_application(user_id):
    markup = types.InlineKeyboardMarkup()
    post_button = types.InlineKeyboardButton("Отправить заявку", callback_data='post_application')
    delete_button = types.InlineKeyboardButton("Удалить черновик", callback_data='delete_data')
    add_coauthor_button = types.InlineKeyboardButton("Добавить соавтора", callback_data='add_coauthor')
    rm_coauthor_button = types.InlineKeyboardButton("Удалить соавтора", callback_data='rm_coauthor')
    back_to_main_manu_button = types.InlineKeyboardButton("В главное меню", callback_data='main_menu')
    markup.add(post_button, delete_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    msg = ("Ready, take a look:\n"
            f"Title: {user_data[user_id].application.title}\n"
            f"Advisor: {user_data[user_id].application.adviser}\n"
            f"University: {user_data[user_id].application.university}\n"
            f"Group: {user_data[user_id].application.student_group}\n"
            f"Name: {user_data[user_id].application.name}\n"
            f"Surname: {user_data[user_id].application.surname}\n"
            f"Patronymic: {user_data[user_id].application.patronymic}\n"
            f"Email: {user_data[user_id].application.email}\n"
            f"Phone: {user_data[user_id].application.phone}\n")
    if len(user_data[user_id].application.coauthors):
        msg += f"Соавторы: \n"
        for coauthor in user_data[user_id].application.coauthors:
            msg += f"\t{coauthor['name']} {coauthor['surname']} {coauthor['patronymic']}\n"
    bot.send_message(user_id, msg, parse_mode="html", reply_markup=markup)

@bot.middleware_handler(update_types=['message'])
def set_user_data(bot_instance, message):
    if message.from_user.id not in user_data:
        user_data[message.from_user.id] = UserState()

@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.from_user.id)


@bot.callback_query_handler(func=lambda call: True, state=MyStates.removing_coauthour)
def remove_coauthor(call):
    del user_data[call.from_user.id].application.coauthors[int(call.data)]
    show_application(call.from_user.id)
    bot.delete_state(call.from_user.id, call.message.chat.id)


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
        elif call.data == 'add_coauthor':
            bot.send_message(call.from_user.id, 'Введите имя соавтора')
            bot.register_next_step_handler(call.message, get_coauthor_name)
        elif call.data == 'rm_coauthor':
            markup = types.InlineKeyboardMarkup()
            for i, coauthor in enumerate(user_data[call.from_user.id].application.coauthors):
                print(i)
                option = types.InlineKeyboardButton(coauthor['surname'], callback_data=str(i))
                markup.add(option)
            bot.send_message(call.from_user.id, 'Какого соавтора вы хотите удалить?', reply_markup=markup)
            bot.set_state(call.from_user.id, MyStates.removing_coauthour, call.message.chat.id)

        elif call.data == 'post_application':
            user_data[call.from_user.id].application.telegram_id = call.from_user.id
            response = requests.post(config.BACKEND_BASE_URL + '/applications', 
                json=user_data[call.from_user.id].application.__dict__)
            if response.status_code == 200:
                bot.send_message(call.from_user.id, 'Спасибо за заявку')

        elif call.data == 'delete_data':
            del user_data[call.from_user.id].application
            main_menu(call.from_user.id)
        elif call.data == 'list_applications':
            response = requests.get(config.BACKEND_BASE_URL + '/applications', 
                params={
                    'telegram_id': call.from_user.id
                })
            print(response.json())

##################### Заполнение формы #####################

def get_title(message):
    user_data[message.from_user.id].application = Application()
    user_data[message.from_user.id].application.title = message.text

    bot.send_message(message.chat.id, 'Введите советника')
    bot.register_next_step_handler(message, get_adviser)

def get_adviser(message):
    user_data[message.from_user.id].application.adviser = message.text

    bot.send_message(message.chat.id, 'Введите ваш университет')
    bot.register_next_step_handler(message, get_university)

def get_university(message):
    user_data[message.from_user.id].application.university = message.text

    bot.send_message(message.chat.id, 'Введите вашу группу')
    bot.register_next_step_handler(message, get_group)

def get_group(message):
    user_data[message.from_user.id].application.student_group = message.text

    bot.send_message(message.chat.id, 'Введите ваше имя')
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data[message.from_user.id].application.name = message.text

    bot.send_message(message.chat.id, 'Введите вашу фамилию')
    bot.register_next_step_handler(message, get_surname)
 
def get_surname(message):
    user_data[message.from_user.id].application.surname = message.text

    bot.send_message(message.chat.id, "Введите ваше отчество (при наличии)")
    bot.register_next_step_handler(message, get_patronymic)

def get_patronymic(message):
    user_data[message.from_user.id].application.patronymic = message.text

    bot.send_message(message.chat.id, "Введите ваш email")
    bot.register_next_step_handler(message, get_email)

def get_email(message):
    user_data[message.from_user.id].application.email = message.text

    bot.send_message(message.chat.id, "Введите ваш номер телефона")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data[message.from_user.id].application.phone = message.text
    show_application(message.from_user.id)

##################### Добавление соавтора #####################

def get_coauthor_name(message):
    user_data[message.from_user.id].coauthor = {}
    user_data[message.from_user.id].coauthor['name'] = message.text

    bot.send_message(message.chat.id, "Введите фамилию соавтора")
    bot.register_next_step_handler(message, get_coauthor_surname)

def get_coauthor_surname(message):
    user_data[message.from_user.id].coauthor['surname'] = message.text

    bot.send_message(message.chat.id, "Введите отчество соавтора")
    bot.register_next_step_handler(message, get_coauthor_patronymic)

def get_coauthor_patronymic(message):
    user_data[message.from_user.id].coauthor['patronymic'] = message.text
    user_data[message.from_user.id].application.coauthors \
        .append(user_data[message.from_user.id].coauthor)
    show_application(message.from_user.id)
    

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()
