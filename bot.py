# import ccxt
# import pandas as pd
# import pandas_ta as ta
# import time
# bot = ccxt.ftxus({

#     'apiKey': '',

#     'secret': '',

# })
# timeframe = '5m'
# symbol = "DOGE/USD"


# rsi_low = 55
# volume_low = 5
# amount = 2.0


# def get_rsi():
#     while True:
#         try:
#             ohlcv = bot.fetch_ohlcv(symbol, timeframe)
#             if len(ohlcv):
#                 df = pd.DataFrame(
#                     ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
#                 df['time'] = pd.to_datetime(df['time'], unit='ms')
#                 df = pd.concat([df, df.ta.rsi()], axis=1)
#                 return df['RSI_14'].iloc[-1]
#         except Exception as e:
#             print(type(e).__name__, str(e))


# def get_volume():
#     while True:
#         try:
#             ohlcv = bot.fetch_ohlcv(symbol, timeframe)
#             if len(ohlcv):
#                 df = pd.DataFrame(
#                     ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
#                 df['time'] = pd.to_datetime(df['time'], unit='ms')
#                 return df['volume'].iloc[-1]
#         except Exception as e:
#             print(type(e).__name__, str(e))


# rsi = get_rsi()
# volume = get_volume()

# while True:
#     print('--------------------------------------------------------------')
#     print('RSI:', rsi)
#     print('Volume:', volume)
#     if rsi < rsi_low and volume < volume_low:
#         print(f'Buying {symbol} at {bot.fetch_ticker(symbol)["last"]}')
#         bot.create_market_buy_order(symbol, amount)
#         print(f'Bought {symbol} at {bot.fetch_ticker(symbol)["last"]}')
#     elif rsi > 5 and volume > volume_low:
#         print(f'Selling {symbol} at {bot.fetch_ticker(symbol)["last"]}')
#         bot.create_market_sell_order(symbol, amount)
#         print(f'Sold {symbol} at {bot.fetch_ticker(symbol)["last"]}')
#     else:
#         print('Waiting for conditions to be met, sleeping for 30 secs...')
#         print('--------------------------------------------------------------')
#         time.sleep(30)


#sentiment code

# # import for environment variables and waiting
from importlib import import_module
import os
from typing_extensions import Self
from unicodedata import name

# #from binance import BinanceSocketManager
# # used to parse XML feeds
import xml.etree.ElementTree as ET

# # we use it to make async http requests
import aiohttp

# # allows us to make our functions async
import asyncio

# # date modules that we'll most likely need
from datetime import date, datetime, timedelta

# # used to grab the XML url list from a CSV file
import csv


# # used to save and load coins_in_hand dictionary
import json

# # numpy for sums and means
import numpy as np

# # nlp library to analyse sentiment
import nltk

import pytz
from nltk.sentiment import SentimentIntensityAnalyzer
# import client
import hmac
import json
import time
import zlib
from collections import defaultdict, deque
from itertools import zip_longest
from typing import DefaultDict, Deque, List, Dict, Tuple, Optional
from gevent.event import Event

# from websocket.websocket_manager import WebsocketManager

# # needed for the binance API
# from binance.client import Client
# from binance.enums import *
# from binance.exceptions import BinanceAPIException, BinanceOrderException
from client import FtxWebsocketClient
# # used for binance websocket
# #from binance.websockets import BinanceSocketManager
# from binance import BinanceSocketManager
# #from binance import BinanceSocketManager
from twisted.internet import reactor

# # used for executing the code
from itertools import count

# # we use it to time our parser execution speed
from timeit import default_timer as timer

from client import FtxClient

# # Use testnet (change to True) or live (change to False)?
testnet = False

# # get binance key and secret from environment variables for testnet and live
# api_key_test = os.getenv('binance_api_stalkbot_testnet')
# api_secret_test = os.getenv('binance_secret_stalkbot_testnet')

