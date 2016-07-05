"""
Build publication list for a list of authors.

Retrieve records from the CRISTIN database of Norwegian scientific publications,
using a mix of the old and new REST APIs.
Present results as HTML.
"""

import requests
# import json

# Set up which user to search for will be passed to an ARGV in the future.
name_of_user = "Jon+Olav+Vik"

# New api, search for the user and find personal id.
url = "https://api.cristin.no/v1/persons?name=" + name_of_user + ""

# Print out url to see if search option is ok.
print(url)

# Performs a get on the specified url.
response = requests.get(url, verify=True)

# Save the responce as a JSON dict
id_data = response.json()

# Use the
user = str(id_data[0]['cristin_person_id'])

# Print the json that is returned
print(user)

# Set up content type for headers
# header2 = {"content-type":"application/json"}

url2 = "http://www.cristin.no/ws/hentVarbeiderPerson?lopenr=" + user + "&fra=2016&til=2016&format=json"
print(url2)
response2 = requests.get(url2, verify=True)

data = response2.json()

# A list with all the names of authors in order.
name_list = []

# Start to iterate through all the "forskningsresultat" list
for i in data['forskningsresultat']:
    # Print out title and year
    print(i['fellesdata']['tittel'], i['fellesdata']['ar'])

    # Print out publication and issue nr
    # ATH this is not working as intended
    print(i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['navn'],
          i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['issn'])
    # This need to be passed to IF statements and captured based on article types.
    # print(i['kategoridata']['tidsskriftsartikkel']['publikasjonskanal']['serie']['navn'],
    #       i['fellesdata']['rapportdata']['publikasjonskanal']['serie']['issn'])

    # Iterate through all the personnel associated with the publications.
    for k in i['fellesdata']['person']:
        # Convert first names to uppercase letters only
        Short_firstname = k['fornavn']
        Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
        # Append all the list to the names
        # print((k['etternavn'] + ' '+ Uppercase_firstname))
        name_list.append((k['etternavn'] + ' ' + Uppercase_firstname))
print(name_list)

# Next task test set up a good output.
# Make sure it works for multiple entries.
# Output as a HTML file.
