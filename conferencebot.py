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
        self.title = ''
        self.adviser = ''
        self.university = ''
        self.student_group = ''
        self.name = ''
        self.surname = ''
        self.patronymic = ''
        self.email = ''
        self.phone = ''
        self.coauthors = []
        self.__dict__.update(entries)

class UserState:
    def __init__(self):
        self.application = None
        self.coauthor = {}
        self.posted_applications = None
        self.edited_application = None

class MyStates(StatesGroup):
    removing_coauthour = State()
    removing_edited_coauthour = State()
    creating_application = State()
    application_list = State()

user_data = {}

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.TOKEN, state_storage=state_storage)

def main_menu(user_id, chat_id, msg):
    markup = types.InlineKeyboardMarkup()
    create_button = types.InlineKeyboardButton('Создать', callback_data='create')
    list_button = types.InlineKeyboardButton('Список моих заявок', callback_data='application_list')
    markup.add(create_button, list_button)
    bot.send_message(user_id, msg, reply_markup=markup)
    bot.delete_state(user_id, chat_id)

def build_application_description(application):
    description = (f'<b>Тема:</b> {application.title}\n'
                f'<b>Советник:</b> {application.adviser}\n'
                f'<b>Университет:</b> {application.university}\n'
                f'<b>Группа:</b> {application.student_group}\n'
                f'<b>Имя:</b> {application.name}\n'
                f'<b>Фамилия:</b> {application.surname}\n')
    if application.patronymic:
        description += f'<b>Отчество:</b> {application.patronymic}\n'
    description += (f'<b>Email:</b> {application.email}\n'
                    f'<b>Телефон:</b> {application.phone}\n')
    if len(application.coauthors):
        description += f'<b>Соавторы:</b>\n'
        for coauthor in application.coauthors:
            description += f'\t{coauthor["name"]} {coauthor["surname"]} '
            if 'patronymic' in coauthor and coauthor['patronymic'] is not None:
                description += coauthor['patronymic']
            description += '\n'
    return description


