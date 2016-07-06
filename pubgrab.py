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
import codecs
from urllib.parse import urlencode

# set up which user to search for will be passed to an ARGV in the future
# To be added later start year and end year
# start_year = 2015 end_year = 2015
#name_of_user = "Jon Olav Vik"
#name_of_user = "Dag Inge Våge"
#name_of_user = "Sigbjørn Lien"
name_of_user = "Arne Bjørke Gjuvsland"

def cristin_person_id(author):
    """
    Get CRISTIN person ID of author.
    > cristin_person_id("Jon Olav Vik")
    22311
    > cristin_person_id("22311")
    22311
    > cristin_person_id(22311)
    22311
    > cristin_person_id("Does not exist") is None
    True
    """
    try:
        return int(author)
    except ValueError:
        base = "https://api.cristin.no/v1/persons?"
        url = base + urlencode(dict(name=author))
        person = requests.get(url).json()
        if person:
            return person[0]["cristin_person_id"]
        else:
            return None
def pubs_by(author):
    """
    Get publications by author.

    For now we return the full record, whose complex structure is documented at
    http://www.cristin.no/techdoc/xsd/resultater/1.0/

    The order of dict items is nondeterministic, which makes it tricky to write doctests...
    The one below sometimes works, sometimes not.

    > pubs_by("Jon Olav Vik")  # doctest:+NORMALIZE_WHITESPACE,+ELLIPSIS
    {...'forskningsresultat': [{'fellesdata': {'registrert': {'dato': '2016-05-25...
    """
    cpid = cristin_person_id(author)
    base = "http://www.cristin.no/ws/hentVarbeiderPerson?"
    url = base + urlencode(dict(lopenr=cpid, fra=2002, til=2016, format="json"))
    print(url)
    pubs = requests.get(url).json()
    return pubs


# Start printing out to file
user = str(cristin_person_id(name_of_user))

# Create a textfile named after the user specific ID
text_file = user+".txt"
myfile = codecs.open(text_file, 'w+', encoding="UTF-8")

# Initiate the url using pubs_by
data = pubs_by(name_of_user)

# Sort data according to year of publication, newest first
data_sort = sorted((data['forskningsresultat']), key=lambda k: k['fellesdata']['ar'],reverse=True)
# Start to itterate throguh all the "forskningsresultat" list
for i in data_sort:
    # Create a string for name for each itteration
    name_list = ''
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

    # Some instances are dicts when it has a single auther
    elif (type(i['fellesdata']['person']) == dict ):
        Short_firstname = i['fellesdata']['person']['fornavn']
        Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
        # Append name to a string
        name_list = ((i['fellesdata']['person']['etternavn'] + ' ' + Uppercase_firstname))

    # Iterate through all keys in the katergories
    for key, value in (i['kategoridata']).items():

        # Start prasing data based on known keys. This will be expanded later
        if key == 'tidsskriftsartikkel':
            myfile.write(name_list+'\n')
            temp_tittle = i['fellesdata']['tittel']
            temp_year = i['fellesdata']['ar']
            temp_ty = temp_tittle + " " +'('+temp_year+') ';
            myfile.write(temp_ty)
            temp_article = i['kategoridata'][key]['tidsskrift']['navn']
            try:
               temp_issue = i['kategoridata'][key]['tidsskrift']['issn']
               break
            except KeyError:
                None

            temp_ai = temp_article + " " + temp_issue
            myfile.write(" "+ temp_ai +"\n")

        elif key == ( 'foredragPoster' ):
            myfile.write(name_list+'\n')
            temp_tittel = i['fellesdata']['tittel']
            temp_year = i['fellesdata']['ar']
            temp_ty = temp_tittle + " " + '(' + temp_year + ') ';
            myfile.write(temp_ty)
            #myfile.write('Poster or workshop\n')

        elif key == 'bokRapportDel':
            myfile.write(name_list+'\n')
            temp_tittel = i['fellesdata']['tittel']
            temp_year = i['fellesdata']['ar']
            temp_ty = temp_tittle + " " + '(' + temp_year + ') ';
            myfile.write(temp_ty)
          #  myfile.write('Book report\n')
        elif key == 'bokRapportDel':
            myfile.write(name_list+'\n')
            temp_tittel = i['fellesdata']['tittel']
            temp_year = i['fellesdata']['ar']
            temp_ty = temp_tittle + " " + '(' + temp_year + ') ';
            myfile.write(temp_ty)
            #myfile.write('Book\n ')
            # Next task test set up a good output.
            # Make sure it works for multiple entries
            # Put out as a HTML file.
