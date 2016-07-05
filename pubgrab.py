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

from urllib.parse import urlencode

import requests


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
    url = base + urlencode(dict(lopenr=cpid, fra=2015, til=2015, format="json"))
    pubs = requests.get(url).json()
    return pubs

if __name__ == "__main__":
    # import json

    # Set up which user to search for will be passed to an ARGV in the future.
    name_of_user = "Jon+Olav+Vik"

    # New api, search for the user and find personal id.
    url = "https://api.cristin.no/v1/persons?name=" + name_of_user + ""

    # Print out url to see if search option is ok.
    print(url)

    # Performs a get on the specified url.
    response = requests.get(url, verify=True)

    # Save the response as a JSON dict
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
