-------------
Upload PDF to FigShare
-------------

Automatically publish articles to FigShare in PDF format.

Add `figshare_pdf` plugin after `pdf` in the plugins:

    PLUGINS = ["pdf", "figshare_pdf"]

Get API credentials from your FigShare account and add them to `pelicanconf.py`:

    FIGSHARE_CLIENT_KEY = ''
    FIGSHARE_CLIENT_SECRET = ''
    FIGSHARE_TOKEN_KEY = ''
    FIGSHARE_TOKEN_SECRET = ''
    FIGSHARE_CATEGORY_ID = 77 #applied computer science

Also creates a `bibtex` entry for each article as `output/bib/slug.bib`,
based on the template in `pelicanconf.py`:

    FIGSHARE_BIBTEX_TEMPLATE = """@InProceedings{ %(tag)s-openproc-2013,
      author    = { %(authors)s },
      title     = { %(title)s },
      booktitle = { Test Proceedings for OpenProceedings },
      year      = { 2013 },
      editor    = { Editor Name },
      doi    = { %(doi)s },
      url    = { %(url)s }
    }

How it works:

* runs after PDF plugin
* creates new private article on figshare
* fills all metadata fields
* articles should have a `author_figshare_ids` field with comma separated list of author ids from FigShare, otherwise
only the author who owns the API credentials will be listed 
* uploads PDF
* writes figshare ID and DOI to json file in the `content/` folder names `article-slug-figshare.json`
* creates a `bibtex` file which includes the DOI and URL from FigShare
* json also includes a field `update=False`
* next run, it updates the PDF with a new version only if `update=True`, this way we do not trigger updates on every run
