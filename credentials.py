# -*- coding: utf-8 -*-

import pykeepass

class GetCredentials:

    def __init__(self, base, password):

        self.kp = pykeepass.PyKeePass(base, password=password)

    def artistikRezoUsername(self):
        return self.kp.find_entries(title='artistikRezo', first=True).username

    def artistikRezoPassword(self):
        return self.kp.find_entries(title='artistikRezo', first=True).password

    def mongoDbUsername(self):
        return self.kp.find_entries(title='MONGODB', first=True).username

    def mongoDbPassword(self):
        return self.kp.find_entries(title='MONGODB', first=True).password

    def mongoDbUrl(self):
        return self.kp.find_entries(title='MONGODB', first=True).url

    def emailUsername(self):
        return self.kp.find_entries(title='emailAccount', first=True).username

    def emailPassword(self):
        return self.kp.find_entries(title='emailAccount', first=True).password