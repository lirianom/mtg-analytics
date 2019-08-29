import sys
sys.path.insert(1, './utils/')

import db_functions
import util

db_functions.drop_table()
util.get_bearer_token()
db_functions.get_product()
db_functions.update_price()