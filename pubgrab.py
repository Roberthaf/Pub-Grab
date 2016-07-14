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

Test:
python pubgrab.py --debug "Jon Olav Vik" "Dag Inge Våge" "Sigbjørn Lien" "Arne Bjørke Gjuvsland"
"""

import argparse
import itertools
import os
import tempfile
import requests
import logging
from urllib.parse import urlencode
from collections import defaultdict
from typing import Mapping, Sequence, Union
import sys

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
def pubs_by(author: str, fra=1900, til=9999, hovedkategori: str="TIDSSKRIFTPUBL") -> Sequence[Mapping]:
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

    An empty list is returned if there are no publications or the author is not found.

    >>> pubs_by("Jon Olav Vik", 2010, 2010)
    []
    >>> pubs_by("Someone who doesn't exist")
    []

    Verify that we handle single-author publications correctly.
    Cristin returns a simple dict for pub["person"] for single-author papers, but a list of dict for multi-author ones.
    For consistency, we wrap even a single author dict in a list.

    >>> [citation(pub) for pub in pubs_by("Stig Omholt", fra=2013, til=2013) if len(pub["person"]) == 1]
    ['Omholt SW (2013) From sequence to consequence and back. ... doi:10.1016/j.pbiomolbio.2012.09.003']
    """
    cpid = cristin_person_id(author)
    if cpid is None:
        return []
    base = "http://www.cristin.no/ws/hentVarbeiderPerson?"
    url = base + urlencode(dict(lopenr=cpid, fra=fra, til=til, hovedkategori=hovedkategori, format="json"))
    r = requests.get(url)
    if r.status_code == 404:
        return []
    pubs = r.json()["forskningsresultat"]
    for i, d in enumerate(pubs):
        # Reduce nesting in the dict for each publication
        e = dict()
        e.update(d["fellesdata"])
        e.update(d["kategoridata"])
        e.update(e["tidsskriftsartikkel"])
        del e["tidsskriftsartikkel"]  # Don't want to duplicate this
        # Ensure the author list in e["person"] is always a list of dict.
        # From Cristin, single-author papers have just a dict in e["person"],
        # whereas multi-author papers have a list of dict.
        if hasattr(e["person"], "keys"):
            e["person"] = [e["person"]]
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


def deduplicate(pubs: Sequence[Mapping]) -> Sequence[Mapping]:
    """
    Remove duplicate publications from list.

    >>> abg = pubs_by("Arne Gjuvsland", fra=2010, til=2014)
    >>> jov = pubs_by("Jon Olav Vik", fra=2010, til=2014)
    >>> len(abg)
    17
    >>> len(jov)
    10
    >>> len(abg + jov)
    27
    >>> len(deduplicate(abg + jov))
    19
    """
    return list({p["id"]: p for p in pubs}.values())


def citation(pub: Mapping, html=False):
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
    pub = defaultdict(str, **pub)  # Simplifies string formatting if fields are missing
    pub["authors"] = ", ".join(format_author(a) for a in pub["person"])
    if "sideangivelse" in pub:
        pages = defaultdict(str, **pub["sideangivelse"])
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


def pub_sort_key(pub: Mapping):
    """
    Function to sort publications most recent first, then alphabetically by authors.

    Use the negative value of the year to place the most recent first.

    >>> pubs = pubs_by("Jon Olav Vik", fra=2000, til=2004)
    >>> sorted([pub_sort_key(pub) for pub in pubs])
    [[-2004, 'Vik JO', 'Stenseth NC', 'Tavecchia G', 'Mysterud A', 'Lingjærde OC'],
     [-2001, 'Vik JO', 'Borgstrøm R', 'Skaala Ø']]
    """
    return [-int(pub["ar"])] + [format_author(a) for a in pub["person"]]


