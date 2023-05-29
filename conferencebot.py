import config
import telebot
import requests
import re
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot import apihelper

apihelper.ENABLE_MIDDLEWARE = True

class Application:
    def __init__(self, **entries):
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

        self.__dict__.update(entries)

class UserState:
    def __init__(self):
        self.application = None
        self.coauthor = {}

class MyStates(StatesGroup):
    removing_coauthour = State()

user_data = {}

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.TOKEN, state_storage=state_storage)


def main_menu(user_id, msg):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    create_button = types.KeyboardButton("Создать")
    list_button = types.KeyboardButton("Список моих заявок")
    markup.add(create_button, list_button)

    bot.send_message(user_id, msg, reply_markup=markup)

def build_application_description(application):
    description = (f"<b>Тема:</b> {application.title}\n"
                f"<b>Советник:</b> {application.adviser}\n"
                f"<b>Университет:</b> {application.university}\n"
                f"<b>Группа:</b> {application.student_group}\n"
                f"<b>Имя:</b> {application.name}\n"
                f"<b>Фамилия:</b> {application.surname}\n"
                f"<b>Отчество:</b> {application.patronymic}\n"
                f"<b>Email:</b> {application.email}\n"
                f"<b>Телефон:</b> {application.phone}\n")
    if len(application.coauthors):
        description += f"<b>Соавторы:</b>\n"
        for coauthor in application.coauthors:
            description += f"\t{coauthor['name']} {coauthor['surname']} {coauthor['patronymic']}\n"
    return description


