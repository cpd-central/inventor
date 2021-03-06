#script to pull data from an api (inventor in this case) and send to mongodb
#will be able to write changes from the db to inventor, but that is not implemented at the moment

#used for importing the .tlb file for the inventor object library
import pythoncom
#win32com is a library used to talk to the inventor application
import win32com.client
from win32com.client import gencache
import os


#NOTE, we are now reading/writing iProperties via the apprentice server since it should be way faster.
#the old code for opening inventor is left here for future reference.
"""
def open_inventor():
	#opens inventor
	inventor = win32com.client.Dispatch('Inventor.Application')
	#NOTE, this is the call (I think) for using Apprentice:
	#inventor = win32com.client.Dispatch('Inventor.ApprenticeServerComponent')
	#exit()
	#del inventor	
	#decide if you want the app to be visible or not - NOTE uncomment to set visible
	#inventor.Visible = True

	#NOTE I don't know what this line actually does.
	#Here's a link to a potentially helpful article I haven't read yet
	#http://www.icodeguru.com/WebServer/Python-Programming-on-Win32/ch12.htm
	#mod = gencache.EnsureModule('{D98A091D-3A0F-4C3E-B36E-61F62068D488}', 0, 1, 0)
	return inventor#, mod

def close_inventor(inv):
	inv.Quit()
	del inv
	return None
"""


#connect/disconnect to/from apprentice server
def open_apprentice(tlb_path):
	#this file contains the inventor object library, which we need in order to create an ApprenticeServerComponent object
	inv_obj_lib = pythoncom.LoadTypeLib(tlb_path)
	
	for index in range(0, inv_obj_lib.GetTypeInfoCount()):
		#name of the component we're looking at for this iteration
		#gets the name of the component which is the first index for GetDocumentation	
		type_name = inv_obj_lib.GetDocumentation(index)[0]
		#check if it's the ApprenticeServerComponent
		if type_name == 'ApprenticeServerComponent':
			#get the id, which we use for our win32com dispatch	
			type_iid = inv_obj_lib.GetTypeInfo(index).GetTypeAttr().iid
			#leave the loop	
			break
	
	apprentice = win32com.client.Dispatch(type_iid)
	return apprentice


def close_apprentice(app):
	app.Close()
	return None



def extract(prop, prop_set):
	#get the value of the iproperty
	iprop = prop_set(prop).Value
	#append the appropriate list within the dictionary
	return iprop

def get_inv_properties(requested_props, not_in_api):
	props = [p for p in requested_props if p not in not_in_api]	
	return props


def get_data(tlb_path, requested_props, parts, not_in_api):
	#now we get the properties we want
	#app, mod = open_inventor()
	app = open_apprentice(tlb_path)
	print(app)
	#get the props that we wish to pull from iproperties, not the filepath/filename	
	inv_properties = get_inv_properties(requested_props, not_in_api)

	parts_props_list = []

	for part in parts:
		print(part)
		#loop through the parts and extract the iproperties for each
		#open the part in apprentice 
		doc = app.Open(part)		
		#NOTE, we may have to dive into other property sets, but for now we will just use Design Tracking Properties
		#a list of all of the sets and what properties can be extracted from them is here:
		#https://forums.autodesk.com/t5/inventor-customization/get-set-iproperty-directly-with-id-enum/td-p/5124654
		design_props = doc.PropertySets.Item('Design Tracking Properties')

		#update our dictionary with all of the lists with the key as the property we are looking at
		part_prop_dict = {}
		for prop in inv_properties:
			part_prop_dict[prop] = extract(prop, design_props)	
		
		#split the part filepath on the backslashes (directory changes).  The last value of this list is the filepath	
		#then, we split on the period, which indicates the file extension, and get the 0th value in this list	
		filename_wo_extension = part.split('\\')[-1].split('.')[0]
		#get the found location and the filename and add them to their locations in the dictionary
		#os.path.dirname() converts the string to the directory path - does not include the filename
		found_location = os.path.dirname(part)
		part_prop_dict['Filename w/o Extension'] = filename_wo_extension
		part_prop_dict['Found Location'] = found_location
		#print(part_prop_dict)
		parts_props_list.append(part_prop_dict)	
		doc.Close()
	
	#close inventor after we have extracted the data we are interested in
	close_apprentice(app)
		
	return parts_props_list


def write_props(new_prop, prop, prop_set):
	prop_set.Item(prop).Value = new_prop
		
	return None

