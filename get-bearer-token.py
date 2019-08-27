import requests
import json
import configparser
import pymongo as mongo
import datetime
import util as util_functions
import card_db_functions as db_functions
import csv

config = configparser.ConfigParser()
config.read('config.ini')
dbclient = mongo.MongoClient()
card_db = dbclient['card_db']
card_col = card_db['cards']
now = datetime.date.today()
header = {
        'Accept': 'application/json',
        'Authorization': 'bearer ' + str(config ['tcgplayer-api-secret']['bearertoken']),
}
url_for_mtg_cards = 'http://api.tcgplayer.com/v1.27.0/catalog/products'
url_for_price = 'http://api.tcgplayer.com/v1.27.0/pricing/product/'
count = 1

def get_bearer_token() :
        if (util_functions.is_time_greater(config['tcgplayer-api-secret']['bearertoken_time'])) :
                return config['tcgplayer-api-secret']['bearertoken']
        else :
                url = 'https://api.tcgplayer.com/token'

                header = {
                        'grant_type': 'client_credentials',
                        'client_id': config['tcgplayer-api-secret']['publickey'],
                        'client_secret': config['tcgplayer-api-secret']['privatekey'],
                }
                req = requests.post(url, data=header)
                response_json = json.loads(req.text)
                config['tcgplayer-api-secret']['bearertoken'] = response_json['access_token']
                config['tcgplayer-api-secret']['bearertoken_time'] = response_json['.expires']
                with open('config.ini', 'w') as config_file:
                        config.write(config_file)
                return config['tcgplayer-api-secret']['bearertoken']

'''
def drop_table() :
        card_col.drop()
        print('Table has been dropped')

def get_total_cards() :
        header = {
                'Accept': 'application/json',
                'Authorization': 'bearer ' + str(config['tcgplayer-api-secret']['bearertoken']),
        }
        url_for_mtg_cards = 'http://api.tcgplayer.com/v1.27.0/catalog/products'
        url_append_for_cards = '?categoryId=1&productTypes=Cards&limit=250'
        req_for_total_cards = requests.get(url_for_mtg_cards + url_append_for_cards, headers=header)
        response_json_cards = json.loads(req_for_total_cards.text)
        return response_json_cards['totalItems']

def insert_cards(json_obj) :
        #INITIAL ADD
        response_json_cards = json_obj
        global count
        add = False
        printData = ''

        for value_cards in response_json_cards['results'] :
                if value_cards['extendedData'] is not None and len(value_cards['extendedData']) > 0 :
                        for card_data in value_cards['extendedData'] :
                                if card_data['name'] == 'Rarity' :
                                        if card_data['value'] == 'C' or card_data['value'] == 'U' or card_data['value'] == 'R' or card_data['value'] == 'M' :
                                                add = True
                                                printData = str(card_data)
                if add :
                        print('Card ID = ' + str(value_cards['productId']) + ' || Card Data = ' + str(printData))
                        if card_col.find_one(
                                {
                                        'name' : value_cards['cleanName']
                                }
                        ) :
                                card_col.find_one_and_update(
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
                                card_col.insert_one(products)
                                count += 1
                        
                add = False
                #print(temp_list)



def get_product() :
        #total cards 44753
        paging_num = 0
        url_append_for_cards = '?getExtendedFields=True&categoryId=1&productTypes=Cards&limit=250&offset=' + str(paging_num)

        total_cards = get_total_cards()

        while total_cards > 0 :
                req_for_cards = requests.get(url_for_mtg_cards + url_append_for_cards, headers=header)
                response_json_cards = json.loads(req_for_cards.text)
                #print(response_json_cards)
                insert_cards(response_json_cards)
                total_cards -= 250
                paging_num += 250
                url_append_for_cards = '?getExtendedFields=True&categoryId=1&productTypes=Cards&limit=250&offset=' + str(paging_num)

def update_price() :
        header = {
                'Accept': 'application/json',
                'Authorization': 'bearer ' + str(config['tcgplayer-api-secret']['bearertoken']),
        }

        url_for_price = 'http://api.tcgplayer.com/v1.32.0/pricing/product/'
        _products = ''

        for card_row in card_col.find() :
                total_price = 0
                total_cards = 0
                avg = 0
                for card_id in card_row['productId'] :
                        _products += str(card_id) + ','
                        total_cards += 1
                req_for_price = requests.get(url_for_price + _products, headers=header)
                print(url_for_price + _products)
                response_json_price = json.loads(req_for_price.text)

                for card_price in response_json_price['results'] :
                        if card_price['subTypeName'] == 'Normal' and card_price['marketPrice'] is not None :
                                total_price += card_price['marketPrice']

                avg = total_price / total_cards

                card_col.find_one_and_update(
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
db_functions.drop_table()
get_bearer_token()
db_functions.get_product()
db_functions.update_price()
'''
with open('card_col.csv', 'w') as csvfile :
        fw = csv.writer(csvfile, delimiter = ',',
                                quotechar = '|', quoting = csv.QUOTE_MINIMAL)
        fw.writerow(['_id', 'productId', 'name', 'price_list'])
        for x in card_col.find() :
                _products = ''
                _price = ''
                for y in x['productId'] :
                        _products += str(y) + ' '
                for z in x['price_list'] :
                        _price += str(z) + ' '
                fw.writerow([x['_id'], _products, x['name'], _price])
'''