api_key = os.getenv('')
api_secret = os.getenv('')

# #Authenticate with the client
# if testnet:
#     client = Client(api_key_test, api_secret_test)
# else:
#     client = Client(api_key_live, api_secret_live)

# # The API URL is manually changed in the library to work on the testnet
# if testnet:
#     client.API_URL = 'https://testnet.binance.vision/api'
from threading import Thread, Lock

from websocket import WebSocketApp
from websocket_manager import WebsocketManager


import requests
import ccxt
import pandas as pd
import pandas_ta as ta
import time


# bot = ccxt.ftxus({

#     'apiKey': '',

#     'secret': '',

# })

# ############################################
# #     USER INPUT VARIABLES LIVE BELOW      #
# # You may edit those to configure your bot #
# ############################################


# # select what coins to look for as keywords in articles headlines
# # The key of each dict MUST be the symbol used for that coin on Binance
# # Use each list to define keywords separated by commas: 'XRP': ['ripple', 'xrp']
# # keywords are case sensitive
keywords = {
    'XRP': ['ripple', 'xrp', 'XRP', 'Ripple', 'RIPPLE'],
    'BTC': ['BTC', 'bitcoin', 'Bitcoin', 'BITCOIN'],
    'XLM': ['Stellar Lumens', 'XLM'],
    #'BCH': ['Bitcoin Cash', 'BCH'],
    'ETH': ['ETH', 'Ethereum'],
    'BNB' : ['BNB', 'Binance Coin'],
    'LTC': ['LTC', 'Litecoin'],
    'SOL': ['SOL', 'Solana'],
    'DOGE': ['DOGE', 'Dogecoin'],
#     'APE': ['DOGE', 'Apecoin']
    }

# # The Buy amount in the PAIRING symbol, by default USDT
# # 100 will for example buy the equivalent of 100 USDT in Bitcoin.
QUANTITY = 1

# # define what to pair each coin to
# # AVOID PAIRING WITH ONE OF THE COINS USED IN KEYWORDS
PAIRING = 'USD'

# # define how positive the news should be in order to place a trade
# # the number is a compound of neg, neu and pos values from the nltk analysis
# # input a number between -1 and 1
SENTIMENT_THRESHOLD = 0
NEGATIVE_SENTIMENT_THRESHOLD = 0

# # define the minimum number of articles that need to be analysed in order
# # for the sentiment analysis to qualify for a trade signal
# # avoid using 1 as that's not representative of the overall sentiment
MINUMUM_ARTICLES = 1

# # define how often to run the code (check for new + try to place trades)
# # in minutes
REPEAT_EVERY = 2

# # define how old an article can be to be included
# # in hours
HOURS_PAST = 2400


# ############################################
# #        END OF USER INPUT VARIABLES       #
# #             Edit with care               #
# ############################################





# coins that bought by the bot since its start
coins_in_hand  = {}

# path to the saved coins_in_hand file
coins_in_hand_file_path = 'coins_in_hand.json'

# use separate files for testnet and live
if testnet:
    coins_in_hand_file_path = 'testnet_' + coins_in_hand_file_path

# if saved coins_in_hand json file exists then load it
if os.path.isfile(coins_in_hand_file_path):
    with open(coins_in_hand_file_path) as file:
        coins_in_hand = json.load(file)

# and add coins from actual keywords if they aren't in coins_in_hand dictionary already
for coin in keywords:
    if coin not in coins_in_hand:
        coins_in_hand[coin] = 0

# current price of CRYPTO pulled through the websocket
CURRENT_PRICE = {}


def get_markets(msg):
    '''Open a stream for financial information for CRYPTO'''
    if msg['e'] != 'error':
        global CURRENT_PRICE
        CURRENT_PRICE['{0}'.format(msg['s'])] = msg['c']
    else:
        print('error')





