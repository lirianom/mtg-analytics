import requests
import json
import configparser
import pymongo as mongo
import datetime
import util as util_functions

config = configparser.ConfigParser()
config.read('config.ini')
dbclient = mongo.MongoClient('mongodb://localhost:27017/')
card_db = dbclient['card_db']
card_col = card_db['cards']
now = datetime.date.today()

def get_bearer_token() :
        if (util_functions.is_time_greater(config['SECRET']['BEARERTOKEN_TIME'])) :
                return config['SECRET']['BEARERTOKEN']
        else :
                url = 'https://api.tcgplayer.com/token'

                header = {
                        'grant_type': 'client_credentials',
                        'client_id': config['SECRET']['PUBLICKEY'],
                        'client_secret': config['SECRET']['PRIVATEKEY'],
                }
                req = requests.post(url, data=header)
                response_json = json.loads(req.text)
                config['SECRET']['BEARERTOKEN'] = response_json['access_token']
                config['SECRET']['BEARERTOKEN_TIME'] = response_json['.expires']
                with open('config.ini', 'w') as config_file:
                        config.write(config_file)
                return config['SECRET']['BEARERTOKEN']

def drop_table() :
        card_col.drop()

def get_product() :
        url_for_mtg_cards = 'http://api.tcgplayer.com/v1.27.0/catalog/products'
        url_for_price = 'http://api.tcgplayer.com/v1.27.0/pricing/product/'
        #url_for_categories = 'http://api.tcgplayer.com/v1.27.0/catalog/categories'

        url_append_for_cards = '?categoryId=1&limit=100'
        header = {
                'Accept': 'application/json',
                'Authorization': 'bearer ' + str(config['SECRET']['BEARERTOKEN']),
        }

        #print(header)

        req_for_cards = requests.get(url_for_mtg_cards + url_append_for_cards, headers=header)

        response_json_cards = json.loads(req_for_cards.text)

        products = []

        for value in response_json_cards['results']:
                products.append(str(value['productId']))

        url_append_for_price = ','.join(products)

        req_for_price = requests.get(url_for_price + url_append_for_price, headers=header)

        response_json_price = json.loads(req_for_price.text)

        price_list = []


        for value in response_json_price['results']:
                if value['subTypeName'] == 'Normal':
                        temp_list = {
                                'productId' : value['productId'],
                                'price' : value['midPrice'],
                        }
                        price_list.append(temp_list)

        '''
        card_col.find_one_and_update({'productId': 193}, {
                '$push' : {
                        'price_list' : {'date' : 'blah', 'price' : 99999}
                }
        })
        '''
        for value_cards, value_price in zip(response_json_cards['results'], price_list):
                now = datetime.date.today()
                temp_list = {
                        'productId' : value_cards['productId'],
                        'name' : value_cards['name'],
                        'imageUrl' : value_cards['imageUrl'],
                        'price_list' : [{
                                'date' : str(now),
                                'price' : value_price['price'],
                        }]
                }
                card_col.insert_one(temp_list)
        '''
        for x in card_col.find():
                print(x)

        for value_cards, value_price in zip(response_json_cards['results'], price_list):
                now = datetime.date.today()
                temp_list = {
                        'productId' : value_cards['productId'],
                        'name' : value_cards['name'],
                        'imageUrl' : value_cards['imageUrl'],
                        'price_list' : [{
                                'date' : str(now),
                                'price' : value_price['price'],
                        }]
                }
                card_col.insert_one(temp_list)
        for x in card_col.find():
                        print(x)
        card_list = []
        for value_cards, value_price in zip(response_json_cards['results'], price_list):
                now = datetime.date.today()
                product_id = value_cards['productId']
                if product_id == value_price['productId']:
                        image_url = value_cards['imageUrl']
                        name = value_cards['name']
                        temp_price = {
                                'date' : str(now),
                                'price' : value_price['price'],
                        }
                        for x in card_col.find({'productId' : product_id}):
                                temp_price_list = x.get('price_list').update(temp_price)
                        #print(x.get('price_list'))
                        temp_list = {
                                'productId' : product_id,
                                'name' : name,
                                'imageUrl' : image_url,
                                'price_list' : temp_price_list,
                        }
                        card_list.append(temp_list)

        card_col.insert_many(card_list)

        for x in card_col.find():
                print(x)

        with open('m_price.ini', 'w') as c:
               c.write(str(card_list))
        '''

def update_price() :
        header = {
                'Accept': 'application/json',
                'Authorization': 'bearer ' + str(config['SECRET']['BEARERTOKEN']),
        }
        url_for_price = 'http://api.tcgplayer.com/v1.27.0/pricing/product/'
        now = datetime.date.today()
        for x in card_col.find() :
                url_append_for_price = str(x['productId'])
                req_for_price = requests.get(url_for_price + url_append_for_price, headers=header)
                response_json_price = json.loads(req_for_price.text)
                card_col.find_one_and_update({'productId': x['productId']}, {
                        '$push' : {
                                'price_list' : {'date' : str(now), 'price' : response_json_price['results']['midPrice']}
                        }
                })

        for x in card_col.find() :
                print(x)
#drop_table()
get_bearer_token()
get_product()
update_price()