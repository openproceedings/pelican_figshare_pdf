# -*- coding: utf-8 -*-
'''
Figshare Generator
-------

Uploads PDF versions of articles to FigShare
'''

from __future__ import unicode_literals, print_function

from pelican import signals, settings
from pelican.generators import Generator

import os
import logging

logger = logging.getLogger(__name__)

import exceptions

### figshare
import requests
from requests_oauthlib import OAuth1
import json

class FigshareInterface(object):

    def __init__(self):
        self.oauth = OAuth1( client_key=settings["FIGSHARE_CLIENT_KEY"], client_secret=settings["FIGSHARE_CLIENT_SECRET"],
                   resource_owner_key=settings["FIGSHARE_TOKEN_KEY"], resource_owner_secret=settings["FIGSHARE_TOKEN_SECRET"], signature_type = 'auth_header')
        self.client = requests.session()

    def create_article(self, obj):
        """Creates new article on FigShare from Pelican post object"""
        body = {'title':obj.title, 'description':obj.summary,'defined_type':'dataset'}
        headers = {'content-type':'application/json'}

        logging.info("Create new article on FigShare")
        response = self.client.post('http://api.figshare.com/v1/my_data/articles', auth=self.oauth, data=json.dumps(body), headers=headers)

        results = json.loads(response.content)
        article_id = results["article_id"]
        doi = results["doi"]
        return article_id, doi

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
        for author in authors:
            response = self.client.get('http://api.figshare.com/v1/my_data/authors?search_for=%s' % author, auth=self.oauth)
            results = json.loads(response.content)

            try:
                if results["results"] == 0:
                    logger.info("Author %s not found, creating" % author)
                    body = {'full_name':author}
                    headers = {'content-type':'application/json'}
                    response = self.client.post('http://api.figshare.com/v1/my_data/authors', auth=self.oauth,
                                            data=json.dumps(body), headers=headers)
                    results = json.loads(response.content)
                    author_id = results["id"]
                else:
                    author_id = results["items"][0]["id"] # get first matching author

                body = {'author_id':author_id}
                headers = {'content-type':'application/json'}

                response = self.client.put('http://api.figshare.com/v1/my_data/articles/%d/authors' % article_id, auth=self.oauth,
                                        data=json.dumps(body), headers=headers)
                results = json.loads(response.content)
            except exceptions.KeyError:
                logger.error("Cannot create author %s, figshare response %s" % (author, json.dumps(results)))
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

    def _upload_figshare(self, obj, output_path):
        if obj.source_path.endswith('.rst'):
            filename = obj.slug + ".pdf"
            output_pdf = os.path.join(output_path, filename)
            json_filename = obj.slug + "-figshare.json"
            output_json = os.path.join(output_path, json_filename)
            if os.path.exists(output_pdf):
                figshare = FigshareInterface()

                if os.path.exists(output_json):
                    with open(output_json, "r") as json_file:
                        meta = json.load(json_file)
                else:
                    meta = {"update":False}
                    meta["article_id"], meta["doi"] = figshare.create_article(obj)

                    figshare.set_category(meta["article_id"], settings.get("FIGSHARE_CATEGORY_ID", 77)) # default applied computer science
                    figshare.set_tag(meta["article_id"], "proceedings")
                    figshare.set_authors(meta["article_id"],  [author.strip() for author in obj.author.name.split(",")])

                if meta["update"]:
                    figshare.upload_pdf(meta["article_id"], output_pdf)

                meta["update"] = False
                with open(output_json, "w") as json_file:
                    json.dump(meta, json_file)
            else:
                logger.error("Missing PDF file: %s" % output_pdf)

    def generate_context(self):
        pass

    def generate_output(self, writer=None):
        logger.info(' Uploading PDF files to Figshare...')
        pdf_path = os.path.join(self.output_path, 'pdf')

        for article in self.context['articles']:
            self._upload_figshare(article, pdf_path)

def get_generators(generators):
    return FigshareGenerator

def register():
    signals.get_generators.connect(get_generators)
