'''
db_test_functions.py
General functions meant to do basic queries to MongoDB instance.

get_product()
get_total_cards()
insert_cards(cards)
update_price()
drop_table()

@Author Martin Liriano

'''

import requests
import json
import configparser
import pymongo as mongo
import datetime
import util as util_functions

config = configparser.ConfigParser()
config.read('config.ini')

dbclient = mongo.MongoClient()
card_db = dbclient['card_db']
mongo_cards_test = card_db['cards_test']
mongo_sets = card_db['sets']

#general header used for tcgplayer api calls
header = {
    'Accept': 'application/json',
    'Authorization': 'bearer ' + str(config ['tcgplayer']['bearertoken']),
}

#urls used throughout file to call tcgplayer API
url_for_cards = config['tcgplayer']['tcgplayer-url-cards']
url_for_price = config['tcgplayer']['tcgplayer-url-price']

#dictionary used to store price data temporarily
price_list = {}

'''
get_product() :
    gets all the cards (max 250 per API requirements) and them to the insert_cards() function.
    Sends 250 cards at a time and then uses offset to get the next batch of cards.

FUNCTION SHOULD ONLY BE CALLED ONCE TO INITIALIZE DATABASE
'''
def get_product() :
    paging_num = 0
    url_append_for_cards = '?getExtendedFields=True&categoryId=1&productTypes=Cards&limit=250&offset=' + str(paging_num)

    total_cards = get_total_cards()

    while total_cards > 0 :
        req_for_cards = requests.get(url_for_cards + url_append_for_cards, headers = header)
        response_json_cards = json.loads(req_for_cards.text)
        insert_cards(response_json_cards)
        total_cards -= 250
        paging_num += 250
        url_append_for_cards = '?getExtendedFields=True&categoryId=1&productTypes=Cards&limit=250&offset=' + str(paging_num)

'''
get_total_cards() :
        gets a count of all the Magic the Gathering cards stored in the tcgplayer database
'''
def get_total_cards() :
    #total cards 44753
    url_append_for_cards = '?categoryId=1&productTypes=Cards&limit=250'
    req_for_total_cards = requests.get(url_for_cards + url_append_for_cards, headers=header)
    response_json_cards = json.loads(req_for_total_cards.text)
    return response_json_cards['totalItems']

'''
insert_cards(cards) :
    inserts Magic the Gathering cards into MongoDB instance initilized above. Document is formatted as follows -
    {
        '_id' : Number,
        'prouductId' : List[Number],
        'name' : String,
        'imageUrl' : String,
        'price_list' : List[{date, Number}]
    }
    Before values are inserted database is queried to make sure that card isn't in the database -
    If card is in database 
            that card's productId is appended to that card's row
    else
        create new row in database

'price_list' is initialized to an empty array here
FUNCTION SHOULD ONLY BE CALLED ONCE TO INITIALIZE DATABASE
'''
def insert_cards(cards) :
    #INITIAL ADD
    global card_id
    add = False

    for value_cards in cards['results'] :
        if value_cards['extendedData'] is not None and len(value_cards['extendedData']) > 0 :
            for card_data in value_cards['extendedData'] :
                if card_data['name'] == 'Rarity' :
                    if card_data['value'] == 'C' or card_data['value'] == 'U' or card_data['value'] == 'R' or card_data['value'] == 'M' :
                        add = True
                if add :
                    set_name = mongo_sets.find_one(
                        {
                            'setId' : value_cards['groupId']
                        }
                    )['name']
                    products = {
                        '_id' : card_id,
                        'productId' : value_cards['productId'],
                        'setId' : value_cards['groupId'],
                        'setName' : set_name,
                        'name' : value_cards['cleanName'],
                        'imageUrl' : value_cards['imageUrl'],
                        'price_list' : []
                    }
                    mongo_cards_test.insert_one(products)
                    card_id += 1
                        
                add = False

'''
update_price() :
    updates the 'price_list' in each row in the MongoDB. This function should be called once a week as it is meant
    to see the delta's of each card's price week by week.

    This function queries the tcgplayer api with each 'productId' in each row in the MongoDB database and average's
    out the price returned. Then uses $push to update that row's 'price_list'

Only adds cards with 'marketPrice'
'''
def update_price() :
    _products = ''
    product_count = 0
    global price_list

    for cards in mongo_cards_test.find() :
        _products += str(cards['productId']) + ','
        product_count += 1
        if product_count == 250 :
            req_for_price = requests.get(url_for_price + _products, headers = header)
            response_json_price = json.loads(req_for_price.text)['results']
            init_card_prices(response_json_price)
            _products = ''
            product_count = 0
    for productId, price_list_item in price_list.items() :
        mongo_cards_test.find_one_and_update(
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
        #print(price_list[card_price['productId']])

'''
drop_table() :
    function that drops the mongo_cards collection. 
Only used for testing and to repopulate database afterwards.
'''
def drop_table() :
    print('dropping mongo_cards_test...')
    mongo_cards_test.drop()

def get_total_sets() :
    #Total Sets 244
    req_for_total_sets = requests.get(url_for_sets + '?categoryId=1', headers = header)
    response_json_sets = json.loads(req_for_total_sets.text)
    return response_json_sets['totalItems']

def get_sets() :
    offset = 0
    total_sets = get_total_sets()
    url_append_for_sets = '?categoryId=1&offset=' + str(offset)
    while total_sets > 0 :
        req_for_sets = requests.get(url_for_sets + url_append_for_sets, headers = header)
        response_json_sets = json.loads(req_for_sets.text)
        insert_sets(response_json_sets)
        offset += 10
        total_sets -= 10
        url_append_for_sets = '?categoryId=1&offset=' + str(offset)


def insert_sets(sets) :
    global set_id
    for value_sets in sets['results'] :
        sets = {
                '_id' : set_id,
                'setId' : value_sets['groupId'],
                'name' : value_sets['name'],
                'abbreviation' : value_sets['abbreviation']
        }
        mongo_sets.insert_one(sets)
        set_id += 1

def get_cards_api() :
    all_cards = []
    card_keys = list(mongo_cards_test.find_one().keys())
    for cards in mongo_cards_test.find() :
        temp = {}
        temp[card_keys[0]] = cards[card_keys[0]]
        temp[card_keys[1]] = cards[card_keys[1]]
        temp[card_keys[2]] = cards[card_keys[2]]
        temp[card_keys[3]] = cards[card_keys[3]]
        temp[card_keys[4]] = cards[card_keys[4]]
        temp[card_keys[5]] = cards[card_keys[5]]
        temp['price'] = cards[card_keys[6]][0]['price']
        all_cards.append(temp)
    return all_cards


def get_sets_api() :
    return mongo_sets.find()

def printCards() :
    for x in mongo_cards_test.find() :
        print(x)

def init() :
    drop_table()
    get_product()
    update_price()