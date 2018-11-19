import sys
sys.path.insert(0, r"C:\Users\jmarsnik\Desktop\data_work\inventor_scripts\best_version\mongo_scripts")
sys.path.insert(0, r"C:\Users\jmarsnik\Desktop\data_work\inventor_scripts\best_version\mongo_scripts\excel")
sys.path.insert(0, r"C:\Users\jmarsnik\Desktop\data_work\inventor_scripts\best_version\mongo_scripts\inventor") 

import mongo_manager as mm
import read_write_excel as ex
import inventor_api as inv
import get_filenames as f

from pprint import pprint


REQUESTED = ['Vendor', 'Part Number', 'Description', 'Catalog Web Link', 'Engr Approved By']
CHANGING = ['Vendor', 'Part Number', 'Description', 'Catalog Web Link', 'Engr Approved By']
DB_NAME = 'Inventor_DB_TESTING'
COLL_NAME = 'iProperties_Collection_TESTING'


def populate_db():
	return None


def update_system():
	return None



"""
parts = f.get_ipts()
parts_props_list = inv.get_data(REQUESTED, parts)
#get the list of part properties
#send this list to mongo
mm.first_to_mongo(parts_props_list, DB_NAME, COLL_NAME) 
"""




#NOTE, there is also a query argument which defaults to {} to get everything.  This could be inputted by the user
""" documents = mm.from_mongo(DB_NAME, COLL_NAME) 
doc_df = ex.mongo_to_dataframe(documents)
ex.send_to_excel(doc_df)
"""

#send excel data to mongo


input_df = ex.get_from_excel()
mm.update_mongo(DB_NAME, COLL_NAME, input_df)



#change iProperties according to the data in the database
"""
parts = f.get_ipts()
documents = mm.from_mongo(DB_NAME, COLL_NAME)
doc_df = ex.mongo_to_dataframe(documents)
inv.change_props(doc_df, parts)
"""



