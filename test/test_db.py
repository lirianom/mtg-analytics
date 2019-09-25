import sys
sys.path.insert(1, './utils/')
import db_test_functions as db_test

db_test.init()
db_test.printCards()