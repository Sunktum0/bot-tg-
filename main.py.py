from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import datetime

TOKEN = '7534888165:AAHPxZnM9W7r1VdSxvYYkuqTnU1J-MfTp7Y'
dict_values = {
    'труба': 30,
    'кабель utp6е': 40
}
result_dict = {}
daily_totals = {}

# Состояния диалога
class States:
    WAITING_FOR_NAME = 1
    WAITING_FOR_MATERIAL = 2
    WAITING_FOR_SCORE = 3
    WAITING_FOR_CONTINUE = 4  # Новое состояние для выбора продолжать или нет

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['state'] = States.WAITING_FOR_NAME
    await update.message.reply_text('Добро пожаловать! Пожалуйста, введите вашу фамилию:')

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')

    if state == States.WAITING_FOR_NAME:
        name = update.message.text
        user_id = update.message.from_user.id
        context.user_data['name'] = name
        context.user_data['id'] = user_id
        context.user_data['state'] = States.WAITING_FOR_MATERIAL
        await update.message.reply_text(f'Спасибо, {name}! Теперь введите название материала или работы.')

    elif state == States.WAITING_FOR_MATERIAL:
        name_values = update.message.text.lower()
        context.user_data['material_name'] = name_values
        context.user_data['state'] = States.WAITING_FOR_SCORE
        await update.message.reply_text('Введите количество:')

    elif state == States.WAITING_FOR_SCORE:
        name = context.user_data['name']
        score_text = update.message.text
        name_values = context.user_data['material_name']

        try:
            score = int(score_text)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите корректное целое число для количества.")
            return

        if name_values in dict_values:
            value = dict_values[name_values]
            result = value * score
            current_date = datetime.datetime.now().date()

            if current_date in daily_totals:
                daily_totals[current_date] += result
            else:
                daily_totals[current_date] = result

            if name not in result_dict:
                result_dict[name] = {}

            if name_values in result_dict[name]:
                result_dict[name][name_values] += result
            else:
                result_dict[name][name_values] = result

            await update.message.reply_text('Данные сохранены! Хотите ввести еще данные? (да/нет)')
            context.user_data['state'] = States.WAITING_FOR_CONTINUE  # Смена состояния на ожидание ответа

        else:
            await update.message.reply_text('Название материала или работы не найдено в словаре.')

    elif state == States.WAITING_FOR_CONTINUE:
        user_response = update.message.text.lower()
        if user_response == 'да':
            context.user_data['state'] = States.WAITING_FOR_MATERIAL
            await update.message.reply_text('Введите название материала или работы:')
        elif user_response == 'нет':
            await show_results(update, context)  # Показываем результаты
            # Сброс состояния, если нужно
            context.user_data['state'] = States.WAITING_FOR_NAME
        else:
            await update.message.reply_text('Пожалуйста, введите "да" или "нет".')

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_str = "\nИтоговые результаты по дням:\n"
    total_sum = sum(daily_totals.values())
    for date, total in daily_totals.items():
        result_str += f'{date}: {total}\n'
    result_str += f'\nОбщая сумма: {total_sum}\nИтоговые результаты по именам и продуктам:\n'
    for user_name, products in result_dict.items():
        result_str += f'Имя: {user_name}\n'
        for product, total in products.items():
            result_str += f' {product}: {total}\n'
    await update.message.reply_text(result_str)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result_str = "Данные от пользователей:\n"

    if result_dict:
        for name, products in result_dict.items():
            for product, total in products.items():
                result_str += f'Фамилия: {name}, Дата: {datetime.datetime.now().date()}, Материал: {product}, Количество: {total // dict_values[product]}, Сумма: {total}\n'
    else:
        result_str = "Нет данных для отображения."

    await update.message.reply_text(result_str)

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message))
    application.add_handler(CommandHandler("results", show_results))
    application.add_handler(CommandHandler("admin", admin))  # Добавляем обработчик для команды /admin
    application.run_polling()

if __name__ == '__main__':
    main()