# -*- coding: utf-8 -*-
'''
Figshare Generator
-------

Uploads PDF versions of articles to FigShare
'''

from __future__ import unicode_literals, print_function
import exceptions

from pelican import signals
from pelican.generators import Generator

import os
import os.path
import logging

logger = logging.getLogger(__name__)

### figshare
import requests
from requests_oauthlib import OAuth1
import json

class FigshareAPIError(exceptions.Exception):
    pass

class FigshareInterface(object):

    def __init__(self, settings):
        self.settings = settings
        self.oauth = OAuth1( client_key=self.settings["FIGSHARE_CLIENT_KEY"], client_secret=self.settings["FIGSHARE_CLIENT_SECRET"],
                   resource_owner_key=self.settings["FIGSHARE_TOKEN_KEY"], resource_owner_secret=self.settings["FIGSHARE_TOKEN_SECRET"], signature_type = 'auth_header')
        self.client = requests.session()

    def create_article(self, obj):
        """Creates new article on FigShare from Pelican post object"""
        body = {'title':obj.title, 'description':obj.summary,'defined_type':'dataset'}
        headers = {'content-type':'application/json'}

        logging.info("Create new article on FigShare")
        response = self.client.post('http://api.figshare.com/v1/my_data/articles', auth=self.oauth, data=json.dumps(body), headers=headers)

        results = json.loads(response.content)
        if results.has_key("error"):
            logger.error(results["error"])
            raise FigshareAPIError(results["error"])
        article_id = results["article_id"]
        doi = results["doi"]
        return article_id, doi, results

    def set_category(self, article_id, category_id):
        body = {'category_id': category_id}
        headers = {'content-type':'application/json'}
        response = self.client.put('http://api.figshare.com/v1/my_data/articles/%d/categories' % article_id, auth=self.oauth,
                                data=json.dumps(body), headers=headers)
        results = json.loads(response.content)
        return results

    def set_tag(self, article_id, tag):
        body = {'tag_name':'proceedings'}
        headers = {'content-type':'application/json'}
        response = self.client.put('http://api.figshare.com/v1/my_data/articles/%d/tags' % article_id, auth=self.oauth,
                                data=json.dumps(body), headers=headers)
        results = json.loads(response.content)
        return results

    def set_authors(self, article_id, authors):
        for author_id in authors:
            #response = self.client.get('http://api.figshare.com/v1/my_data/authors?search_for=%s' % author, auth=self.oauth)
            #results = json.loads(response.content)

            #try:
#                if results["results"] == 0:
#                    logger.info("Author %s not found, creating" % author)
#                    body = {'full_name':author}
#                    headers = {'content-type':'application/json'}
#                    response = self.client.post('http://api.figshare.com/v1/my_data/authors', auth=self.oauth,
#                                            data=json.dumps(body), headers=headers)
#                    results = json.loads(response.content)
#                    author_id = results["id"]
#                else:
#                    author_id = results["items"][0]["id"] # get first matching author
#
            body = {'author_id':author_id}
            headers = {'content-type':'application/json'}

            response = self.client.put('http://api.figshare.com/v1/my_data/articles/%d/authors' % article_id, auth=self.oauth,
                                    data=json.dumps(body), headers=headers)
            results = json.loads(response.content)
            #except exceptions.KeyError:
            #    logger.error("Cannot create author %s, figshare response %s" % (author, json.dumps(results)))
        return results


    def upload_pdf(self, article_id, output_pdf):
        files = {'filedata':(os.path.basename(output_pdf), open(output_pdf, 'rb'))}
        logger.info("Uploading PDF")
        response = self.client.put('http://api.figshare.com/v1/my_data/articles/%d/files' % article_id, auth=self.oauth,
                              files=files)
        results = json.loads(response.content)
        return results

    def make_public(self, article_id):
        response = self.client.post('http://api.figshare.com/v1/my_data/articles/%d/action/make_public' % article_id, auth=self.oauth)
        results = json.loads(response.content)
        return results

class FigshareGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(FigshareGenerator, self).__init__(*args, **kwargs)

    def _upload_figshare(self, obj, output_path, bib_path):
        if obj.source_path.endswith('.rst'):
            filename = obj.slug + ".pdf"
            output_pdf = os.path.join(output_path, filename)
            output_json = obj.source_path.replace(".rst", "-figshare.json")
            if os.path.exists(output_pdf):
                figshare = FigshareInterface(self.settings)

                if os.path.exists(output_json):
                    with open(output_json, "r") as json_file:
                        meta = json.load(json_file)
                else:
                    meta = {"update":True}
                    meta["article_id"], meta["doi"], _ = figshare.create_article(obj)

                    figshare.set_category(meta["article_id"], self.settings.get("FIGSHARE_CATEGORY_ID", 77)) # default applied computer science
                    figshare.set_tag(meta["article_id"], "proceedings")
                    if hasattr(obj, "author_figshare_ids"):
                        figshare.set_authors(meta["article_id"],  map(int, obj.author_figshare_ids.split(",")))

                if meta["update"]:
                    figshare.upload_pdf(meta["article_id"], output_pdf)

                meta["update"] = False
                with open(output_json, "w") as json_file:
                    json.dump(meta, json_file)

                output_bib = os.path.join(bib_path, obj.slug + ".bib")
                input_filename = os.path.splitext(os.path.basename(obj.source_path))[0]
                with open(output_bib, "w") as bib_file:
                    bib_file.write(self.settings["FIGSHARE_BIBTEX_TEMPLATE"] % dict(
                                                                                authors=obj.author, 
                                                                                title=obj.title, 
                                                                                doi=meta["doi"].replace("http://dx.doi.org/",""),
                                                                                url=meta["doi"],
                                                                                tag=input_filename))
            else:
                logger.error("Missing PDF file: %s" % output_pdf)
            

    def generate_context(self):
        pass

    def generate_output(self, writer=None):
        logger.info(' Uploading PDF files to Figshare...')
        pdf_path = os.path.join(self.output_path, 'pdf')
        bib_path = os.path.join(self.output_path, 'bib')
        if not os.path.exists(bib_path):
            try:
                os.mkdir(bib_path)
            except OSError:
                logger.error("Couldn't create the bib output folder in " +
                             bib_path)

        for article in self.context['articles']:
            self._upload_figshare(article, pdf_path, bib_path)

def get_generators(generators):
    return FigshareGenerator

def register():
    signals.get_generators.connect(get_generators)
