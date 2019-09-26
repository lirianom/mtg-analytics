'''
db_init.py

functions used to initalize the mongo_cards and mongo_sets databases.

get_cards()
insert_cards(cards)
get_total_cards()
get_sets()
insert_sets(sets)
get_total_sets()

@Author Martin Liriano
'''
import requests
import json
import configparser
import pymongo as mongo

config = configparser.ConfigParser()
config.read('config.ini')

#database initialization
'''
mongo_cards is
    {
        '_id' : Number,
        'prouductId' : List[Number],
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
mongo_sets = card_db['sets']

#general header used for tcgplayer api calls
header = {
    'Accept': 'application/json',
    'Authorization': 'bearer ' + str(config ['tcgplayer']['bearertoken']),
}

#urls used throughout files to call tcgplayer api
url_for_cards = config['tcgplayer']['tcgplayer-url-cards']
url_for_sets = config['tcgplayer']['tcgplayer-url-sets']

#count used to create id's for database rows
card_id = 1
set_id = 1

'''
get_cards() :
    gets all the cards (max 250 per API requirements) and inserts them to the insert_cards() function.
    Sends 250 cards at a time and then uses offset to get the next batch of cards.
'''
def get_cards() :
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
insert_cards(cards) :
    inserts Magic the Gathering cards into MongoDB instance initilized above. Document is formatted as follows -
    {
        '_id' : Number,
        'prouductId' : Number,
        'name' : String,
        'setId' : Number,
        'setName' : String,
        'imageUrl' : String,
        'price_list' : List[{date, Number}]
    }
'price_list' is initialized to an empty array here
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
                    mongo_cards.insert_one(products)
                    card_id += 1
                        
                add = False

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
get_sets() :
    gets all the sets (max 10 per API requirements) and inserts them to the insert_sets() function.
    Sends 10 sets at a time and then uses offset to get the next batch of sets.
'''
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

'''
insert_sets(sets) :
    inserts Magic the Gathering sets into MongoDB instance initilized above. Document is formatted as follows -
    {
        '_id' : Number,
        'setId' : Number,
        'name' : String,
        'abbreviation' : String
    }
'''
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

'''
get_total_sets() :
    gets a count of all the Magic the Gathering sets in the tcgplayer databse
'''
def get_total_sets() :
    #Total Sets 244
    req_for_total_sets = requests.get(url_for_sets + '?categoryId=1', headers = header)
    response_json_sets = json.loads(req_for_total_sets.text)
    return response_json_sets['totalItems']

'''
def init() :
    initializes mongo_cards and mongo_sets database
'''
def init() :
    get_sets()
    get_cards()