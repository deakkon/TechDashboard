'''
Created on 8 Sep 2015

@author: jurica
'''
from TechDashAPI.parseFeed import parseNewsFeed
import logging
import os

#from TechDashAPI.repeater import *

from time import sleep

if __name__ == '__main__':
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    workingDirectroy = os.getcwd()
    
    print "starting..."
    gn = parseNewsFeed(workingDirectroy)
    while True:
        gn.checkFeedUpdate()
        gn.printFeedItems()
        print 'Waiting for 600 second for a new try.'
        sleep(600)