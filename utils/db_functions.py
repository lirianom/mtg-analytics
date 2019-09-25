'''
db_functions.py

@Author Martin Liriano
'''

import requests
import json
import configparser
import pymongo as mongo
import datetime

config = configparser.ConfigParser()
config.read('config.ini')

#database initialization
'''
mongo_cards is
    {
        '_id' : Number,
        'prouductId' : Number,
        'name' : String,
        'setId' : Number,
        'setName' : String,
        'imageUrl' : String,
        'price_list' : List[{date, Number}]
    }
'''
dbclient = mongo.MongoClient()
card_db = dbclient['card_db']
mongo_cards = card_db['cards']

#general header used for tcgplayer api calls
header = {
    'Accept': 'application/json',
    'Authorization': 'bearer ' + str(config ['tcgplayer']['bearertoken']),
}

#urls used throughout file to call tcgplayer API
url_for_price = config['tcgplayer']['tcgplayer-url-price']

price_list = {}

'''
update_price() :
    updates the 'price_list' in each row in the MongoDB. This function should be called once a week as it is meant
    to see the delta's of each card's price week by week.

    Uses init_cards_prices() to populate global price_list dictionary then iterates 
    through price_list dictionary and updates the mongo_cards database with price information for each card

Only adds cards with 'marketPrice'
'''
def update_price() :
    _products = ''
    product_count = 0
    global price_list

    for cards in mongo_cards.find() :
        _products += str(cards['productId']) + ','
        product_count += 1
        if product_count == 250 :
            req_for_price = requests.get(url_for_price + _products, headers = header)
            response_json_price = json.loads(req_for_price.text)['results']
            init_card_prices(response_json_price)
            _products = ''
            product_count = 0
    for productId, price_list_item in price_list.items() :
        mongo_cards.find_one_and_update(
            {
                'productId' : productId
            },
            {
                '$push' :
                {
                    'price_list' : price_list_item
                }
            }
        )

'''
init_card_prices(prices) :
    helper function for update_price(). Takes in prices json converts it to list and then iterates through it
    adding all prices to the global price_list dictionary.
'''
def init_card_prices(prices) :
    now = datetime.date.today()
    list_price = list(prices)
    price_iterator = iter(list_price)
    global price_list
    for card_price in price_iterator :
        price_exist = price_list.get(card_price['productId'])
        normal_price = 0.00
        foil_price = 0.00
        got_foil = False
        got_normal = False
        if card_price['subTypeName'] == 'Normal' and card_price['marketPrice'] is not None :
            normal_price = card_price['marketPrice']
            got_normal = True
        if card_price['subTypeName'] == 'Foil' and card_price['marketPrice'] is not None :
            foil_price = card_price['marketPrice']
            got_foil = True
        if price_exist is None :
            prices = {
                        card_price['productId'] : 
                            [{
                                'date' : str(now),
                                'foil-price' : foil_price,
                                'normal-price' : normal_price
                            }]
                    }
            price_list.update(prices)
        elif price_exist is not None :
            if not got_foil :
                price_list[card_price['productId']][0]['normal-price'] = normal_price
            elif not got_normal :
                price_list[card_price['productId']][0]['foil-price'] = foil_price

'''
drop_table() :
    function that drops the mongo_cards collection. 
    Only used for testing and to repopulate database afterwards.
'''
def drop_tables() :
    print('dropping mongo_cards and mongo_sets...')
    mongo_cards.drop()
    card_db['sets'].drop()

def print_cards() :
        for x in mongo_cards.find() :
                print(x)