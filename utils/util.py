'''
general util functions that are used by the mtg-analytics application.

get_bearer_token()
is_time_greater(date)

'''
import datetime
import calendar
import requests
import json
import configparser
import util as util_functions

config = configparser.ConfigParser()
config.read('config.ini')

'''
get_bearer_token() :
checks to see if token is not outdated -
        if (true) :
                return current bearertoken in config filew
        else :
                get a new bearer token and update config file
                then return bearertoken
'''
def get_bearer_token() :
        if is_time_greater(config['tcgplayer-api-secret']['bearertoken_time']) :
                return config['tcgplayer-api-secret']['bearertoken']
        else :
                url = config['tcgplayer-api-secret']['tcgplayer-token-url']

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
is_time_greater(date) :
compares current date and passed in date and returns true if passed in date
is past the current date
'''
def is_time_greater(date):
    abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}
    temp_string = date[5:7] + str(abbr_to_num[date[8:11]]) + date[12:16]
    datetime_obj = datetime.datetime.strptime(temp_string, '%d%m%Y')
    datetime_now = datetime.datetime.now()

    return datetime_obj > datetime_now