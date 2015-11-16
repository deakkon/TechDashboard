'''
Created on 8 Sep 2015

@author: jurica
'''
from TechDashAPI.parseFeed import *
from TechDashAPI.ContentExtractor import *
from TechDashAPI.createDOM import *
from TechDashAPI import ContentExtractorTrainer

#from TechDashAPI.repeater import *

from time import sleep

if __name__ == '__main__':
    print "starting..."
    gn = parseNewsFeed()
    while True:
        gn.checkFeedUpdate()
        gn.printFeedItems()
        print 'Waiting for 100 second for a new try.'
        sleep(100)