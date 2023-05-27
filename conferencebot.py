import config
import telebot
import json
import requests
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.TOKEN, state_storage=state_storage)

class MyStates(StatesGroup):
    mainMenu = State()
    create_application = State()

    input_title = State()
    input_advisor = State()
    input_university = State()
    input_group = State() 
    input_name = State()
    input_surname = State()
    input_patronymic = State()
    input_email = State()
    input_phone = State()
    

    my_applications = State()

def main_menu(message):
    markup = types.InlineKeyboardMarkup()
    create_button = types.InlineKeyboardButton("Создать", callback_data='create_application')
    list_button = types.InlineKeyboardButton("Список моих заявок", callback_data='list_applications')
    markup.add(create_button, list_button)

    bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    bot.reply_to(message, 'Привет, с чего начнем?', reply_markup=markup)

def show_application(message):
    markup = types.InlineKeyboardMarkup()
    post_button = types.InlineKeyboardButton("Отправить заявку", callback_data='post_application')
    delete_button = types.InlineKeyboardButton("Удалить черновик", callback_data='delete_data')
    add_coauthor_button = types.InlineKeyboardButton("Добавить соавтора", callback_data='add_coauthor')
    rm_coauthor_button = types.InlineKeyboardButton("Удалить соавтора", callback_data='rm_coauthor')
    back_to_main_manu_button = types.InlineKeyboardButton("В главное меню", callback_data='main_menu')
    markup.add(post_button, delete_button, add_coauthor_button, rm_coauthor_button, back_to_main_manu_button)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if data is not None:
            print(data)
            msg = ("Ready, take a look:\n<b>"
                    f"Title: {data['title']}\n"
                    f"Advisor: {data['advisor']}\n"
                    f"University: {data['university']}\n"
                    f"Group: {data['group']}\n"
                    f"Name: {data['name']}\n"
                    f"Surname: {data['surname']}\n"
                    f"Patronymic: {data['patronymic']}\n"
                    f"Email: {data['email']}\n"
                    f"Phone: {data['phone']}\n</b>")
            bot.send_message(message.chat.id, msg, parse_mode="html", reply_markup=markup)


@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message)
                             
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == 'main_menu':
            main_menu(call.message)
        if call.data == 'create_application':
            show_application(call.message)
            bot.set_state(call.from_user.id, MyStates.input_title, call.message.chat.id)
            bot.send_message(call.message.chat.id, 'Введите тему')
            
        if call.data == 'post_application':
            with bot.retrieve_data(call.message.from_user.id, call.message.chat.id) as data:
                print(data['name'])
                response = requests.post(config.BACKEND_BASE_URL + '/applications', json=data)
                print(response.json())
        if call.data == 'delete_data':
            bot.reset_data(call.message.from_user.id, call.message.chat.id)
            main_menu(call.message)
        if call.data == 'list_applications':
            response = requests.post(config.BACKEND_BASE_URL + '/applications', params={
                'telegram_id': call.message.from_user.id
            })

@bot.message_handler(state=MyStates.input_title)
def name_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['title'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_advisor, message.chat.id)
    bot.send_message(message.chat.id, 'Введите советника')

@bot.message_handler(state=MyStates.input_advisor)
def name_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['advisor'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_university, message.chat.id)
    bot.send_message(message.chat.id, 'Введите ваш университет')

@bot.message_handler(state=MyStates.input_university)
def name_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['university'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_group, message.chat.id)
    bot.send_message(message.chat.id, 'Введите вашу группу')

@bot.message_handler(state=MyStates.input_group)
def name_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['group'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_name, message.chat.id)
    bot.send_message(message.chat.id, 'Введите ваше имя')

@bot.message_handler(state=MyStates.input_name)
def name_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['name'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_surname, message.chat.id)
    bot.send_message(message.chat.id, 'Введите вашу фамилию')
 
@bot.message_handler(state=MyStates.input_surname)
def surname_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['surname'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_patronymic, message.chat.id)
    bot.send_message(message.chat.id, "Введите ваше отчество (при наличии)")

@bot.message_handler(state=MyStates.input_patronymic)
def surname_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['patronymic'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_email, message.chat.id)
    bot.send_message(message.chat.id, "Введите ваш email")

@bot.message_handler(state=MyStates.input_email)
def surname_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['email'] = message.text

    bot.set_state(message.from_user.id, MyStates.input_phone, message.chat.id)
    bot.send_message(message.chat.id, "Введите ваш номер телефона")

@bot.message_handler(state=MyStates.input_phone)
def patronymic_get(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['phone'] = message.text

    show_application(message)

    bot.delete_state(message.from_user.id, message.chat.id)

#incorrect number
# @bot.message_handler(state=MyStates.age, is_digit=False)
# def age_incorrect(message):
#     """
#     Wrong response for MyStates.age
#     """
#     bot.send_message(message.chat.id, 'Looks like you are submitting a string in the field age. Please enter a number')

bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling()
