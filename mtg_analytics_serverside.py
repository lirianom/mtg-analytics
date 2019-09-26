import sys
sys.path.insert(1, './utils/')
sys.path.insert(2, './utils/init')
import db_init
import db_functions
import util

#db_functions.drop_tables()
#db_init.init()
db_functions.update_price()
db_functions.print_cards()