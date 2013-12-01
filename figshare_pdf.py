# -*- coding: utf-8 -*-
'''
Figshare Generator
-------

Uploads PDF versions of articles to FigShare
'''

from __future__ import unicode_literals, print_function

from pelican import signals
from pelican.generators import Generator

import os
import logging

logger = logging.getLogger(__name__)

### figshare
import requests
from requests_oauthlib import OAuth1
import json

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
                oauth = OAuth1(client_key=client_key, client_secret=client_secret,
                               resource_owner_key=token_key, resource_owner_secret=token_secret,
                                              signature_type = 'auth_header')
                client = requests.session()
                body = {'title':obj.title, 'description':obj.summary,'defined_type':'dataset'}
                headers = {'content-type':'application/json'}

                #response = client.post('http://api.figshare.com/v1/my_data/articles', auth=oauth, data=json.dumps(body), headers=headers)

                #results = json.loads(response.content)
                #print(results["doi"])
                #article_id = results["article_id"]
                article_id = 852126

                body = {'category_id':77} # applied computer science
                headers = {'content-type':'application/json'}
                response = client.put('http://api.figshare.com/v1/my_data/articles/%d/categories' % article_id, auth=oauth,
                                        data=json.dumps(body), headers=headers)
                results = json.loads(response.content)

                body = {'tag_name':'proceedings'}
                headers = {'content-type':'application/json'}
                response = client.put('http://api.figshare.com/v1/my_data/articles/%d/tags' % article_id, auth=oauth,
                                        data=json.dumps(body), headers=headers)
                results = json.loads(response.content)
                authors = [author.strip() for author in obj.author.name.split(",")]
                for author in authors:
                    print(author)

                    response = client.get('http://api.figshare.com/v1/my_data/authors?search_for=Kapil Arya', auth=oauth)
                    results = json.loads(response.content)
                    print(results)

                    if results["results"] == 0:
                        body = {'full_name':author}
                        headers = {'content-type':'application/json'}
                        response = client.post('http://api.figshare.com/v1/my_data/authors', auth=oauth,
                                                data=json.dumps(body), headers=headers)
                        results = json.loads(response.content)
                        print(results)

                    body = {'author_id':results["author_id"]}
                    headers = {'content-type':'application/json'}

                    response = client.put('http://api.figshare.com/v1/my_data/articles/%d/authors' % article_id, auth=oauth,
                                            data=json.dumps(body), headers=headers)
                    results = json.loads(response.content)

                    files = {'filedata':(os.path.basename(output_pdf), open(output_pdf, 'rb'))}

                    response = client.put('http://api.figshare.com/v1/my_data/articles/%d/files' % article_id, auth=oauth,
                                          files=files)
                    results = json.loads(response.content)
                    print(results)
                    #response = client.post('http://api.figshare.com/v1/my_data/articles/%d/action/make_public' % article_id, auth=oauth)
                    #results = json.loads(response.content)
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
