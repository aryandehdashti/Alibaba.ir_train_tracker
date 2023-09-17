import asyncio
import datetime
import logging
import sys
from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.utils.markdown import hbold
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
import tracker
import tracemalloc
import json
import re

tracemalloc.start()

TOKEN = ""
CHAT_ID = None
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)

form_router = Router()

class ADDTrip(StatesGroup):
    origin = State()
    destination = State()
    departureDate = State()

class TicketAction(StatesGroup):
    getTickets = State()
    isLooking = State()
    
@form_router.message(CommandStart())
async def commandStartHandler(message: Message) -> None:
    global CHAT_ID
    CHAT_ID = message.from_user.id
    await mainMenu(message)

@form_router.message(F.text == "home")
async def mainMenu(message: Message) -> None:
    newTripBtn = KeyboardButton(text="NewTrip")
    tripsBtn = KeyboardButton(text="ShowTrips")
    trainsBtn = KeyboardButton(text="ShowTrains")
    removeTripsBtn = KeyboardButton(text="RemoveTrips")
    mainKeyboard = ReplyKeyboardMarkup(keyboard=[[newTripBtn],[tripsBtn],[trainsBtn],[removeTripsBtn]],one_time_keyboard=True, resize_keyboard=True,is_persistent=True)
    await message.answer("گزینه مورد نظر را انتخاب کنید",reply_markup=mainKeyboard)

        
@form_router.message(F.text == "NewTrip")
async def addTripMessage(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ADDTrip.origin)
    await message.answer("مبدا مورد نظر را وارد کنید:",reply_markup=ReplyKeyboardRemove())

@form_router.message(ADDTrip.origin)
async def getTripOrigin(message: Message, state: FSMContext):
    await state.update_data(origin=message.text)
    await state.set_state(ADDTrip.destination)
    await message.answer("مقصد مورد نظر را وارد کنید:")

@form_router.message(ADDTrip.destination)
async def getTripDestination(message: Message,state: FSMContext):
    await state.update_data(destination=message.text)
    await state.set_state(ADDTrip.departureDate)
    await message.answer("تاریخ مورد نظر را به شمسی و با فرمت yyyy-mm-dd وارد کنید:")

@form_router.message(ADDTrip.departureDate)
async def getTripDepartureDate(message: Message,state: FSMContext):
    await state.update_data(departureDate=message.text)
    trip = await state.get_data()
    await state.clear()
    try:
        tracker.Trip(userOrigin=trip["origin"], userDestination=trip["destination"], userDate=trip["departureDate"]).to_dict()
        await message.answer("سفر جدید اضافه شد آن را بررسی کنید و در صورت نیاز آن را حذف و دوباره اضافه کنید!!!")
    except:
        await message.answer("ایجاد این مسیر امکان پذیر نیست")
    await mainMenu(message)




@form_router.message(F.text == "ShowTrips")
async def showTrips(message: Message):
    trips = tracker.showAllTrips()
    if len(trips) == 0:
        await message.answer(text="سفری ثبت نشده", reply_markup= await mainMenu(message))
    else:
        keys = []
        for trip_ in trips:
            keys.append([KeyboardButton(text=f"""اطلاعات مسیر
مبدا : {html.quote(trip_['faOrigin'])}
مقصد : {html.quote(trip_['faDestination'])}
تاریخ حرکت : {html.quote(trip_['faDepartureDate'])}""",)])
        tripsOptionsKB = ReplyKeyboardMarkup(keyboard=keys, one_time_keyboard=True, resize_keyboard=False)
        await message.answer('سفر مورد نظر را انتخاب کنید', reply_markup=tripsOptionsKB)

@form_router.message(F.text.startswith('اطلاعات مسیر'))
async def getTrains(message: Message, state: FSMContext):
    lines = message.text.split('\n')
    origin = lines[1].split(':')[1]
    destination = lines[2].split(':')[1]
    departureDate = lines[3].split(':')[1]
    tickets = []
    await state.set_state(TicketAction.getTickets)
    with open('trips.json') as f:
        trips = json.load(f)
        for trip_ in trips:
            if trip_['faOrigin'] == origin.strip() and trip_['faDestination'] == destination.strip() and trip_['faDepartureDate'] == departureDate.strip():
                token = trip_['token']
                tickets=tracker.getTripsTickets(token)
                await state.update_data(getTickets=tickets)
                keys = []
                for ticket_ in tickets:
                    keys.append([KeyboardButton(text=f"""بلیط قطار///زمان حرکت : {html.quote(ticket_['timeOfArrival'])}///هزینه : {html.quote(ticket_['cost'])}///تعداد صندلی موجود : {html.quote(ticket_['availableSeats'])} ///proposalId :{html.quote(ticket_['proposalId'])}""")])
                ticketOptionsKB = ReplyKeyboardMarkup(keyboard=keys, one_time_keyboard=True)
                await message.answer('قطار مورد نظر را انتخاب کنید:', reply_markup=ticketOptionsKB)
                break
        