def show_application(user_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    post_button = types.KeyboardButton("Отправить заявку")
    delete_button = types.KeyboardButton("Удалить черновик")
    add_coauthor_button = types.KeyboardButton("Добавить соавтора")
    rm_coauthor_button = types.KeyboardButton("Удалить соавтора")
    back_to_main_manu_button = types.KeyboardButton("В главное меню")
    markup.add(post_button, delete_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    msg = "<b>Готово, посмотрите на вашу заявку:</b>\n"
    msg += build_application_description(user_data[user_id].application)
    bot.send_message(user_id, msg, parse_mode="html", reply_markup=markup)

# Проверить на несколько заявок
def show_user_applications(user_id, applications):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    back_to_main_manu_button = types.KeyboardButton("В главное меню")
    for application in applications:
        modify_button = types.KeyboardButton(f"Изменить заявку №{application.id}")
        markup.add(modify_button)
    markup.row(back_to_main_manu_button)
    msg = ''
    for application in applications:
        msg += f'<b><tg-emoji emoji-id="1">✅</tg-emoji> Заявка №{application.id}</b>\n'
        msg += build_application_description(application)
    bot.send_message(user_id, msg, parse_mode="html", reply_markup=markup)


@bot.middleware_handler(update_types=['message'])
def set_user_data(bot_instance, message):
    if message.from_user.id not in user_data:
        user_data[message.from_user.id] = UserState()


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.from_user.id, 'Привет, с чего начнем?')


@bot.callback_query_handler(func=lambda call: True, state=MyStates.removing_coauthour)
def remove_coauthor(call):
    del user_data[call.from_user.id].application.coauthors[int(call.data)]
    show_application(call.from_user.id)
    bot.delete_state(call.from_user.id, call.message.chat.id)


@bot.message_handler(content_types=['text'])
def main(message):
    try:
        if message.text == 'В главное меню':
            main_menu(message.from_user.id, 'Вы вернулись в главное меню')
        elif message.text == 'Создать':
            if user_data[message.from_user.id].application:
                show_application(message.from_user.id)
            else:
                bot.send_message(message.from_user.id, 'Введите тему')
                bot.register_next_step_handler(message, get_title)
        elif message.text == 'Добавить соавтора':
            bot.send_message(message.from_user.id, 'Введите имя соавтора')
            bot.register_next_step_handler(message, get_coauthor_name)
        elif message.text == 'Удалить соавтора':
            markup = types.InlineKeyboardMarkup()
            for i, coauthor in enumerate(user_data[message.from_user.id].application.coauthors):
                option = types.InlineKeyboardButton(coauthor['surname'], callback_data=str(i))
                markup.add(option)
            bot.send_message(message.from_user.id, 'Какого соавтора вы хотите удалить?', reply_markup=markup)
            bot.set_state(message.from_user.id, MyStates.removing_coauthour, message.chat.id)
        elif message.text == 'Отправить заявку':
            user_data[message.from_user.id].application.telegram_id = message.from_user.id
            response = requests.post(config.BACKEND_BASE_URL + '/applications', 
                json=user_data[message.from_user.id].application.__dict__)
            if response.ok:
                main_menu(message.from_user.id, 'Заявка отправлена, спасибо')
        elif message.text == 'Удалить черновик':
            del user_data[message.from_user.id].application
            main_menu(message.from_user.id, 'Черновик удален, создадим новый?')
        elif message.text == 'Список моих заявок':
            response = requests.get(config.BACKEND_BASE_URL + '/applications', 
                params={
                    'telegram_id': message.from_user.id
                })
            if response.ok:
                print(response.json())
                applications = [Application(**data) for data in response.json()]
                show_user_applications(message.from_user.id, applications)
            else:
                bot.send_message(message.from_user.id, 'Похоже, что сервер заявок не доступен')
    except Exception as e:
        print(e)
        main_menu(message.from_user.id, 'Бип буп, ошибка')

##################### Заполнение формы #####################
def get_title(message):
    user_data[message.from_user.id].application = Application()
    user_data[message.from_user.id].application.title = message.text

    bot.send_message(message.chat.id, 'Введите ФИО cоветника')
    bot.register_next_step_handler(message, get_adviser)


# проверить проверки
def get_adviser(message):
    try:
        if not message.text.replace(' ', '').replace('.', '').isalpha():
            raise Exception('ФИО cоветника не может содержать цифры и спецсимволы\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.adviser = message.text

        bot.send_message(message.chat.id, 'Введите ваш университет')
        bot.register_next_step_handler(message, get_university)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_adviser)

def get_university(message):
    try:
        if not message.text.replace(' ', '').isalpha():
            raise Exception('Название университета должно содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.university = message.text

        bot.send_message(message.chat.id, 'Введите вашу группу')
        bot.register_next_step_handler(message, get_group)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_university)

def get_group(message):
    try:
        if not message.text.replace(' ', '').isalnum():
            raise Exception('Номер группы может содержать только буквы алфавита или цифры\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.student_group = message.text

        bot.send_message(message.chat.id, 'Введите ваше имя')
        bot.register_next_step_handler(message, get_name)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_group)

def get_name(message):
    try:
        if not message.text.isalpha():
            raise Exception('Имя может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.name = message.text

        bot.send_message(message.chat.id, 'Введите вашу фамилию')
        bot.register_next_step_handler(message, get_surname)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_name)
 
def get_surname(message):
    try:
        if not message.text.isalpha():
            raise Exception('Фамилия может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.surname = message.text

        bot.send_message(message.chat.id, "Введите ваше отчество (при наличии)")
        bot.register_next_step_handler(message, get_patronymic)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_surname)

# Что если нет отчества?
def get_patronymic(message):
    try:
        if len(message.text) and not message.text.isalpha():
            raise Exception('Отчество может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.patronymic = message.text

        bot.send_message(message.chat.id, "Введите ваш email. Например example@yandex.ru")
        bot.register_next_step_handler(message, get_email)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_patronymic)

def get_email(message):
    try:
        if not re.match(r'([a-z]+)@([a-z]+)\.([a-z]+)', message.text):
            raise Exception('Неверный формат email адреса\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.email = message.text

        bot.send_message(message.chat.id, "Введите ваш номер телефона. Например 89999999999")
        bot.register_next_step_handler(message, get_phone)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_email)

def get_phone(message):
    try:
        if len(message.text) != 11 or not message.text.isdigit():
            raise Exception('Неверный формат email адреса\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.phone = message.text
        show_application(message.from_user.id)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_phone)

##################### Добавление соавтора #####################

def get_coauthor_name(message):
    try:
        if not message.text.isalpha():
            raise Exception('Имя может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].coauthor = {}
        user_data[message.from_user.id].coauthor['name'] = message.text

        bot.send_message(message.chat.id, "Введите фамилию соавтора")
        bot.register_next_step_handler(message, get_coauthor_surname)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_coauthor_name)


def get_coauthor_surname(message):
    try:
        if not message.text.isalpha():
            raise Exception('Фамилия может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].coauthor['surname'] = message.text

        bot.send_message(message.chat.id, "Введите отчество соавтора")
        bot.register_next_step_handler(message, get_coauthor_patronymic)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_coauthor_surname)

# что если нет отчества?
def get_coauthor_patronymic(message):
    try:
        if not message.text.isalpha():
            raise Exception('Отчество может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].coauthor['patronymic'] = message.text
        user_data[message.from_user.id].application.coauthors \
            .append(user_data[message.from_user.id].coauthor)
        show_application(message.from_user.id)
    except Exception as ex:
        bot.send_message(message.chat.id, ex)
        bot.register_next_step_handler(message, get_coauthor_patronymic)
    

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()