#  # connect to the websocket client and start the socket
# bsm = BinanceSocketManager(client)
# for coin in keywords:
#     conn_key = bsm.start_symbol_ticker_socket(coin+PAIRING, ticker_socket)
# bsm.start()

bsm = WebsocketManager._connect
for coin in keywords:
    conn_key = bsm.get_markets(coin+PAIRING,  )
# bsm.start()


'''For the amount of CRYPTO to trade in USDT'''
lot_size = {}

'''Find step size for each coin
For example, BTC supports a volume accuracy of
0.000001, while XRP only 0.1
'''
for coin in keywords:

    try:
        info = Self.get_symbol_info(coin+PAIRING)
        step_size = info['filters'][2]['stepSize']
        lot_size[coin+PAIRING] = step_size.index('1') - 1

        if lot_size[coin+PAIRING]<0:
            lot_size[coin+PAIRING]=0

    except:
        pass
for coin in keywords:
    try:
        info = Self.get_symbol_info(coin)
        step_size = info['filters'][2]['stepSize']
        lot_size[coin] = step_size.index('1') - 1

        if lot_size[coin]<0:
            lot_size[coin]=0

    except:
        pass



def calculate_one_volume_from_lot_size(coin, amount):
    if coin not in lot_size:
        return float('{:.1f}'.format(amount))

    else:
        return float('{:.{}f}'.format(amount, lot_size[coin]))


def calculate_volume():
    while CURRENT_PRICE == {}:
        print('Connecting to the socket...')
        time.sleep(3)

    else:
        volume = {}
        for coin in CURRENT_PRICE:
            volume[coin] = float(QUANTITY / float(CURRENT_PRICE[coin]))
            volume[coin] = calculate_one_volume_from_lot_size(coin, volume[coin])

        return volume


# load the csv file containg top 100 crypto feeds
# want to scan other websites?
# Simply add the RSS Feed url to the Crypto feeds.csv file
with open('Crypto feeds.csv') as csv_file:

    # open the file
    csv_reader = csv.reader(csv_file)

    # remove any headers
    next(csv_reader, None)

    # create empty list
    feeds = []

    # add each row cotaining RSS url to feeds list
    for row in csv_reader:
        feeds.append(row[0])


# Make headlines global variable as it should be the same across all functions
headlines = {'source': [], 'title': [], 'pubDate' : [] }


async def get_feed_data(session, feed, headers):
    '''
    Get relevent data from rss feed, in async fashion
    :param feed: The name of the feed we want to fetch
    :param headers: The header we want on the request
    :param timeout: The default timout before we give up and move on
    :return: None, we don't need to return anything we append it all on the headlines dict
    '''
    try:
        async with session.get(feed, headers=headers, timeout=60) as response:
            # define the root for our parsing
            text = await response.text()
            root = ET.fromstring(text)

            channel = root.find('channel/item/title').text
            pubDate = root.find('channel/item/pubDate').text
            # some jank to ensure no alien characters are being passed
            title = channel.encode('UTF-8').decode('UTF-8')

            # convert pubDat to datetime
            published = datetime.strptime(pubDate.replace("GMT", "+0000"), '%a, %d %b %Y %H:%M:%S %z')
            # calculate timedelta
            time_between = datetime.now(pytz.utc) - published

            #print(f'Czas: {time_between.total_seconds() / (60 * 60)}')

            if time_between.total_seconds() / (60 * 60) <= HOURS_PAST:
                # append the source
                headlines['source'].append(feed)
                # append the publication date
                headlines['pubDate'].append(pubDate)
                # append the title
                headlines['title'].append(title)
                print(channel)

    except Exception as e:
        # Catch any error and also print it
        print(f'Could not parse {feed} error is: {e}')


