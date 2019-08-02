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
    def __init__(self, name, data):
        self.name = name
        self.data = data

    #ANCHOR SET PARAM
    def set_parameter(self, parameter, value):
        pass

    # SERVER > USER > [date, change, balance, note],
    #ANCHOR ADD ENTRY
    def addentry(self, ctx, user, amount_change, note=''):
        server = ctx.guild.id
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
    def getbalance(self, ctx, user, *flags):
        '''Returns current balance for user
        Flags:
        \'int\' - returns balance as integer'''
        server = ctx.guild.id
        try:
            if 'int' in flags:
                balance = int(self.data[server][user][-1][2])
            else:
                amount = str(self.data[server][user][-1][2])
                if 'prefix' in self.data:
                    balance = f'{self.data["prefix"]}{amount}'
                elif 'suffix' in self.data:
                    balance = f'{amount} {self.data["suffix"].capitalize()}'
                else:
                    balance = f'{amount} {self.name}'
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
            log.error(f'{self.name.capitalize()} ledger could not be saved to file!')
            return
    #ANCHOR GET HISTORY
    def gethistory(self, ctx, user, lines=5):
        '''Return a formatted history statement'''
        server = ctx.guild.id
        history = 'Date\t\tChange\tBal\tNote\n-------------------------------------\n'
        for i in range(1, int(lines) + 1):
            try:
                history = history + str(self.data[server][user][-i]) + '\n'
            except:
                break
        history = history.replace(', ',',\t').replace('\'', '').replace('[','').replace(']','')
        return history
    #ANCHOR TRANSFER
    def transfer(self, ctx, sender, recipients : list, amount, note):
        if int(amount) * len(recipients) <= self.getbalance(ctx, sender, 'int'):
            for r in recipients:
                try:
                    r_name = ctx.guild.get_member(r).nick
                except:
                    r_name = r

                try:
                    self.addentry(ctx, r, int(amount), f'Given by {sender}')
                    self.addentry(ctx, sender, -int(amount), f'Sent to {r_name}')
                except:
                    log.error('Could not transfer tokens!')
            return 'Funds successfully transferred'
        else:
            balance = self.getbalance(ctx, sender)
            return f'Insufficient funds, current balance is {balance}'
            #await client.send_message()
#!SECTION 
