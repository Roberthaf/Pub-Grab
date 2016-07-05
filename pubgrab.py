# Purpouse of this script is to access cristin.no API and fetch publication
# related to the cigene proje
import requests

# set up which user to search for will be passed to an ARGV in the future
# To be added later start year and end year
# start_year = 2015 end_year = 2015
name_of_user = "Jon+Olav+Vik"

# new api, search for the user and find personal id
url = "https://api.cristin.no/v1/persons?name=" + name_of_user + ""

# print out url to see if search option is ok.
print(url)

# Perform a get on the specified url.
response = requests.get(url, verify=True)

# Save the responce as a JSON dict
id_data = response.json()

# Save the person_id as a string
user = str(id_data[0]['cristin_person_id'])

# Insert saved person_id in the
url2 = "http://www.cristin.no/ws/hentVarbeiderPerson?lopenr=" + user + "&fra=2004&til=2016&format=json"
print(url2)
response2 = requests.get(url2, verify=True)

data = response2.json()

# start to itterate throguh all the "forskningsresultat" list
for i in data['forskningsresultat']:
    # Create a string for name for each itteration
    name_list = ''
    # for debugin porpuse nly
    # print((i['kategoridata']).items())
    # itterate through all persons in the project and create a name list
    #some instances are lists when multiple authers
    if (type(i['fellesdata']['person']) == list ):
        for k in i['fellesdata']['person']:
            # Convert first names to uppercase letters only
            #print(k['fornavn'])
            Short_firstname = k['fornavn']
            Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
            # Append all the names to a string
            name_list += ((k['etternavn'] + ' ' + Uppercase_firstname) + ', ')
        # remove a comma and a white space at the end of strings
        name_list = name_list[:-2]
    #some instances are dicts when single auther
    elif (type(i['fellesdata']['person']) == dict ):

        Short_firstname = i['fellesdata']['person']['fornavn']
        Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
        # Append name to a string
        name_list = ((i['fellesdata']['person']['etternavn'] + ' ' + Uppercase_firstname))
    # iterate through all keys in the katergories
    for key, value in (i['kategoridata']).items():
        # Start prasing data based on known keys. This will be expanded later
        if key == 'tidsskriftsartikkel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print(i['kategoridata'][key]['tidsskrift']['navn'], i['kategoridata'][key]['tidsskrift']['issn'])
            print('article journal\n')
        elif key == 'foredragPoster':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            # print(i['kategoridata'][key]['arrangement']['navn'], i['kategoridata'][key]['tidsskrift']['issn'])
            print('Poster or workshop\n')
        elif key == 'bokRapportDel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print('Book report\n')
        elif key == 'bokRapportDel':
            print(name_list)
            print(i['fellesdata']['tittel'], i['fellesdata']['ar'])
            print('Book\n ')
            # next task test set up a good output.
            # make sure it works for multiple entries
            # put out as a HTML file.