def show_application(user_id, application):
    markup = types.InlineKeyboardMarkup()
    post_button = types.InlineKeyboardButton('Отправить заявку', callback_data='post_data')
    delete_button = types.InlineKeyboardButton('Удалить черновик', callback_data='rm_data')
    add_coauthor_button = types.InlineKeyboardButton('Добавить соавтора', callback_data='add_coauthor')
    rm_coauthor_button = types.InlineKeyboardButton('Удалить соавтора', callback_data='rm_coauthor')
    back_to_main_manu_button = types.InlineKeyboardButton('В главное меню', callback_data='main_menu')
    markup.add(post_button, delete_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    msg = '<b>Готово, посмотрите на ваш черновик:</b>\n'
    msg += build_application_description(application)
    bot.send_message(user_id, msg, parse_mode='html', reply_markup=markup)

def show_edited_application(user_id, application):
    markup = types.InlineKeyboardMarkup()
    update_button = types.InlineKeyboardButton('Сохранить', callback_data='update_data')
    add_coauthor_button = types.InlineKeyboardButton('Добавить соавтора', callback_data='add_coauthor')
    rm_coauthor_button = types.InlineKeyboardButton('Удалить соавтора', callback_data='rm_coauthor')
    back_to_main_manu_button = types.InlineKeyboardButton('Отменить редактирование', callback_data='main_menu')
    markup.add(update_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    msg = '<b>Готово, посмотрите на вашу заявку:</b>\n'
    msg += build_application_description(application)
    bot.send_message(user_id, msg, parse_mode='html', reply_markup=markup)

def show_user_applications(user_id, chat_id):
    markup = types.InlineKeyboardMarkup()
    back_to_main_manu_button = types.InlineKeyboardButton('В главное меню', callback_data='main_menu')
    for application in user_data[user_id].posted_applications:
        modify_button = types.InlineKeyboardButton(f'Изменить заявку №{application.id}', callback_data=str(application.id))
        markup.add(modify_button)
    markup.row(back_to_main_manu_button)
    msg = ''
    for application in user_data[user_id].posted_applications:
        msg += f'<b><tg-emoji emoji-id="1">✅</tg-emoji> Заявка №{application.id}</b>\n'
        msg += build_application_description(application)
    bot.send_message(user_id, msg, parse_mode='html', reply_markup=markup)
    bot.set_state(user_id, MyStates.application_list, chat_id)


def input_prompt(message, text, handler, markup = None):
    bot_message = bot.send_message(message.chat.id, text, reply_markup=markup)
    bot.register_next_step_handler(message, handler, bot_message)


@bot.middleware_handler()
def set_user_data(bot_instance, update):
    user_id = 0
    if update.callback_query:
        user_id = update.callback_query.from_user.id
    elif update.message:
        user_id = update.message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = UserState()


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.from_user.id, message.chat.id, 'Привет, с чего начнем?')


@bot.callback_query_handler(func=lambda call: True, state=MyStates.removing_coauthour)
def remove_coauthor_callback_handler(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    del user_data[call.from_user.id].application.coauthors[int(call.data)]
    show_application(call.from_user.id, user_data[call.from_user.id].application)
    bot.set_state(call.from_user.id, MyStates.creating_application, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: True, state=MyStates.removing_edited_coauthour)
def remove_edited_coauthor_callback_handler(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    del user_data[call.from_user.id].edited_application.coauthors[int(call.data)]
    show_edited_application(call.from_user.id, user_data[call.from_user.id].edited_application)
    bot.set_state(call.from_user.id, MyStates.application_list, call.message.chat.id)

@bot.callback_query_handler(func=lambda call: True, state=MyStates.creating_application)
def creating_application_callback_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        if call.data == 'skip_patronymic':
            bot.clear_step_handler(call.message)
            input_prompt(call.message, 'Введите ваш email. Например example@yandex.ru', get_email)
        elif call.data == 'skip_coauthor_patronymic':
            user_data[call.from_user.id].application.coauthors.append(user_data[call.from_user.id].coauthor)
            bot.clear_step_handler(call.message)
            show_application(call.from_user.id, user_data[call.from_user.id].application)
        elif call.data == 'main_menu':
            main_menu(call.from_user.id, call.message.chat.id, 'Вы вернулись в главное меню')
        elif call.data == 'add_coauthor':
            input_prompt(call.message, 'Введите имя соавтора', get_coauthor_name)
        elif call.data == 'rm_coauthor':
            markup = types.InlineKeyboardMarkup()
            for i, coauthor in enumerate(user_data[call.from_user.id].application.coauthors):
                option = types.InlineKeyboardButton(coauthor['surname'], callback_data=str(i))
                markup.add(option)
            bot.send_message(call.from_user.id, 'Какого соавтора вы хотите удалить?', reply_markup=markup)
            bot.set_state(call.from_user.id, MyStates.removing_coauthour, call.message.chat.id)
        elif call.data == 'post_data':
            user_data[call.from_user.id].application.telegram_id = call.from_user.id
            response = requests.post(config.BACKEND_BASE_URL + '/applications', 
                json=user_data[call.from_user.id].application.__dict__)
            if response.ok:
                main_menu(call.from_user.id, call.message.chat.id, 'Заявка отправлена, спасибо')
        elif call.data == 'rm_data':
            user_data[call.from_user.id].application = None
            main_menu(call.from_user.id, call.message.chat.id, 'Черновик удален, создадим новый?')
    except Exception as e:
        print(e)
        main_menu(call.from_user.id, call.message.chat.id, 'Бип буп, ошибка')
        raise e

@bot.callback_query_handler(func=lambda call: True, state=MyStates.application_list)
def application_list_callback_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        if call.data == 'main_menu':
            main_menu(call.from_user.id, call.message.chat.id, 'Вы вернулись в главное меню')
        elif call.data == 'skip_patronymic':
            bot.clear_step_handler(call.message)
            user_data[call.from_user.id].edited_application.patronymic = ''
            input_prompt(call.message, 'Введите ваш email. Например example@yandex.ru', get_new_email)
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            leave_as_is_button = types.KeyboardButton(user_data[call.from_user.id].edited_application.email)
            markup.add(leave_as_is_button)
            bot.send_message(call.message.chat.id, 'Или выберите уже имеющийся', reply_markup=markup)
        elif call.data == 'skip_coauthor_patronymic':
            user_data[call.from_user.id].edited_application.coauthors.append(user_data[call.from_user.id].coauthor)
            bot.clear_step_handler(call.message)
            show_edited_application(call.from_user.id, user_data[call.from_user.id].edited_application)
        elif call.data == 'add_coauthor':
            input_prompt(call.message, 'Введите имя соавтора', get_coauthor_name)
        elif call.data == 'rm_coauthor':
            markup = types.InlineKeyboardMarkup()
            for i, coauthor in enumerate(user_data[call.from_user.id].edited_application.coauthors):
                option = types.InlineKeyboardButton(coauthor['surname'], callback_data=str(i))
                markup.add(option)
            bot.send_message(call.from_user.id, 'Какого соавтора вы хотите удалить?', reply_markup=markup)
            bot.set_state(call.from_user.id, MyStates.removing_edited_coauthour, call.message.chat.id)
        elif call.data == 'update_data':
            response = requests.put(config.BACKEND_BASE_URL + '/applications', 
                json=user_data[call.from_user.id].edited_application.__dict__)
            if response.ok:
                main_menu(call.from_user.id, call.message.chat.id, 'Заявка обновлена, спасибо')
        elif int(call.data):
            user_data[call.from_user.id].edited_application = \
                next(application for application in user_data[call.from_user.id].posted_applications if application.id == int(call.data))
            input_prompt(call.message, 'Введите тему', get_new_title)

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
            leave_as_is_button = types.KeyboardButton(user_data[call.from_user.id].edited_application.title)
            markup.add(leave_as_is_button)
            bot.send_message(call.message.chat.id, 'Или выберите уже имеющееся', reply_markup=markup)

    except Exception as e:
        print(e)
        main_menu(call.from_user.id, call.message.chat.id, 'Бип буп, ошибка')
        raise e

@bot.callback_query_handler(func=lambda call: True)
def main_callback_handler(call):
    try:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        if call.data == 'main_menu':
            main_menu(call.from_user.id, call.message.chat.id, 'Вы вернулись в главное меню')
        elif call.data == 'create':
            if user_data[call.from_user.id].application:
                show_application(call.from_user.id, user_data[call.from_user.id].application)
            else:
                input_prompt(call.message, 'Введите тему', get_title)
            bot.set_state(call.from_user.id, MyStates.creating_application, call.message.chat.id)
        elif call.data == 'application_list':
            response = requests.get(config.BACKEND_BASE_URL + '/applications', 
                params={
                    'telegram_id': call.from_user.id
                })
            if response.ok:
                user_data[call.from_user.id].posted_applications = [Application(**data) for data in response.json()]
                show_user_applications(call.from_user.id, call.message.chat.id)
            else:
                bot.send_message(call.from_user.id, 'Похоже, что сервер заявок не доступен')
    except Exception as e:
        print(e)
        main_menu(call.from_user.id, call.message.chat.id, 'Бип буп, ошибка')
        raise e


##################### Заполнение формы #####################
def get_title(message, bot_message):
    user_data[message.from_user.id].application = Application()
    user_data[message.from_user.id].application.title = message.text
    input_prompt(message, 'Введите ФИО cоветника', get_adviser)

def get_adviser(message, bot_message):
    try:
        if not message.text.replace(' ', '').replace('.', '').isalpha():
            raise Exception('ФИО cоветника не может содержать цифры и спецсимволы\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.adviser = message.text
        input_prompt(message, 'Введите ваш университет', get_university)
    except Exception as ex:
        input_prompt(message, ex, get_adviser)

def get_university(message, bot_message):
    try:
        if not message.text.replace(' ', '').isalpha():
            raise Exception('Название университета должно содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.university = message.text
        input_prompt(message, 'Введите вашу группу', get_group)
    except Exception as ex:
        input_prompt(message, ex, get_university)

def get_group(message, bot_message):
    try:
        if not message.text.replace(' ', '').isalnum():
            raise Exception('Номер группы может содержать только буквы алфавита или цифры\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.student_group = message.text
        input_prompt(message, 'Введите ваше имя', get_name)
    except Exception as ex:
        input_prompt(message, ex, get_group)

def get_name(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Имя может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.name = message.text
        input_prompt(message, 'Введите вашу фамилию', get_surname)
    except Exception as ex:
        input_prompt(message, ex, get_name)
 
def get_surname(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Фамилия может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.surname = message.text

        markup = types.InlineKeyboardMarkup()
        skip_patronymic_button = types.InlineKeyboardButton('Отчество отсутствует', callback_data='skip_patronymic')
        markup.add(skip_patronymic_button)
        input_prompt(message, 'Введите ваше отчество', get_patronymic, markup)
    except Exception as ex:
        input_prompt(message, ex, get_surname)

def get_patronymic(message, bot_message):
    try:
        if len(message.text) and not message.text.isalpha():
            raise Exception('Отчество может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        
        bot.edit_message_reply_markup(message.chat.id, bot_message.id)
        user_data[message.from_user.id].application.patronymic = message.text
        input_prompt(message, 'Введите ваш email. Например example@yandex.ru', get_email)
    except Exception as ex:
        input_prompt(message, ex, get_patronymic)

def get_email(message, bot_message):
    try:
        if not re.match(r'([a-z]+)@([a-z]+)\.([a-z]+)', message.text):
            raise Exception('Неверный формат email адреса\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.email = message.text
        input_prompt(message, 'Введите ваш номер телефона. Например 89999999999', get_phone)
    except Exception as ex:
        input_prompt(message, ex, get_email)

def get_phone(message, bot_message):
    try:
        phone = message.text \
            .replace('+7', '8') \
            .replace('-', '') \
            .replace(' ', '') \
            .replace('(', '') \
            .replace(')', '')
        if len(phone) != 11 or not phone.isdigit():
            raise Exception('Неверный формат номера телефона\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].application.phone = phone
        show_application(message.from_user.id, user_data[message.from_user.id].application)
    except Exception as ex:
        input_prompt(message, ex, get_phone)

##################### Добавление соавтора #####################

def get_coauthor_name(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Имя может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].coauthor = {}
        user_data[message.from_user.id].coauthor['name'] = message.text
        input_prompt(message, 'Введите фамилию соавтора', get_coauthor_surname)
    except Exception as ex:
        input_prompt(message, ex, get_coauthor_name)

def get_coauthor_surname(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Фамилия может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].coauthor['surname'] = message.text

        markup = types.InlineKeyboardMarkup()
        skip_patronymic_button = types.InlineKeyboardButton('Отчество отсутствует', callback_data='skip_coauthor_patronymic')
        markup.add(skip_patronymic_button)
        input_prompt(message, 'Введите отчество соавтора', get_coauthor_patronymic, markup)
    except Exception as ex:
        input_prompt(message, ex, get_coauthor_surname)

def get_coauthor_patronymic(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Отчество может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')

        bot.edit_message_reply_markup(message.chat.id, bot_message.id)
        user_data[message.from_user.id].coauthor['patronymic'] = message.text

        if bot.get_state(message.from_user.id, message.chat.id) == 'MyStates:application_list':
            user_data[message.from_user.id].edited_application.coauthors \
                .append(user_data[message.from_user.id].coauthor)
            show_edited_application(message.from_user.id, user_data[message.from_user.id].edited_application)
        else:
            user_data[message.from_user.id].application.coauthors \
                .append(user_data[message.from_user.id].coauthor)
            show_application(message.from_user.id, user_data[message.from_user.id].application)
    except Exception as ex:
        input_prompt(message, ex, get_coauthor_patronymic)


##################### Обновление заявки #####################
def get_new_title(message, bot_message):
    user_data[message.from_user.id].edited_application.title = message.text
    input_prompt(message, 'Введите ФИО cоветника', get_new_adviser)

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.adviser)
    markup.add(leave_as_is_button)
    bot.send_message(message.chat.id, 'Или выберите уже имеющееся', reply_markup=markup)
    

def get_new_adviser(message, bot_message):
    try:
        if not message.text.replace(' ', '').replace('.', '').isalpha():
            raise Exception('ФИО cоветника не может содержать цифры и спецсимволы\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.adviser = message.text
        input_prompt(message, 'Введите ваш университет', get_new_university)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.university)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющийся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_adviser)

def get_new_university(message, bot_message):
    try:
        if not message.text.replace(' ', '').isalpha():
            raise Exception('Название университета должно содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.university = message.text
        input_prompt(message, 'Введите вашу группу', get_new_group)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.student_group)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющуюся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_university)

def get_new_group(message, bot_message):
    try:
        if not message.text.replace(' ', '').isalnum():
            raise Exception('Номер группы может содержать только буквы алфавита или цифры\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.student_group = message.text
        input_prompt(message, 'Введите ваше имя', get_new_name)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.name)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющееся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_group)

def get_new_name(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Имя может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.name = message.text
        input_prompt(message, 'Введите вашу фамилию', get_new_surname)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.surname)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющуюся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_name)
 
def get_new_surname(message, bot_message):
    try:
        if not message.text.isalpha():
            raise Exception('Фамилия может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.surname = message.text

        markup = types.InlineKeyboardMarkup()
        skip_patronymic_button = types.InlineKeyboardButton('Отчество отсутствует', callback_data='skip_patronymic')
        markup.add(skip_patronymic_button)
        input_prompt(message, 'Введите ваше отчество', get_new_patronymic, markup)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.patronymic)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющееся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_surname)

def get_new_patronymic(message, bot_message):
    try:
        if len(message.text) and not message.text.isalpha():
            raise Exception('Отчество может содержать только буквы алфавита\n' + 
                            'Попробуйте еще раз')
        bot.edit_message_reply_markup(message.chat.id, bot_message.id)
        input_prompt(message, 'Введите ваш email. Например example@yandex.ru', get_new_email)
        user_data[message.from_user.id].edited_application.patronymic = message.text
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.email)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющийся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_patronymic)

def get_new_email(message, bot_message):
    try:
        if not re.match(r'([a-z]+)@([a-z]+)\.([a-z]+)', message.text):
            raise Exception('Неверный формат email адреса\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.email = message.text
        input_prompt(message, 'Введите ваш номер телефона. Например 89999999999', get_new_phone)
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        leave_as_is_button = types.KeyboardButton(user_data[message.from_user.id].edited_application.phone)
        markup.add(leave_as_is_button)
        bot.send_message(message.chat.id, 'Или выберите уже имеющийся', reply_markup=markup)
    except Exception as ex:
        input_prompt(message, ex, get_new_email)

def get_new_phone(message, bot_message):
    try:
        phone = message.text \
            .replace('+7', '8') \
            .replace('-', '') \
            .replace(' ', '') \
            .replace('(', '') \
            .replace(')', '')
        if len(phone) != 11 or not phone.isdigit():
            raise Exception('Неверный формат номера телефона\n' +
                            'Попробуйте еще раз')
        user_data[message.from_user.id].edited_application.phone = phone
        show_edited_application(message.from_user.id, user_data[message.from_user.id].edited_application)
    except Exception as ex:
        input_prompt(message, ex, get_new_phone)

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()
