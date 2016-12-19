# Pub-Grab

pubgrab.py will generate an html publication list for given authors, retrieving records from the [CRISTIN](http://cristin.no) database of Norwegian scientific publications.

Sample output: [Centre for Integrative Genetics' publication list](http://cigene.no/all-publications/).

# Prerequisites

* [python 3](http://python.org)
* [joblib](https://pythonhosted.org/joblib/), e.g. ```pip install joblib```

# Installation

    git clone https://github.com/Roberthaf/Pub-Grab.git
    cd Pub-Grab
    python pubgrab.py --help

To process non-ascii characters, please read the help text below closely.
If your console code page and python input/output encoding are set correctly, the example near the end should show "Våge" with an "å".

# Usage instructions

	usage: pubgrab.py [-h] [-d] [--fra FRA] [--til TIL] [--hovedkategori HKAT]
					  [--clear]
					  [authors [authors ...]]

	Compile HTML bibliography from CRISTIN for list of authors.

	If no authors are given, read from stdin.

	positional arguments:
	  authors               list of authors, e.g. 'Jane Doe' 'John Deere'

	optional arguments:
	  -h, --help            show this help message and exit
	  -d, --debug           log debug messages
	  --fra FRA             from year
	  --til TIL             to year
	  --hovedkategori HKAT  Hovedkategori, see http://www.cristin.no/cristin/super
							brukeropplaering/ws-
							dokumentasjon.html#hovedkategorier2011
	  --clear               clear cache

	To work with non-ascii author names, set the console code page and Python i/o encoding to utf-8.
	In a Windows command shell:

	> CHCP 65001
	> SET PYTHONIOENCODING=UTF-8

	Then run e.g.

	> python pubgrab.py 'Dag Inge Våge'
	> python pubgrab.py < people.txt > publications.html

# Cristin API resources

* [New API docs](https://api.cristin.no/index.html)
* [New JSON schema](https://api.cristin.no/v1/doc/json-schemas/)
* [Old API docs](http://www.cristin.no/cristin/superbrukeropplaering/ws-dokumentasjon.html#toc5)
* [Old XML schema](http://www.cristin.no/techdoc/xsd/resultater/1.0/)
* [Info on transition from old to new API](http://www.cristin.no/om/aktuelt/aktuelle-saker/2016/api-lansering.html)
