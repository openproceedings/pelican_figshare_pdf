import os
from glob import glob
#import json
from figshare_pdf import FigshareInterface
from pelican.settings import read_settings

settings = read_settings(path="../../pelicanconf.py")

output_path = "/home/zonca/dev/openproceedings/openproceedings-buildbot/output/pdf"
output_pdf = glob(os.path.join(output_path, "*.pdf"))[0]
json_filename = output_pdf.replace(".pdf", "-figshare.json")
output_json = os.path.join(output_path, json_filename)

class EmptyObject(object):
    pass

obj = EmptyObject()
obj.title = "Test Figshare PDF"
obj.summary = "Summary goes here"
obj.author = EmptyObject()
obj.author.name = "Firstname Lastname, Firstname2 Lastname2"

meta = {}
figshare = FigshareInterface(settings)

meta["article_id"], meta["doi"], response = figshare.create_article(obj)

#figshare.set_category(meta["article_id"], settings.get("FIGSHARE_CATEGORY_ID", 77)) # default applied computer science
#figshare.set_tag(meta["article_id"], "proceedings")
#figshare.set_authors(meta["article_id"],  [author.strip() for author in obj.author.name.split(",")])
#
#figshare.upload_pdf(meta["article_id"], output_pdf)
