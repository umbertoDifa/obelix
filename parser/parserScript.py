from pykml import parser
import json
import urllib2
from dotenv import load_dotenv
import os
#LOAD ENV

dotenv_path = './../merda.env'
load_dotenv(dotenv_path)

MONGODB_URI=os.environ.get("MONGODB_URI")
####DOWNLOAD AND PARSE KML INTO JSON

url = os.environ.get("KML_URL")
fileobject = urllib2.urlopen(url)
root = parser.parse(fileobject).getroot()

##local test
# kml_file = 'tpi.kml'
# with open(kml_file) as f:
#     doc = parser.parse(f)
# root = doc.getroot()

jsonDoc = []
for folder in root.Document.iterchildren():
    if hasattr(folder, 'name'): #HACK:this is the way to check that the element is a folder
        newCategory = folder.name.text
        try:
            placemark = folder.Placemark
        except AttributeError:
            placemark = None

        while(placemark is not None):
            placeName = placemark.name
            coordinates=placemark.Point.coordinates.text.strip().split(',')
            lon = coordinates[0]
            lat = coordinates[1]
            newPlace={"Name":placeName.text,"Category":newCategory,"geometry":{"type":"Point","coordinates":[float(lon),float(lat)]}}
            jsonDoc.append(newPlace)
            placemark = placemark.getnext()


with open('tpi.json', 'w') as outfile:
    json.dump(jsonDoc,outfile,indent=3)


##CONNETECT TO DB AND UPDATE
from pymongo import MongoClient

collectionName = 'posti'
client = MongoClient(MONGODB_URI)
db = client['heroku_2lvqz56l']

db.drop_collection(collectionName)
collection = db.get_collection(collectionName)
collection.insert_many(jsonDoc)

#create index
collection.create_index([("geometry", "2dsphere")])
