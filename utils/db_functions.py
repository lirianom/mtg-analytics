'''
db_functions.py
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
import csv

config = configparser.ConfigParser()
config.read('config.ini')

#database initialization
'''
card_row is
        {
                '_id' : Number,
                'prouductId' : Array[Number],
                'name' : String,
                'imageUrl' : String,
                'price_list' : Array[{date, Number}]
        }
'''
dbclient = mongo.MongoClient()
card_db = dbclient['card_db']
card_row = card_db['cards']

#general header used for tcgplayer api calls
header = {
        'Accept': 'application/json',
        'Authorization': 'bearer ' + str(config ['tcgplayer']['bearertoken']),
}

#urls used throughout file to call tcgplayer API
url_for_cards = config['tcgplayer']['tcgplayer-url-cards']
url_for_price = config['tcgplayer']['tcgplayer-url-price']

#count used to create id's for database rows
count = 1

'''
get_product() :
        gets all the cards (max 250 per API requirements) and them to the insert_cards() function.
        Sends 250 cards at a time and then uses offset to get the next batch of cards.

FUNCTION SHOULD ONLY BE CALLED ONCE TO INITIALIZE DATABASE
'''
def get_product() :
        #total cards 44753
        paging_num = 0
        url_append_for_cards = '?getExtendedFields=True&categoryId=1&productTypes=Cards&limit=250&offset=' + str(paging_num)

        total_cards = get_total_cards()

        while total_cards > 0 :
                req_for_cards = requests.get(url_for_cards + url_append_for_cards, headers=header)
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
        url_append_for_cards = '?categoryId=1&productTypes=Cards&limit=250'
        req_for_total_cards = requests.get(url_for_cards + url_append_for_cards, headers=header)
        response_json_cards = json.loads(req_for_total_cards.text)
        return response_json_cards['totalItems']

'''
insert_cards(cards) :
        inserts Magic the Gathering cards into MongoDB instance initilized above. Document is formatted as follows -
        {
                '_id' : Number,
                'prouductId' : Array[Number],
                'name' : String,
                'imageUrl' : String,
                'price_list' : Array[{date, Number}]
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
        global count
        add = False
        printData = ''

        for value_cards in cards['results'] :
                if value_cards['extendedData'] is not None and len(value_cards['extendedData']) > 0 :
                        for card_data in value_cards['extendedData'] :
                                if card_data['name'] == 'Rarity' :
                                        if card_data['value'] == 'C' or card_data['value'] == 'U' or card_data['value'] == 'R' or card_data['value'] == 'M' :
                                                add = True
                                                printData = str(card_data)
                if add :
                        print('Card ID = ' + str(value_cards['productId']) + ' || Card Data = ' + str(printData))
                        if card_row.find_one(
                                {
                                        'name' : value_cards['cleanName']
                                }
                        ) :
                                card_row.find_one_and_update(
                                        {
                                                'name' : value_cards['cleanName']
                                        },
                                        {
                                                '$push' :
                                                        {
                                                                'productId' : value_cards['productId']
                                                        }
                                        }
                                )
                        else :
                                products = {
                                        '_id' : count,
                                        'productId' : [value_cards['productId']],
                                        'name' : value_cards['cleanName'],
                                        'imageUrl' : value_cards['imageUrl'],
                                        'price_list' : []
                                }
                                card_row.insert_one(products)
                                count += 1
                        
                add = False

'''
update_price() :
        updates the 'price_list' in each row in the MongoDB. This function should be called once a week as it is meant
        to see the delta's of each card's price week by week.

        This function queries the tcgplayer api with each 'productId' in each row in the MongoDB database and average's
        out the price returned. Then uses $push to update that row's 'price_list'

Should be changed to median then average
Only adds Non-Foil Cards
Only adds cards with 'marketPrice'
'''
def update_price() :
        _products = ''
        now = datetime.date.today()

        for card_row in card_row.find() :
                total_price = 0
                total_cards = 0
                avg = 0
                for card_id in card_row['productId'] :
                        _products += str(card_id) + ','
                        total_cards += 1
                req_for_price = requests.get(url_for_price + _products, headers=header)
                response_json_price = json.loads(req_for_price.text)

                for card_price in response_json_price['results'] :
                        if card_price['subTypeName'] == 'Normal' and card_price['marketPrice'] is not None :
                                total_price += card_price['marketPrice']

                avg = total_price / total_cards

                card_row.find_one_and_update(
                        {
                                '_id' : card_row['_id']
                        },
                        {
                                '$push' : 
                                {
                                        'price_list' : {'date' : str(now), 'price' : avg}
                                }
                        }
                )
                _products = ''

'''
drop_table() :
        function that drops the card_row collection. 
Only used for testing and to repopulate database afterwards.
'''
def drop_table() :
        print('dropping card_row')
        card_row.drop()