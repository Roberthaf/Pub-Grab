import requests
import json

# Set up which user to search for will be passed to an ARGV in the future
name_of_user="Jon+Olav+Vik"

#new api, search for the user and find personal id
url = "https://api.cristin.no/v1/persons?name=" + name_of_user + ""

#print out url to see if search option is ok.
print(url)

#Performs a get on the specified url.
response = requests.get(url, verify=True)

#Save the responce as a JSON dict
id_data=response.json()

#use the
user = str(id_data[0]['cristin_person_id'])

#print the json that is returned
print(user)

#Set up content type for headers
#header2 = {"content-type":"application/json"}

url2 = "http://www.cristin.no/ws/hentVarbeiderPerson?lopenr=" + user + "&fra=2016&til=2016&format=json"
print(url2)
response2 = requests.get(url2, verify=True)

data = response2.json()

#A list with all the names of aouthors in order
name_list = []

#start to itterate throguh all the "forskningsresultat" list
for i in data['forskningsresultat']:
     #print out title and year
     print(i['fellesdata']['tittel'], i['fellesdata']['ar'])

     #print out publication and issue nr.
     #ATH this is not working as intended
     print(i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['navn'], i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['issn'])
     #This need to be passed to IF statements and captured based on article types
     #print(i['kategoridata']['tidsskriftsartikkel']['publikasjonskanal']['serie']['navn'], i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['issn'])

     #itterate through all the personal associated with the publications
     for k in i['fellesdata']['person']:
          #Convert first names to uppercase letters only
          Short_firstname = k['fornavn']
          Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
          #Append all the list to the names
          #print((k['etternavn'] + ' '+ Uppercase_firstname))
          name_list.append( (k['etternavn'] + ' '+ Uppercase_firstname) )
print(name_list)

#next task test set up a good output.
#make sure it works for multiple entries
#put out as a HTML file.
