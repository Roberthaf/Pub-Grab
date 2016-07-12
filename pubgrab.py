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
from urllib.parse import urlencode

# set up which user to search for will be passed to an ARGV in the future
# To be added later start year and end year
# start_year = 2015 end_year = 2015
name_of_user = "Jon Olav Vik"
#name_of_user = "Dag Inge Våge"
#name_of_user = "Sigbjørn Lien"
#name_of_user = "Arne Bjørke Gjuvsland"

def cristin_person_id(author):
    """
    Get CRISTIN person ID of author.
    >>> cristin_person_id("Jon Olav Vik")
    22311
    >>> cristin_person_id("22311")
    22311
    >>> cristin_person_id(22311)
    22311
    >>> cristin_person_id("Does not exist") is None
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

    >>> pubs_by("Jon Olav Vik")  # doctest:+NORMALIZE_WHITESPACE,+ELLIPSIS
    {...'forskningsresultat': [{'fellesdata': {'registrert': {'dato': '2016-05-25...
    """
    cpid = cristin_person_id(author)
    base = "http://www.cristin.no/ws/hentVarbeiderPerson?"
    url = base + urlencode(dict(lopenr=cpid, fra=2002, til=2016, format="json"))
    print(url)
    pubs = requests.get(url).json()
    return pubs

# Initiate the url using pubs_by
data = pubs_by(name_of_user)

# Create a list containing all information for printing html code
html_codes_all = []

# Sort data according to year of publication, newest first
data_sort = sorted((data['forskningsresultat']), key=lambda k: k['fellesdata']['ar'],reverse=True)
# Start to itterate throguh all the "forskningsresultat" list
for i in data_sort:
    # Create a string for name for each itteration
    authers = ''
    # Iterate through all persons in the project and create a name list
    # Some instances are lists when multiple authers
    if (type(i['fellesdata']['person']) == list ):
        for k in i['fellesdata']['person']:
            # Convert first names to uppercase letters only
            Short_firstname = k['fornavn']
            Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
            # Append all the names to a string
            authers += ((k['etternavn'] + ' ' + Uppercase_firstname) + ', ')
        # Remove a comma and a white space at the end of strings
        authers = authers[:-2]

    # For instances when its a single auther
    elif (type(i['fellesdata']['person']) == dict ):
        Short_firstname = i['fellesdata']['person']['fornavn']
        Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
        # Append name to a string
        authers = ((i['fellesdata']['person']['etternavn'] + ' ' + Uppercase_firstname))
        
    # Iterate through all keys in the katergories.
    for key, value in (i['kategoridata']).items():
        # Start prasing data based on known keys. This will be expanded later
        if key == 'tidsskriftsartikkel':
            tittel = i['fellesdata']['tittel']
            year = i['fellesdata']['ar']
            journal = '<em>'+i['kategoridata']['tidsskriftsartikkel']['tidsskrift']['navn']+'</em>'

            try:
                articlenr = i['kategoridata']['tidsskriftsartikkel']['artikkelnr']
            except KeyError:
                articlenr = ''

            try:
                volum = '<strong>(' + i['kategoridata']['tidsskriftsartikkel']['volum'] + ')</strong>'
            except KeyError:
                volum = ''

            try:
                 DOI = 'http://dx.doi.org/' + i['kategoridata']['tidsskriftsartikkel']['doi']
            except KeyError:
                 DOI = ''

            HTML_string = ('<p> ' + authers + ' (' + year + '). ' + tittel + ' ' + journal + ' ' + volum + ' ' + articlenr + ' ' + DOI + '</p>')
            html_codes_all.append(HTML_string)

        # Corrently only working for Articles, codes below can be used to add more items.
        # elif key == ( 'foredragPoster' ):
        #     tittel = i['fellesdata']['tittel']
        #     year = i['fellesdata']['ar']
        #     #journal = '<em>'+i['kategoridata'][key]['navn']+'</em>' Wrokshop
        # elif key == 'bokRapport':
        #     tittel = '<em>'+i['fellesdata']['tittel']+'</em>'
        #     year = '<strong>'+i['fellesdata']['ar']+'</strong>'
        #
        # elif key == 'bokRapportDel':
        #     tittel = '<em>'+i['fellesdata']['tittel']+'</em>'
        #     year = '<strong>'+i['fellesdata']['ar']+'</strong>'

html_str_start = """
<!DOCTYPE html>
<HTML>
    <head>
        <meta charset="utf-8">
    </head>

    <body>
        <h1>References</h1>
"""

html_str_end = """
    </body>
</HTML>
"""

filename = name_of_user+'.html'
with open(filename, 'w+',encoding="utf-8") as myFile:
    myFile.write(html_str_start)
    for i in html_codes_all:
        myFile.write('\t\t'+i+'\n')
    myFile.write(html_str_end)