async def get_headlines():
    '''
    Creates a an async task for each of our feeds which are appended to headlines
    :return: None
    '''
    # add headers to the request for ElementTree. Parsing issues occur without headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'
    }

    # A nifty timer to see how long it takes to parse all the feeds
    start = timer()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for feed in feeds:
            task = asyncio.ensure_future(get_feed_data(session, feed, headers))
            tasks.append(task)

        # This makes sure we finish all tasks/requests before we continue executing our code
        await asyncio.gather(*tasks)
    end = timer()
    print("Time it took to parse feeds: ", end - start)


def categorise_headlines():
    '''arrange all headlines scaped in a dictionary matching the coin's name'''
    # get the headlines
    asyncio.run(get_headlines())
    categorised_headlines = {}

    # this loop will create a dictionary for each keyword defined
    for keyword in keywords:
        categorised_headlines['{0}'.format(keyword)] = []

    # keyword needs to be a loop in order to be able to append headline to the correct dictionary
    for keyword in keywords:

        # looping through each headline is required as well
        for headline in headlines['title']:
            # appends the headline containing the keyword to the correct dictionary
            if any(key in headline for key in keywords[keyword]):
                categorised_headlines[keyword].append(headline)

    return categorised_headlines


def analyse_headlines():
    '''Analyse categorised headlines and return NLP scores'''
    sia = SentimentIntensityAnalyzer()
    categorised_headlines = categorise_headlines()

    sentiment = {}

    for coin in categorised_headlines:
        if len(categorised_headlines[coin]) > 0:
            # create dict for each coin
            sentiment['{0}'.format(coin)] = []
            # append sentiment to dict
            for title in categorised_headlines[coin]:
                sentiment[coin].append(sia.polarity_scores(title))

    return sentiment


def compile_sentiment():
    '''Arranges every compound value into a list for each coin'''
    sentiment = analyse_headlines()
    compiled_sentiment = {}

    for coin in sentiment:
        compiled_sentiment[coin] = []

        for item in sentiment[coin]:
            # append each compound value to each coin's dict
            compiled_sentiment[coin].append(sentiment[coin][sentiment[coin].index(item)]['compound'])

    return compiled_sentiment


def compound_average():
    '''Calculates and returns the average compoud sentiment for each coin'''
    compiled_sentiment = compile_sentiment()
    headlines_analysed = {}

    for coin in compiled_sentiment:
        headlines_analysed[coin] = len(compiled_sentiment[coin])

        # calculate the average using numpy if there is more than 1 element in list
        compiled_sentiment[coin] = np.array(compiled_sentiment[coin])

        # get the mean
        compiled_sentiment[coin] = np.mean(compiled_sentiment[coin])

        # convert to scalar
        compiled_sentiment[coin] = compiled_sentiment[coin].item()

    return compiled_sentiment, headlines_analysed




def buy(compiled_sentiment, headlines_analysed):
    '''Check if the sentiment is positive and keyword is found for each handle'''
    volume = calculate_volume()
    for coin in compiled_sentiment:


        # check if the sentiment and number of articles are over the given threshold
        if compiled_sentiment[coin] > SENTIMENT_THRESHOLD and headlines_analysed[coin] >= MINUMUM_ARTICLES and coins_in_hand[coin]==0:
            # check the volume looks correct
            print(f'preparing to buy {volume[coin+PAIRING]} {coin} with {PAIRING} at {CURRENT_PRICE[coin+PAIRING]}')

            if (testnet):
                # create test order before pushing an actual order
                test_order = Self.create_test_order(symbol=coin+PAIRING, side='BUY', type='MARKET', quantity=volume[coin+PAIRING])

            # try to create a real order if the test orders did not raise an exception
            try:
                buy_limit = Self.create_order(
                    symbol=coin+PAIRING,
                    side='BUY',
                    type='MARKET',
                    quantity=volume[coin+PAIRING]
                )

            #error handling here in case position cannot be placed
            except Exception as e:
                print(e)

            # run the else block if the position has been placed and return some info
            else:
                # adds coin to our portfolio
                coins_in_hand[coin] += volume[coin+PAIRING]

                # retrieve the last order
                order = Self.get_all_orders(symbol=coin+PAIRING, limit=1)

                if order:
                    # convert order timsestamp into UTC format
                    time = order[0]['time'] / 1000
                    utc_time = datetime.fromtimestamp(time)

                    # grab the price of CRYPTO the order was placed at for reporting
                    bought_at = CURRENT_PRICE[coin+PAIRING]

                    # print order condirmation to the console
                    print(f"order {order[0]['orderId']} has been placed on {coin} with {order[0]['origQty']} at {utc_time} and bought at {bought_at}")
                else:
                    print('Could not get last order from Binance!')

        else:
            print(f'Sentiment not positive enough for {coin}, or not enough headlines analysed or already bought: {compiled_sentiment[coin]}, {headlines_analysed[coin]}')




