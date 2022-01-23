import logging

from os import getenv
from sys import exit
from aiogram import Bot, Dispatcher, executor, types
from ossapi import OssapiV2
from ossapi import Ossapi
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

bot_token = getenv(token) #<---- Import your telegram bot token
if not bot_token:
    exit("Error: no token provided")

bot = Bot(token=bot_token)
osu = OssapiV2(user_id, secret_id) #<---- Import your own data
osuv1 = Ossapi(api_key) #<---- Import your api key



dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

class States(StatesGroup):
    main_menu = State()
    user_name = State()
    info_about_user = State()
    beatmap_name = State()
    info_about_beatmap = State()
    

@dp.message_handler(commands="start", state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["Посмотреть информацию об игроке", "Посмотреть информацию о карте"]
    keyboard.add(*buttons)
    await message.answer("Выберите пункт из меню", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Посмотреть информацию об игроке")
async def get_user_name(message: types.Message):
    await States.user_name.set()
    await message.answer("Введите никнейм игрока,используя английские символы")


@dp.message_handler(state=States.user_name)
async def work_with_user(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        info["user_name"] = message.text
    if not osu.search(query=message.text).users.data:
        await message.answer("Вы ввели неправильно никнейм")
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Посмотреть количество игр",
        "Посмотреть онлайн ли он",
        "Посмотреть его аватар",
        "Посмотреть когда он зарегистрировался",
        "Посмотреть на какой карте больше всего попыток",
        "Посмотреть лучший скор",
        "Назад",
    ]
    keyboard.add(*buttons)
    await States.next()
    await message.answer("Что Вы хотите узнать?", reply_markup=keyboard)


@dp.message_handler(text="Посмотреть количество игр", state=States.info_about_user)
async def get_player_playcount(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user = osu.search(query=info["user_name"]).users.data[0]
    await message.answer(f"""Количество игр: {osuv1.get_user(user.id).playcount}""")


@dp.message_handler(text="Посмотреть его аватар", state=States.info_about_user)
async def get_player_avatar(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user = osu.search(query=info["user_name"]).users.data[0]
    await message.answer(f"""Аватар: {user.avatar_url}""")


@dp.message_handler(text="Посмотреть онлайн ли он", state=States.info_about_user)
async def get_player_online(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user = osu.search(query=info["user_name"]).users.data[0]
    await message.answer(f"""Онлайн: {user.is_online}""")


@dp.message_handler(
    text="Посмотреть когда он зарегистрировался", state=States.info_about_user
)
async def get_player_registry_date(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user = osu.search(query=info["user_name"]).users.data[0]
    await message.answer("Для получения времени МСК в дате +3 часа")
    await message.answer(f"""Дата регистрации: {osu.user(user.id).join_date}""")


@dp.message_handler(
    text="Посмотреть на какой карте больше всего попыток",
    state=States.info_about_user,
)
async def get_player_beatmap_playcount(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user_name = info["user_name"]
    user_id = osu.search(query=user_name).users.data[0].id
    user_beatmaps = osu.user_beatmaps(user_id=user_id, type_="most_played")[0]
    beatmap = user_beatmaps.beatmap()
    beatmapset = beatmap.beatmapset()
    beatmap_user_score = osu.beatmap_user_score(
        beatmap_id=beatmap.id, user_id=user_id
    ).score
    await message.answer(
        f"""Название карты: {beatmapset.title}
Количество попыток: {user_beatmaps.count}
Дата: {beatmap_user_score.created_at}
Количество PP: {beatmap_user_score.pp}
Превью карты: {beatmapset.preview_url}"""
    )


@dp.message_handler(text="Посмотреть лучший скор", state=States.info_about_user)
async def get_player_best_score(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        user = osu.search(query=info["user_name"]).users.data[0]
    beatmap_info = osu.user_scores(user.id, "best")[0].beatmap
    beatmap_info_id = beatmap_info.id
    beatmap_title = beatmap_info.beatmapset().title
    beatmap_user_score = osu.beatmap_user_score(beatmap_id=beatmap_info_id, user_id=user.id)
    await message.answer("Для получения времени МСК в дате +3 часа")
    await message.answer(
        f"""Название карты: {beatmap_title}
Дата: {beatmap_info.created_at}
Количество PP: {beatmap_user_score.score.pp}
Место на карте: {beatmap_user_score.position}
Превью карты:{beatmap_info.beatmapset().preview_url}"""
    )


@dp.message_handler(lambda message: message.text == "Посмотреть информацию о карте")
async def get_beatmap_name(message: types.Message):
    await States.beatmap_name.set()
    await message.answer("Введите название карты, используя английские символы")


@dp.message_handler(state=States.beatmap_name)
async def work_with_beatmap(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        info["beatmap_name"] = message.text
    if not osu.search_beatmapsets(query=message.text).beatmapsets:
        await message.answer("Вы ввели неправильно название карты")
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Посмотреть количество игр на карте",
        "Посмотреть автора карты",
        "Прослушать превью карты",
        "Дата создания карты",
        "Назад",
    ]
    keyboard.add(*buttons)
    await States.next()
    await message.answer("Что Вы хотите узнать?", reply_markup=keyboard)


@dp.message_handler(
    text="Посмотреть количество игр на карте", state=States.info_about_beatmap
)
async def get_beatmap_playcount(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        beatmap = osu.search_beatmapsets(query=info["beatmap_name"]).beatmapsets[0]
    await message.answer(f"Количество игр: {beatmap.play_count}")


@dp.message_handler(text="Посмотреть автора карты", state=States.info_about_beatmap)
async def get_beatmap_creator(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        beatmap = osu.search_beatmapsets(query=info["beatmap_name"]).beatmapsets[0]
    await message.answer(f"Автор карты: {beatmap.creator}")


@dp.message_handler(text="Прослушать превью карты", state=States.info_about_beatmap)
async def get_beatmap_prewiev(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        beatmap = osu.search_beatmapsets(query=info["beatmap_name"]).beatmapsets[0]
    await message.answer(f"Превью:{beatmap.preview_url}")


@dp.message_handler(text="Дата создания карты", state=States.info_about_beatmap)
async def get_beatmap_date_creation(message: types.Message, state: FSMContext):
    async with state.proxy() as info:
        beatmap = osu.search_beatmapsets(query=info["beatmap_name"]).beatmapsets[0]
    await message.answer("Для получения времени МСК в дате +3 часа")
    await message.answer(f"Дата создания карты:{beatmap.submitted_date}")


@dp.message_handler(text="Назад", state="*")
async def get_back(message: types.Message):
    await dp.storage.close()
    await dp.storage.wait_closed()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["Посмотреть информацию об игроке", "Посмотреть информацию о карте"]
    keyboard.add(*buttons)
    await message.answer("Выберите пункт из меню", reply_markup=keyboard)

async def on_shutdown(dp):
    await dp.storage.close()
    await dp.storage.wait_closed()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_shutdown = on_shutdown)