def change_props(tlb_path, df=None, not_in_api=None, parts=None, props_to_change=None, path_id_dict=None, is_first=False):
	#edge case for when this is being called from populate_db as opposed to updating
	#used for writing the object_id from mongo
	app = open_apprentice(tlb_path)	
	#if it's the first insert, we're just writing the object id as a new property	
	if is_first:
		#path id dict keys are the paths to the different parts.  The values are the object ids from mongo
		for path in path_id_dict.keys():	
			print(path)
			#open the document in apprentice	
			doc = app.Open(path)
			#get the property set for custom properties
			user_def_props = doc.PropertySets.Item('Inventor User Defined Properties')
			#add the object id as a custom property
			#NOTE inventor doesn't like the ObjectId object type so we cast it as a string in python	
			object_id = str(path_id_dict[path])	
			#NOTE, if the inventor file already has this as a parameters, win32api will throw error -2147024809: 'The Parameter is Incorrect'.
			#If this error gets thrown, nothing should be changed, the object id we're attempting to write should be logged as well as the error so we can
			#investigate.	

			#check if the mongo id exists as a custom property already.  if it does, update with the new one, if it doesn't, create it	
			try:
				existing = user_def_props.Item('Mongo ObjectId')	
				existing.Value = object_id
			except Exception as exc:	
				print('Mongo ID likely does not exist as an iProperty.  Adding...')
				print(exc)
				user_def_props.Add(object_id, 'Mongo ObjectId')
			#need to save the document after we write to it	
			doc.PropertySets.FlushToFile()
			doc.Close()
		close_apprentice(app)	
	else:	
		#convert the _id column in the dataframe to strings
		for path in path_id_dict.keys():
			#new_object_id is of type bson.objectid.ObjectId, which is what mongo needs to use it.  We cast it as a string here for the equivalency check
			#later on.
			new_object_id = str(path_id_dict[path])	
			#now, we need to open each .ipt in this directory and find the one that has the same object_id
			for filename in os.listdir(path):
				if filename.endswith('.ipt'):
					#add the filename to the path
					#NOTE the filename in the dataframe may be different than what exists, which is why we do it this way
					full_path = os.path.join(path, filename)
					print(full_path)
					doc = app.Open(full_path)
					user_def_props = doc.PropertySets.Item('Inventor User Defined Properties')
					#see if the object_id exits as a property for this file.
					#if it does, see if it matches the one in the dictionary
					try:	
						object_id = extract('Mongo ObjectId', user_def_props)
						if object_id == new_object_id:
							print('equal!')
							#if the object id is the same as the one in the dictionary we pass in, change the properties from the dataframe
							design_props = doc.PropertySets.Item('Design Tracking Properties')
							inv_properties = get_inv_properties(df.columns, not_in_api)				
							#loop through inv_properties and write each one
							for prop in inv_properties:
								#get the property we want to write.  It is the property located in the 'prop' column where the value in the '_id' column equals 
								#the object_id
								print(f'property is: {prop}')
								#exit loop and go to next part if we reach '_id', since we don't want to change that one, even if it was mistakenly changed in the 
								#spreadsheet
								if prop == '_id':
									break
								#new_prop = df[prop]['_id' == object_id]	
								#NOTE, same thing here with type differences, we need to cast the df['_id'] values as strings so the comparison works	
								#iloc[0] call at the end gives us the value without the index
								new_prop = df.loc[df['_id'].astype(str) == object_id, prop].iloc[0]
								print(f'new property is: {new_prop}')	
								#NOTE, new_prop is the value of the property, prop is the name of the property and design_props is the property set
								write_props(new_prop, prop, design_props)
								#NOTE, we might want to put this in the write_props function at some point, but this is fine for now	
								doc.PropertySets.FlushToFile()
								#NOW, if the filename is different than the value of 'Filename w/o Extension' for this object_id, we change the actual filename	
								new_filename = df.loc[df['_id'].astype(str) == object_id, 'Filename w/o Extension'].iloc[0] + '.ipt'
								new_full_path = os.path.join(path, new_filename)
								print(new_filename)
								if filename != new_filename:
									os.rename(full_path, new_full_path)
								elif filename == new_filename:
									print('same')
					except Exception as exc:
						print(f'error reading Mongo object_id for {filename}')
						print(exc)
						continue
					doc.Close()
		close_apprentice(app)
		return None

"""
def check_objectid(parts):
	app = open_inventor()
	for part in parts:
		print(part)
		app.Documents.Open(part)
		doc = app.ActiveDocument
		user_def_props = doc.PropertySets.Item('Inventor User Defined Properties')
		print(user_def_props('Mongo ObjectId').Value)
		app.Documents.CloseAll()
	close_inventor(app)
	return None
"""