def sell(compiled_sentiment, headlines_analysed):
    '''Check if the sentiment is negative and keyword is found for each handle'''
    for coin in compiled_sentiment:

        # check if the sentiment and number of articles are over the given threshold
        if compiled_sentiment[coin] < NEGATIVE_SENTIMENT_THRESHOLD and headlines_analysed[coin] >= MINUMUM_ARTICLES and coins_in_hand[coin]>0:

            # check the volume looks correct
            print(f'preparing to sell {coins_in_hand[coin]} {coin} at {CURRENT_PRICE[coin+PAIRING]}')

            amount_to_sell = calculate_one_volume_from_lot_size(coin+PAIRING, coins_in_hand[coin]*99.5/100)

            if (testnet):
                # create test order before pushing an actual order
                test_order = Self.create_test_order(symbol=coin+PAIRING, side='SELL', type='MARKET', quantity=amount_to_sell)

            # try to create a real order if the test orders did not raise an exception
            try:
                buy_limit = Self.create_order(
                    symbol=coin+PAIRING,
                    side='SELL',
                    type='MARKET',
                    quantity=amount_to_sell
                )

            #error handling here in case position cannot be placed
            except Exception as e:
                print(e)

            # run the else block if the position has been placed and return some info
            else:
                # set coin to 0
                coins_in_hand[coin]=0
                # retrieve the last order
                order = Self.get_all_orders(symbol=coin+PAIRING, limit=1)

                if order:
                    # convert order timsestamp into UTC format
                    time = order[0]['time'] / 1000
                    utc_time = datetime.fromtimestamp(time)

                    # grab the price of CRYPTO the order was placed at for reporting
                    sold_at = CURRENT_PRICE[coin+PAIRING]

                    # print order condirmation to the console
                    print(f"order {order[0]['orderId']} has been placed on {coin} with {order[0]['origQty']} coins sold for {sold_at} each at {utc_time}")
                else:
                    print('Could not get last order from Binance!')

        else:
            print(f'Sentiment not negative enough for {coin}, not enough headlines analysed or not enough {coin} to sell: {compiled_sentiment[coin]}, {headlines_analysed[coin]}')


def save_coins_in_hand_to_file():
    # abort saving if dictionary is empty
    if not coins_in_hand:
        return

    # save coins_in_hand to file
    with open(coins_in_hand_file_path, 'w') as file:
        json.dump(coins_in_hand, file, indent=4)



if __name__ == '__main__':
    print('Press Ctrl-Q to stop the script')
    for i in count():
        compiled_sentiment, headlines_analysed = compound_average()
        print("\nBUY CHECKS:")
        buy(compiled_sentiment, headlines_analysed)
        print("\nSELL CHECKS:")
        sell(compiled_sentiment, headlines_analysed)
        print('\nCurrent bot holdings: ')
        for coin in coins_in_hand:
            if coins_in_hand[coin] > 0:
                print(f'{coin}: {coins_in_hand[coin]}')
        save_coins_in_hand_to_file()
        print(f'\nIteration {i}')
        time.sleep(60 * REPEAT_EVERY)