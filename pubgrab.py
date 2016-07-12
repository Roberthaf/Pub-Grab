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
import logging
from urllib.parse import urlencode

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


def pubs_by(author, fra="", til="", hovedkategori="TIDSSKRIFTPUBL"):
    """
    Get publications by author.

    For now we return the full record, whose complex structure is documented at
    http://www.cristin.no/techdoc/xsd/resultater/1.0/

    To make doctests reproducible we use pprint, which recursively sorts dict items.

    >>> from pprint import pprint

    Arne Gjuvsland published two journal articles in 2010.

    >>> p = pubs_by("Arne Gjuvsland", 2010, 2010)
    >>> len(p)
    2

    Each item has "fellesdata" (shared among all publication types) and "kategoridata" (particular to journal articles).
    Both are of interest.

    >>> sorted(p[0].keys())
    ['fellesdata', 'kategoridata']
    >>> pprint(p)
    [{'fellesdata': {...
                     'ar': '2010',
                     ...
                     'id': '769189',
                     ...
                     'person': [{'etternavn': 'Gjuvsland',
                                 'fornavn': 'Arne Bjørke', ...},
                                {'etternavn': 'Plahte', ...},
                                {'etternavn': 'Ådnøy', ...},
                                {'etternavn': 'Omholt', ...}],
                     ...
                     'tittel': 'Allele Interaction - Single Locus Genetics Meets '
                               'Regulatory Biology'},
      'kategoridata': {'tidsskriftsartikkel': {'artikkelnr': 'e9379',
                                               'doi': '10.1371/journal.pone.0009379',
                                               'hefte': '2',
                                               'tidsskrift': {'@oaDoaj': 'true',
                                                              'id': '435449',
                                                              'issn': '1932-6203',
                                                              'kvalitetsniva': {'kode': '1', ...},
                                                              'navn': 'PLoS ONE',
                                                              ...},
                                               'volum': '5'}}},
     {'fellesdata': {...
                     'ar': '2010',
                     ...
                     'id': '771116',
                     ...
                     'person': [{'etternavn': 'Tøndel', ...},
                                {'etternavn': 'Gjuvsland', ...},
                                ...],
                     ...
                     'tittel': 'Screening design for computer experiments: '
                               'metamodelling of a deterministic mathematical '
                               'model of the mammalian circadian clock'},
      'kategoridata': {'tidsskriftsartikkel': {'doi': '10.1002/cem.1363',
                                               'hefte': '11-12',
                                               'sideangivelse': {'sideFra': '738',
                                                                 'sideTil': '747'},
                                               'tidsskrift': {...
                                                              'navn': 'Journal of '
                                                                      'Chemometrics',
                                                              ...},
                                               'volum': '24'}}}]

    Funding sources are in pubs[i]["fellesdata"]["eksternprosjekt"].

    >>> pprint(pubs_by("Jon Olav Vik", 2014, 2014))
    [{'fellesdata': {'ar': '2014',
                     ...
                     'eksternprosjekt': [{'finansieringskilde': {'kode': 'SKGJ', ...},
                                          'id': 'SKGJ-MED-005'},
                                         {'finansieringskilde': {'kode': 'NFR', ...},
                                          'id': '178901'},
                                         {'finansieringskilde': {'kode': 'NOTUR/NORSTORE', ...},
                                          'id': 'NN4653K'}],...
    """
    cpid = cristin_person_id(author)
    base = "http://www.cristin.no/ws/hentVarbeiderPerson?"
    url = base + urlencode(dict(lopenr=cpid, fra=fra, til=til, hovedkategori=hovedkategori, format="json"))
    logging.debug("Getting URL: " + url)
    pubs = requests.get(url).json()
    # This has dict_keys(['@xsi:noNamespaceSchemaLocation', 'generert', '@xmlns:xsi', 'forskningsresultat']),
    # but we only need this one.
    return pubs["forskningsresultat"]

def citation(pub):
    """
    Citation of a single publication.

    >>> pubs = pubs_by("Arne Gjuvsland", 2010, 2010)
    >>> pubs.keys()
    >>> for pub in pubs:
    ...     print(citation(pub))
    """

if __name__ == "__main__":
    # set up which user to search for will be passed to an ARGV in the future
    # To be added later start year and end year
    # start_year = 2015 end_year = 2015
    name_of_user = "Jon Olav Vik"
    # name_of_user = "Dag Inge Våge"
    # name_of_user = "Sigbjørn Lien"
    # name_of_user = "Arne Bjørke Gjuvsland"

    # Initiate the url using pubs_by
    data = pubs_by(name_of_user)

    # Create a list containing all information for printing html code
    html_codes_all = []

    # Sort data according to year of publication, newest first
    # noinspection PyShadowingNames
    data_sort = sorted((data['forskningsresultat']), key=lambda k: k['fellesdata']['ar'], reverse=True)
    # Start to iterate through all the "forskningsresultat" list
    for i in data_sort:
        # Create a string for name for each iteration
        authors = ''
        # Iterate through all persons in the project and create a name list
        # Some instances are lists when multiple authors
        if type(i['fellesdata']['person']) == list:
            for k in i['fellesdata']['person']:
                # Convert first names to uppercase letters only
                Short_firstname = k['fornavn']
                Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
                # Append all the names to a string
                authors += ((k['etternavn'] + ' ' + Uppercase_firstname) + ', ')
            # Remove a comma and a white space at the end of strings
            authors = authors[:-2]

        # For instances when there is a single author
        elif type(i['fellesdata']['person']) == dict:
            Short_firstname = i['fellesdata']['person']['fornavn']
            Uppercase_firstname = ''.join(c for c in Short_firstname if c.isupper())
            # Append name to a string
            authors = i['fellesdata']['person']['etternavn'] + ' ' + Uppercase_firstname

        # Iterate through all keys in the categories.
        for key, value in (i['kategoridata']).items():
            # Start processing data based on known keys. This will be expanded later
            if key == 'tidsskriftsartikkel':
                tittel = i['fellesdata']['tittel']
                year = i['fellesdata']['ar']
                journal = '<em>' + i['kategoridata']['tidsskriftsartikkel']['tidsskrift']['navn'] + '</em>'

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

                HTML_string = ('<p> ' + authors + ' (' + year + '). ' + tittel + ' ' + journal + ' ' + volum +
                               ' ' + articlenr + ' ' + DOI + '</p>')
                html_codes_all.append(HTML_string)

                # Currently only working for Articles, codes below can be used to add more items.
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

    filename = name_of_user + '.html'
    with open(filename, 'w+', encoding="utf-8") as myFile:
        myFile.write(html_str_start)
        for i in html_codes_all:
            myFile.write('\t\t' + i + '\n')
        myFile.write(html_str_end)