@form_router.message(F.text.startswith('بلیط'))
async def ticketSituation(message: Message, state: FSMContext):
    proposalId = re.search(r'proposalId\s*:\s*(\d+)', message.text).group(1)
    tickets = await state.get_data()
    for ticket_ in tickets['getTickets']:
        if ticket_['proposalId'] == proposalId:
            tracker.Train(ticket_['proposalId'], ticket_['originName'], ticket_['destinationName'], ticket_['originCode'], ticket_['destinationCode'], ticket_['timeOfArrival'], ticket_['moveDatetime'], ticket_['cost'], ticket_['availableSeats']).to_dict()
            await message.answer(f"""اطلاعات قطار
مبدا : {html.quote(ticket_['originName'])}
مقصد : {html.quote(ticket_['destinationName'])}
تاریخ حرکت : {html.quote(ticket_['moveDatetime'])}
ساعت حرکت : {html.quote(ticket_['timeOfArrival'])}
تعداد صندلی ها موجود : {html.quote(ticket_['availableSeats'])}
قیمت : {html.quote(ticket_['cost'])}
این قطار به لیست قطار های تحت نظر اضافه شد. در صورت نیاز به تغییر قطار را حذف کرده و ذوباره ثبت کنید.""",reply_markup=await mainMenu(message))
            await state.clear()
            break

@form_router.message(F.text == "ShowTrains")           
async def showTrains(message: Message):
    trains = tracker.getSpecialTrains()
    if len(trains) == 0:
        await message.answer(text="قطاری ثبت نشده", reply_markup= await mainMenu(message))
    else:
        keys = []
        for train_ in trains:
            keys.append([KeyboardButton(text=f'''حذف قطار
مبدا : {html.quote(train_['originName'])}
مقصد : {html.quote(train_['destinationName'])}
ساعت حرکت : {html.quote(train_['timeOfArrival'])}
{html.quote(train_['proposalId'])}''')])
        await message.answer('قطار مورد نظر برای حذف را انتخاب کنید', reply_markup=ReplyKeyboardMarkup(keyboard=keys,one_time_keyboard=True))

@form_router.message(F.text.startswith("حذف قطار"))
async def removeTrain(message: Message):
    proposalId = message.text.split('\n')[-1]
    tracker.removeTrain(proposalId)
    await message.answer('قطار مورد نظر حذف شد', reply_markup=await mainMenu(message))

@form_router.message(F.text == 'RemoveTrips')
async def removeTrips(message: Message):
    trips = tracker.showAllTrips()
    if len(trips) == 0:
        await message.answer(text="سفری ثبت نشده", reply_markup= await mainMenu(message))
    else:
        keys = []
        for trip_ in trips:
            keys.append([KeyboardButton(text=f'''حذف سفر
مبدا : {html.quote(trip_['faOrigin'])}
مقصد : {html.quote(trip_['faDestination'])}
تاریخ حرکت : {html.quote(trip_['faDepartureDate'])} ''')])
        await message.answer('سفر مورد نظر برای حذف را انتخاب کنید',reply_markup=ReplyKeyboardMarkup(keyboard=keys,one_time_keyboard=True))


@form_router.message(F.text.startswith("حذف سفر"))
async def removeTripsAction(message: Message):
    lines = message.text.split('\n')
    origin = lines[1].split(':')[1].strip()
    destination = lines[2].split(':')[1].strip()
    departureDate = lines[3].split(':')[1].strip()
    tracker.removeTrip(origin, destination, departureDate)
    await message.answer('سفر مورد نظر حذف شد', reply_markup=await mainMenu(message))

async def checkTrips():
    trips = tracker.showAllTrips()
    if len(trips) > 0:
        for trip_ in trips:
            if datetime.datetime.strptime(trip_['departureDate'],'%Y-%m-%d').date() < datetime.datetime.now().date():
                tracker.removeTrip(trip_['faOrigin'],trip_['faDestination'],trip_['faDepartureDate'])
        for trip_ in trips:
            tickets = tracker.getTripsTickets(trip_['token'])
            if  tickets != None and len(tickets) > 0 :
                if tracker.isTrainTicketAvailable(tickets):
                    try:
                        await bot.send_message(chat_id=CHAT_ID,text=f'برای مسیر {html.quote(trip_["faOrigin"])}-{html.quote(trip_["faDestination"])} قطار پیدا شد')
                    except: pass

async def checkTrains():
    trains = tracker.getSpecialTrains()
    if len(trains)>0:
        for train_ in trains:
            if datetime.datetime.strptime(train_['moveDatetime'], '%Y-%m-%dT%H:%M:%S') < datetime.datetime.now():
                tracker.removeTrain(train_['proposalId'])
            token=tracker.getTripToken(train_['originCode'], train_['destinationCode'], str(datetime.datetime.strptime(train_['moveDatetime'],'%Y-%m-%dT%H:%M:%S').date()))
            try:
                tickets = tracker.getTripsTickets(token)
                if len(tickets) > 0:
                    for ticket_ in tickets:
                        if ticket_['timeOfArrival']==train_['timeOfArrival'] and ticket_['moveDatetime']==train_['moveDatetime'] and int(ticket_['availableSeats']) > 0:
                            try:
                                await bot.send_message(chat_id=CHAT_ID,text=f'جای خالی در قطار {html.quote(train_["originName"])} - {html.quote(train_["destinationName"])} ساعت {html.quote(train_["timeOfArrival"])} روز {html.quote(str(datetime.datetime.strptime(train_["moveDatetime"],"%Y-%m-%dT%H:%M:%S").date()))}')
                            except: pass
            except:
                try:
                    await bot.send_message(chat_id=CHAT_ID, text="سفر مربوط به یکی از قطار های مورد نظر حذف شده است. برای کارکرد درست ربات آن را مجددا به لیست سفر ها اضافه کنید")
                except: pass

async def check_loop():
    while True:
        await checkTrips()
        await checkTrains()
        await asyncio.sleep(60)

async def main() -> None:
    dp = Dispatcher()
    dp.include_router(form_router)
    await dp.start_polling(bot)
    
async def main_loop():
    await asyncio.gather(main(), check_loop())

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main_loop())