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

import argparse
import operator
import itertools
import os
import tempfile
import requests
import logging
from urllib.parse import urlencode
from collections import defaultdict

from joblib import Memory


cachedir = os.path.join(tempfile.gettempdir(), "pubgrab_cache")
mem = Memory(cachedir, verbose=0)


@mem.cache
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


@mem.cache
def pubs_by(author, fra=1900, til=9999, hovedkategori="TIDSSKRIFTPUBL"):
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
    >>> pprint(p)
    [{...
      'ar': '2010',
      'arRapportert': '2010',
      'artikkelnr': 'e9379',
      'doi': '10.1371/journal.pone.0009379',
      ...
      'hefte': '2',
      'id': '769189',
      ...
      'kategori': {'hovedkategori': {'kode': 'TIDSSKRIFTPUBL',
                                     'navn': 'Tidsskriftspublikasjon',
                                     'navnEngelsk': 'Journal publication'},
                   'underkategori': {'kode': 'ARTIKKEL',
                                     'navn': 'Vitenskapelig artikkel',
                                     'navnEngelsk': 'Academic article'}},
      ...
      'person': [{'etternavn': 'Gjuvsland',
                  'fornavn': 'Arne Bjørke',
                  'harFodselsnummer': 'true',
                  'id': '7059',
                  'rekkefolgenr': '1',
                  'tilhorighet': {'sted': {'avdnr': '1', ...}}},
                 {'etternavn': 'Plahte', ...},
                 {'etternavn': 'Ådnøy', ...},
                 {'etternavn': 'Omholt', ...}],
      ...
      'sammendrag': [{'sprak': {'kode': 'EN',
                                'navn': 'Engelsk',
                                'navnEngelsk': 'English'},
                      'tekst': 'Conclusion/Significance: The concept of allele '
                               'interaction refines single locus genetics ' ...},
                     {'sprak': {'kode': 'EN',
                                'navn': 'Engelsk',
                                'navnEngelsk': 'English'},
                      'tekst': 'Allele Interaction - Single Locus Genetics Meets '
                               'Regulatory Biology'}],
      'sprak': {'kode': 'EN', 'navn': 'Engelsk', 'navnEngelsk': 'English'},
      'tidsskrift': {'@oaDoaj': 'true',
                     'id': '435449',
                     'issn': '1932-6203',
                     'kvalitetsniva': {'kode': '1', ...},
                     'navn': 'PLoS ONE',
                     ...},
      'tittel': 'Allele Interaction - Single Locus Genetics Meets Regulatory '
                'Biology',
      'volum': '5'},
     ...
     {...
      'ar': '2010',
      'arRapportert': '2010',
      'doi': '10.1002/cem.1363',
      ...
      'id': '771116',
      ...
      'person': [{'etternavn': 'Tøndel', ...},
                 {'etternavn': 'Gjuvsland', ...},
                 ...],
      ...
      'sideangivelse': {'sideFra': '738', 'sideTil': '747'},
      'sprak': {'kode': 'EN', 'navn': 'Engelsk', 'navnEngelsk': 'English'},
      'tidsskrift': {'id': '5117',
                     'issn': '0886-9383',
                     'kvalitetsniva': {'kode': '1', ...},
      'tittel': 'Screening design for computer experiments: metamodelling of a '
                'deterministic mathematical model of the mammalian circadian clock',
      'volum': '24'}]

    Funding sources are in pubs[i]["fellesdata"]["eksternprosjekt"].

    >>> pprint(pubs_by("Jon Olav Vik", 2014, 2014))
    [{'ar': '2014',
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
    pubs = requests.get(url).json()["forskningsresultat"]
    for i, d in enumerate(pubs):
        # Reduce nesting in the dict for each publication
        e = dict()
        e.update(d["fellesdata"])
        e.update(d["kategoridata"])
        e.update(e["tidsskriftsartikkel"])
        del e["tidsskriftsartikkel"]  # Don't want to duplicate this
        pubs[i] = e
    return pubs


def format_author(a):
    """
    Format author name.

    >>> format_author(dict(fornavn="Odd Even", etternavn="Strange"))
    'Strange OE'
    >>> format_author(dict(fornavn="Odd-Even", etternavn="Strange"))
    'Strange OE'
    """
    given_names = a["fornavn"].replace("-", " ").split()
    initials = "".join(i[0] for i in given_names)
    return a["etternavn"] + " " + initials

def deduplicate(pubs):
    """
    Remove duplicate publications from list.

    >>> abg = pubs_by("Arne Gjuvsland", fra=2010, til=2014)
    >>> jov = pubs_by("Jon Olav Vik", fra=2010, til=2014)
    >>> len(abg)
    17
    >>> len(jov)
    10
    >>> len(deduplicate([abg, jov]))
    19
    """
    return {p["id"]: p for p in itertools.chain(*pubs)}.values()

def citation(pub, html=False):
    """
    Citation of a single publication.

    >>> pub0, pub1 = pubs_by("Arne Gjuvsland", 2010, 2010)
    >>> sorted(pub0.keys())
    ['alternativTittel', 'ar', 'arRapportert', 'artikkelnr', 'doi', 'eier', 'endret', 'erPublisert', 'hefte', 'id',
    'idItar', 'importertFra', 'kategori', 'kontrollert', 'oversettelseAv', 'person', 'rapportdata', 'registrert',
    'sammendrag', 'sprak', 'tidsskrift', 'tittel', 'volum']

    >>> print(citation(pub0))
    Gjuvsland AB, Plahte E, Ådnøy T, Omholt SW (2010)
    Allele Interaction - Single Locus Genetics Meets Regulatory Biology.
    PLoS ONE 5:e9379, doi:10.1371/journal.pone.0009379
    >>> print(citation(pub1))
    Tøndel K, Gjuvsland AB...(2010)
    Screening design for computer experiments:
    metamodelling of a deterministic mathematical model of the mammalian circadian clock.
    Journal of Chemometrics 24:738-747, doi:10.1002/cem.1363
    >>> print(citation(pub0, html=True))
    Gjuvsland AB, Plahte E, Ådnøy T, Omholt SW (2010)
    Allele Interaction - Single Locus Genetics Meets Regulatory Biology.
    <em>PLoS ONE</em> <strong>5</strong>:e9379
    doi:<a href="http://dx.doi.org/10.1371/journal.pone.0009379">10.1371/journal.pone.0009379</a>
    """
    pub = defaultdict(str, pub)  # Simplifies string formatting if fields are missing
    pub["authors"] = ", ".join(format_author(a) for a in pub["person"])
    if "sideangivelse" in pub:
        pages = pub["sideangivelse"]
        if "sideFra" in pages:
            pub["pages"] = pages["sideFra"] + "-" + pages["sideTil"]
        else:
            pub["pages"] = pages["antallSider"] + " pages"
    elif "artikkelnr" in pub:
        pub["pages"] = pub["artikkelnr"]
    if html:
        fmt = ('{authors} ({ar}) {tittel}. <em>{tidsskrift[navn]}</em> <strong>{volum}</strong>:{pages} '
               'doi:<a href="http://dx.doi.org/{doi}">{doi}</a>')
    else:
        fmt = "{authors} ({ar}) {tittel}. {tidsskrift[navn]} {volum}:{pages}, doi:{doi}"
    return fmt.format(**pub)


def bibliography_author(author, *args, **kwargs):
    """
    Bibliography of a list of publications.

    All arguments are passed to pubs_by().

    >>> print(bibliography_author("Jon Olav Vik"))
    <h1>Publication list - Jon Olav Vik</h1>
    ...
    <p>Vik JO, Borgstrøm R, Skaala Ø (2001) Cannibalism governing mortality of juvenile brown trout, Salmo trutta, ...
    """
    s = "<h1>Publication list - {}</h1>\n".format(author)
    pubs = pubs_by(author, *args, **kwargs)
    pubs.sort(key=operator.itemgetter("ar"), reverse=True)
    s += "\n".join("<p>{}</p>".format(citation(pub, html=True)) for pub in pubs)
    return s


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile HTML bibliography from CRISTIN for list of authors.")
    parser.add_argument("-d", "--debug", help="log debug messages", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    authors = """
    Jon Olav Vik
    Dag Inge Våge
    Sigbjørn Lien
    Arne Bjørke Gjuvsland
    """
    authors = [a.strip() for a in authors.strip().split("\n")]
    pubs = [pubs_by(a, fra=2003, til=2015) for a in authors]
    logging.debug("%s authors with a total of %s publications", len(authors), sum(len(p) for p in pubs))
    pubs = deduplicate(pubs)
    logging.debug("%s unique publications", len(pubs))