def bibliography(pubs: Sequence[Mapping]) -> str:
    """
    Bibliography of a list of publications.

    >>> pubs = pubs_by("Jon Olav Vik", fra=2000, til=2004)
    >>> print(bibliography(pubs))
    <p>Vik JO, ... (2004) Living in synchrony on Greenland coasts?. <em>Nature</em> <strong>427</strong>:697-698...
    <p>Vik JO, Borgstrøm R, Skaala Ø (2001) Cannibalism governing mortality of juvenile brown trout, Salmo trutta, ...

    Duplicate publications are removed.

    >>> print(bibliography(pubs + pubs))
    <p>Vik JO, ... (2004) Living in synchrony on Greenland coasts?. <em>Nature</em> <strong>427</strong>:697-698...
    <p>Vik JO, Borgstrøm R, Skaala Ø (2001) Cannibalism governing mortality of juvenile brown trout, Salmo trutta, ...
    """
    pubs = sorted(deduplicate(pubs), key=pub_sort_key)
    return "\n".join("<p>{}</p>".format(citation(pub, html=True)) for pub in pubs)


def bibliography_author(authors: Union[str, Sequence[str]], *args, **kwargs) -> str:
    """
    Bibliography of a list of publications by a single author or a list of authors.

    All arguments are passed to pubs_by().

    Bibliography for one author.

    >>> print(bibliography_author("Jon Olav Vik", fra=2000, til=2004))
    <p>Vik JO, ... (2004) Living in synchrony on Greenland coasts?. <em>Nature</em> <strong>427</strong>:697-698 ...
    <p>Vik JO, Borgstrøm R, Skaala Ø (2001) Cannibalism governing mortality of juvenile brown trout, Salmo trutta, ...

    For two authors.

    >>> print(bibliography_author("Arne Gjuvsland", fra=2010, til=2010))
    <p>Gjuvsland AB, ... (2010) Allele Interaction - Single Locus Genetics Meets Regulatory Biology. ...
    <p>Tøndel K, ... (2010) Screening design for computer experiments: ...
    >>> print(bibliography_author(["Jon Olav Vik", "Arne Gjuvsland"], fra=2009, til=2010))
    <p>Gjuvsland AB, ... (2010) Allele Interaction - Single Locus Genetics Meets Regulatory Biology. ...
    <p>Tøndel K, ... (2010) Screening design for computer experiments: ...
    <p>Godvik IMR, ... (2009) Temporal scales, trade-offs, and functional responses in red deer habitat selection. ...
    """
    # Ensure author is a list
    if isinstance(authors, str):
        authors = [authors]
    # Convert generator to list for easier debugging if things fail later
    pubs = list(itertools.chain.from_iterable(pubs_by(a, *args, **kwargs) for a in authors))
    return bibliography(pubs)


if __name__ == "__main__":
    descr = "Compile HTML bibliography from CRISTIN for list of authors.\n\nIf no authors are given, read from stdin."
    epilog = ("To work with non-ascii author names, set the console code page and Python i/o encoding to utf-8.\n"
              "In a Windows command shell:\n\n"
              "> CHCP 65001\n"
              "> SET PYTHONIOENCODING=UTF-8\n\n"
              "Then run e.g.\n\n"
              "> python pubgrab.py 'Dag Inge Våge'\n"
              "> python pubgrab.py < people.txt > publications.html")
    parser = argparse.ArgumentParser(description=descr, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", help="log debug messages", action="store_true")
    parser.add_argument("authors", help="list of authors, e.g. 'Jane Doe' 'John Deere'", nargs="*")
    parser.add_argument("--fra", default=2003, help="from year")
    parser.add_argument("--til", default=2015, help="to year")
    parser.add_argument("--hovedkategori", metavar="HKAT", default="TIDSSKRIFTPUBL", help="Hovedkategori, see\n"
                        "http://www.cristin.no/cristin/superbrukeropplaering/ws-dokumentasjon.html#hovedkategorier2011")
    parser.add_argument("--clear", help="clear cache", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.clear:
        mem.clear()
    logging.debug("Authors: %s", args.authors)
    if not args.authors:
        args.authors = [i.strip() for i in sys.stdin if i.strip()]
    if args.authors:
        print("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="utf-8"/>
        </head>
        <body>
        {}
        </body>
        </html>
        """.format(bibliography_author(args.authors, fra=args.fra, til=args.til, hovedkategori=args.hovedkategori)))
