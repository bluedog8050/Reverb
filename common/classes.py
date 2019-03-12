import json
import logging
import os
import re
from datetime import datetime

import discord

log = logging.getLogger('bot.common')

class JsonFileObject(dict):
    '''Represents a JSON file on disk'''

    def __init__(self, filename, **default):
        try:
            os.mkdir(os.path.abspath(f'./data'))
        except FileExistsError:
            pass

        self.filename = os.path.abspath(f'./data/{filename}')
        
        try:
            with open(self.filename, 'r') as f:
                super().__init__(json.load(f))
        except FileNotFoundError:
            logging.warning(f'Unable to read {self.filename}')
            super().__init__(default)
            with open(self.filename, 'w+') as f:
                json.dump(self, f, indent = 4)

    def save(self):
        with open(self.filename, 'w+') as f:
            json.dump(self, f, indent = 4)

    def savecopy(self, as_filename):
        with open(as_filename, 'w+') as f:
            json.dump(self, f, indent = 4)

class Ledger:
    ## {'server':{'user':['oct-18-2018',1,2,'This is a test entry']},}
    def __init__(self, data_directory, name, unit_string, *flags):
        self.name = name
        self.data_dir = data_directory
        self.unit_string = unit_string
        
        try:
            with open(os.path.abspath(f'{os.path.join(self.data_dir, self.name)}.json')) as f:
                self.data = json.load(f)
        except:
            self.data = {}
        if 'prefix' in flags: self.prefix = True 
        else: self.prefix = False
        if 'allow_negative' in flags: self.allow_negative = True 
        else: self.allow_negative = False
        
        return

    # SERVER > USER > [date, change, balance, note],
    #ANCHOR ADD ENTRY
    def addentry(self, server, user, amount_change, note=''):
        # try:    
        if server not in self.data: self.data.update({server : {}})
        if user not in self.data[server]: self.data[server].update({user : []})
        try:
            balance = int(self.data[server][user][-1][2])+int(amount_change)
        except:
            balance = int(amount_change)
        entry = [datetime.datetime.now().strftime(r"%Y-%m-%d"), str(amount_change), str(balance), note]
        print(entry)
        self.data[server][user].append(entry)
        message = True

        return message
    #ANCHOR GET BALANCE
    def getbalance(self, server, user, *flags):
        '''Returns current balance for user
        Flags:
        \'int\' - returns balance as integer'''
        try:
            if 'int' in flags:
                balance = int(self.data[server][user][-1][2])
            else:
                balance = (self.unit_string + self.data[server][user][-1][2]) if self.prefix else (self.data[server][user][-1][2] + ' ' + self.unit_string)
        except KeyError:
            if 'int' in flags:
                balance = 0
            else:
                balance = 'no transaction history'
        return balance
    #ANCHOR SAVE TO FILE
    def savetofile(self):
        '''Save ledger to JSON file'''
        try:
            with open(os.path.abspath(f'{os.path.join(self.data_dir, self.name)}.json'), 'w+') as outfile:
                json.dump(self.data, outfile)
        except:
            print('{} ledger could not be saved to file!'.format(self.unit_string))
            return
    #ANCHOR GET HISTORY
    def gethistory(self, server, user, lines=5):
        '''Return a formatted history statement'''
        history = 'Date\t\tChange\tBal\tNote\n-------------------------------------\n'
        for i in range(1, int(lines) + 1):
            try:
                history = history + str(self.data[server][user][-i]) + '\n'
            except:
                break
        history = history.replace(', ',',\t').replace('\'', '').replace('[','').replace(']','')
        return history
    #ANCHOR TRANSFER
    def transfer(self, server, sender, recipients : list, amount, note):
        if int(amount) * len(recipients) > self.getbalance(server, sender, 'int'):
            pass
            #await client.send_message()
#!SECTION 
