import json
import logging

class JsonFileObject(dict):
    '''Represents a JSON file on disk'''
    def __init__(self, filename, **default):
        self.filename = filename
        try:
            with open(filename, 'r') as f:
                super().__init__(json.load(f))
        except FileNotFoundError:
            logging.warning(f'Unable to read {filename}')
            super().__init__(default)
            with open(filename, 'w+') as f:
                json.dump(self, f, indent = 4)
    def save(self):
        with open(self.filename, 'w+') as f:
            json.dump(self, f, indent = 4)
    def savecopy(self, filename):
        with open(filename, 'w+') as f:
            json.dump(self, f, indent = 4)