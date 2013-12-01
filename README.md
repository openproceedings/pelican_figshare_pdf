-------------
Upload PDF to FigShare
-------------

Publish to figshare plugin:

* runs after PDF plugin
* creates new private article on figshare
* fills all metadata fields
* uploads PDF
* writes figshare ID and DOI to json file in the `content/` folder names `article-slug-figshare.json`
* json also includes a field `publish=False`
* next run, it updates the PDF with a new version only if `publish=True`, this way we do not trigger updates on every run
