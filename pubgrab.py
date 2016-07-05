"""
Build publication list for a list of authors.

Retrieve records from the CRISTIN database of Norwegian scientific publications,
using a mix of the old and new REST APIs.
Present results as HTML.

New API docs: https://api.cristin.no/index.html
New JSON schema: https://api.cristin.no/v1/doc/json-schemas/
Old API docs: http://www.cristin.no/cristin/superbrukeropplaering/ws-dokumentasjon.html#toc5
Old XML schema: http://www.cristin.no/techdoc/xsd/resultater/1.0/
Info on transition from old to new API: http://www.cristin.no/om/aktuelt/aktuelle-saker/2016/api-lansering.html
"""
import requests

# Set up which user to search for will be passed to an ARGV in the future
# To be added later start year and end year
# Start_year = 2015 end_year = 2015
name_of_user = "Jon+Olav+Vik"

# New api, search for the user and find personal id
url = "https://api.cristin.no/v1/persons?name=" + name_of_user + ""

# Print out url to see if search option is ok
print(url)

# Perform a get on the specified url
response = requests.get(url, verify = True)

# Save the responce as a JSON dict
id_data = response.json()

# Save the person_id as a string
user = str(id_data[0]['cristin_person_id'])

# Insert saved person_id in the
url2 = "http://www.cristin.no/ws/hentVarbeiderPerson?lopenr=" + user + "&fra=2004&til=2016&format=json"
print(url2)
response2 = requests.get(url2, verify=True)
# Save response as a json object 
data = response2.json()

# Start to itterate throguh all the "forskningsresultat" list
for i in data['forskningsresultat']:
    # Create a string for name for each itteration
    name_list = ''
    # For debugin porpuse nly
    # Print((i['kategoridata']).items())
    # Iterate through all persons in the project and create a name list
    # Some instances are lists when multiple authers
    if (type(i['fellesdata']['person']) == list ):
        for k in i['fellesdata']['person']:
            # Convert first names to uppercase letters only
            Short_firstname = k['fornavn']
            Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
            # Append all the names to a string
            name_list += ((k['etternavn'] + ' ' + Uppercase_firstname) + ', ')
        # Remove a comma and a white space at the end of strings
        name_list = name_list[:-2]
    # Fix authers list when it has only a single auther
    elif (type(i['fellesdata']['person']) == dict ):
        Short_firstname = i['fellesdata']['person']['fornavn']
        Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
        # Append name to a string
        name_list = ((i['fellesdata']['person']['etternavn'] + ' ' + Uppercase_firstname))
    # iterate through all keys in the 'katergories'
    for key, value in (i['kategoridata']).items():
        # Start printing data based on known keys. ATH this will be expanded later
        if key == 'tidsskriftsartikkel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print(i['kategoridata'][key]['tidsskrift']['navn'], i['kategoridata'][key]['tidsskrift']['issn'])
            print('article journal\n')
        elif key == 'foredragPoster':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print('Poster or workshop\n')
        elif key == 'bokRapportDel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print('Book report\n')
        elif key == 'bokRapportDel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print('Book\n ')
        
            # Save output as a HTML file
