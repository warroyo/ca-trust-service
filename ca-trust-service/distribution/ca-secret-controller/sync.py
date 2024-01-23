#!/usr/bin/env python

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging


logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


class Controller(BaseHTTPRequestHandler):

    def create_secret(self,object,related):
        LOGGER.info("Logging related objects ---> {0}".format(related['Secret.v1']))
        if len(related['Secret.v1']) == 0:
            LOGGER.info("no secrets match required name")
            return []
        else:
            return [
                {
                    "apiVersion": "v1",
                    "data": related['Secret.v1']['ca-trust-service-secret']['data'],
                    "kind": "Secret",
                    "metadata": {
                        "name": object['metadata']['name'] + "-user-trusted-ca-secret",
                        "namespace": object['metadata']['namespace'],
                        
                    },
                    "type": "Opaque"
                }
            ]


    def customize(self) -> dict:
        return [
            {
                'apiVersion': 'v1',
                'resource': 'secrets',
                'names': ["ca-trust-service-secret"]
            }
        ]
   
    def do_POST(self):
        if self.path == '/sync':
            observed = json.loads(self.rfile.read(int(self.headers.get('content-length'))))
            LOGGER.info("/sync %s", observed['object']['metadata']['name'])
            secret = self.create_secret(observed['object'], observed['related']) 
            response = {
                "attachments": secret
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif self.path == '/customize':
            request: dict = json.loads(self.rfile.read(
                int(self.headers.get('content-length'))))
            parent: dict = request['parent']
            LOGGER.info("/customize %s", parent['metadata']['name'])
            LOGGER.info("Parent resource: \n %s", parent['spec'])
            related_resources: dict = {
                'relatedResources': self.customize()
            }
            LOGGER.info("Related resources: \n %s", related_resources)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(related_resources).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg: dict = {
                'error': '404',
                'endpoint': self.path
            }
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))

HTTPServer(('', 80), Controller).serve_forever()




