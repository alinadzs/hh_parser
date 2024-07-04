import telebot
from telebot import types
import config
import psycopg2

bot = telebot.TeleBot(config.token)

# Конфигурация базы данных
db_config = {
    'dbname': "postgres",
    'user': "alina",
    'password': "12345678",
    'host': "host.docker.internal",
    'port': "5432",
}


# Подключение к базе данных
def connect_db():
    return psycopg2.connect(**db_config)


# Глобальная переменная для отслеживания текущей позиции вакансий для каждого пользователя
user_position = {}


@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.send_message(
        message.chat.id,
        text=f"Здравствуйте, {message.from_user.first_name}! Я - бот для отображения информации о вакансиях hh.ru. Напишите /help, чтобы понять, как я работаю"
    )


@bot.message_handler(commands=['help'])
def help_bot(message):
    bot.send_message(message.chat.id, text=config.help_text)


@bot.message_handler(commands=['vacancies'])
def get_vacancies(message):
    chat_id = message.chat.id
    user_position[chat_id] = 0  # Инициализация позиции пользователя

    send_vacancies(chat_id, user_position[chat_id])


def send_vacancies(chat_id, position):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT city, company, title, salary, url FROM vacancies")
    vacancies = cursor.fetchall()
    cursor.close()
    conn.close()

    response = ""
    end_position = position + 5  # Показываем по 5 вакансий за раз
    for i in range(position, min(end_position, len(vacancies))):
        vacancy = vacancies[i]
        response += f"Город: {vacancy[0]}\nКомпания: {vacancy[1]}\nДолжность: {vacancy[2]}\nЗарплата: {vacancy[3]}\nURL: {vacancy[4]}\n\n"

    if response:
        markup = types.InlineKeyboardMarkup()
        if end_position < len(vacancies):
            next_button = types.InlineKeyboardButton("Далее", callback_data=f"next_{end_position}")
            markup.add(next_button)
        bot.send_message(chat_id, text=response, reply_markup=markup)
    else:
        bot.send_message(chat_id, text="Вакансии не найдены")


@bot.callback_query_handler(func=lambda call: call.data.startswith('next_'))
def callback_next(call):
    chat_id = call.message.chat.id
    position = int(call.data.split('_')[1])
    user_position[chat_id] = position

    send_vacancies(chat_id, position)
    bot.answer_callback_query(call.id)


if __name__ == "__main__":
    bot.polling(none_stop=True)