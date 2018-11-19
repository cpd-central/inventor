#script to pull data from an api (inventor in this case) and send to mongodb
#will be able to write changes from the db to inventor, but that is not implemented at the moment

#win32com is a library used to talk to the inventor application
import win32com.client
from win32com.client import gencache
import os
#these are not extracted from the api
NOT_IN_API = ['Filename w/o Extension', 'Found Location']


def open_inventor():
	#opens inventor
	inventor = win32com.client.Dispatch('Inventor.Application')
	#decide if you want the app to be visible or not - NOTE uncomment to set visible
	#inventor.Visible = True

	#NOTE I don't know what this line actually does.
	#Here's a link to a potentially helpful article I haven't read yet
	#http://www.icodeguru.com/WebServer/Python-Programming-on-Win32/ch12.htm
	mod = gencache.EnsureModule('{D98A091D-3A0F-4C3E-B36E-61F62068D488}', 0, 1, 0)
	return inventor, mod

def extract(prop, prop_set, part):
	#get the value of the iproperty
	iprop = prop_set(prop).Value
	#append the appropriate list within the dictionary
	return iprop

def get_data(requested_props, parts):
	#now we get the properties we want
	app, mod = open_inventor()

	inv_properties = [p for p in requested_props if p not in NOT_IN_API]
	print(inv_properties)

	parts_props_list = []

	for part in parts:
		#loop through the parts and extract the iproperties for each
		#open the part in inventor
		app.Documents.Open(part)
		#gets the document as whatever the open document in inventor is (now the part we just opened)
		doc = app.ActiveDocument	
		#NOTE, we may have to dive into other property sets, but for now we will just use Design Tracking Properties
		#a list of all of the sets and what properties can be extracted from them is here:
		#https://forums.autodesk.com/t5/inventor-customization/get-set-iproperty-directly-with-id-enum/td-p/5124654
		design_props = doc.PropertySets.Item('Design Tracking Properties')

		#update our dictionary with all of the lists with the key as the property we are looking at
		part_prop_dict = {}
		for prop in inv_properties:
			part_prop_dict[prop] = extract(prop, design_props, part)	
		#split the part filepath on the backslashes (directory changes).  The last value of this list is the filepath	
		#then, we split on the period, which indicates the file extension, and get the 0th value in this list	
		filename_wo_extension = part.split('\\')[-1].split('.')[0]
		#get the found location and the filename and add them to their locations in the dictionary
		#os.path.dirname() converts the string to the directory path - does not include the filename
		found_location = os.path.dirname(part)
		part_prop_dict['Filename w/o Extension'] = filename_wo_extension
		part_prop_dict['Found Location'] = found_location
		print(part_prop_dict)
		parts_props_list.append(part_prop_dict)	

		app.Documents.CloseAll()
	print(parts_props_list)	
	#close inventor after we have extracted the data we are interested in
	app.Quit()
	return parts_props_list

#requested = ['Vendor', 'Part Number', 'Description', 'Catalog Web Link', 'Engr Approved By']
#get_data(requested, parts_list, inventor, mod)

def change_props(props_to_change, parts):
	app, mod = open_inventor()
	doc = app.ActiveDocument
	design_props = doc.PropertySets.Item('Design Tracking Properties')

	#now, we just change the corresponding parts

	
	










