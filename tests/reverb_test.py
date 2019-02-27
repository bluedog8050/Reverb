import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)
import discord
import unittest
from cogs.reverb import Reverb

class test_reverb_cog(unittest.TestCase):
    def setup(self):
        pass
    def teardown(self):
        pass

    def test_load_defaults(self):
        pass

    def test_forward_from_defualt(self):
        pass
        
    def test_insert_new_link(self):
        pass
        
    def test_forward_from_new_link(self):
        pass