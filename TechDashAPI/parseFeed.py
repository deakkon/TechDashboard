'''
Created on 7 Sep 2015

@author: jurica
'''
import feedparser
from datetime import datetime 
from urlparse import urlparse #domain extraction
import sys
from TechDashAPI.mysqlUtilities import connectMySQL
from TechDashAPI.ContentExtractor import ContentExtractor
from TechDashAPI.ContentExtractorTrainer import ContentExtractorTrainer
from TechDashAPI.createDOM import createDom
from TechDashAPI.util import utilities

from pprint import pprint
import os
import json
import dicttoxml
import traceback



class parseNewsFeed(object):
    __feedURL = None
    __parsedFeed = None
    __entries = None
    __etags = None
    
    def __init__(self, feedURL= ''):
        if feedURL == '':
            self.__feedURL = [
                'http://feeds.reuters.com/reuters/technologyNews?format=xml',
                'http://feeds.reuters.com/reuters/scienceNews',
                'http://www.cnet.com/rss/all/',
                'http://feeds.feedburner.com/TechCrunch/',
                'http://www.wired.com/category/gear/feed/',
                'http://www.wired.com/category/science/feed/',
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'http://www.infoworld.com/index.rss'
            ]
        else:
            self.__feedURL=feedURL

        if isinstance(self.__feedURL, list):
            self.__etags = {}
            for item in self.__feedURL:
                #===============================================================
                # print item
                #===============================================================
                self.__etags[item] = {
                    #item : {
                        'etag' : None,
                        'modified': None,
                        'feed' : None,
                        'changed' : False
                        #}
                    }
        else:
            self.__etags = {
                    self.__feedURL : {
                    'etag' : None,
                    'modified': None,
                    'feed' : None,
                    'changed' : False
                    }
            }

        self.__articleLinks = []
        self.__domainDBkey = None
        self.__db = connectMySQL(db='xpath', port=3366)
        self.__filesFolder = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'
        self.__utilitiesFunctions = utilities()
            
    def getDomainKey(self, url):
        '''
        Check if at least one document from domain was already analyzed! 
        '''
        parsed_uri = urlparse(url)
        self.__domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        
        sqlQuery = 'select domainListID from domainList where domainName="%s"' %(self.__domain)
        #sqlQuery = 'select domainListID from domainList'
        self.__db.executeQuery(sqlQuery)
        #print self.__db._connectMySQL__results
        if len(self.__db._connectMySQL__results) == 1:
            print "Analyzing existing domain %s!"%(self.__domain)
            results = self.__db._connectMySQL__results
            self.__domainDBkey = results[0][0]
        elif len(self.__db._connectMySQL__results) > 1:
            print "Something is wrong in the domain -> DB Key mapping"
            sys.exit(0)
        else:
            print 'Adding new domain %s to database' %(self.__domain)
            sqlQuery = 'insert into domainList (domainName) values("%s")'%(self.__domain)
            self.__db.executeQuery(sqlQuery)
            self.__db._connectMySQL__connection.commit()
            self.__domainDBkey = self.__db._connectMySQL__cursor.lastrowid
    
    def checkFeedUpdate(self, feedUrl='', etag='', modified=''):
        #=======================================================================
        # Check if the feed has been updated since last check
        #=======================================================================

        for keys in self.__etags:
            self.__etags[keys]['feed'] = feedparser.parse(keys, etag=self.__etags[keys]['etag'],modified=self.__etags[keys]['modified'])
            
            if self.__etags[keys]['feed'].status == 304:
                print datetime.now(),'Feed %s did not change since last attempt. Be patient.' %(keys)
                self.__etags[keys]['changed'] = False
            else:
                print datetime.now(),'Feed %s changed since last attempt. New content to extract.' %(keys)
                try:
                    self.__etags[keys]['etag'] = self.__etags[keys]['feed'].etag
                except AttributeError:
                    self.__etags[keys]['etag'] = ''
                    
                try:
                    self.__etags[keys]['modified'] = self.__etags[keys]['feed'].modified
                except AttributeError:
                    self.__etags[keys]['modified'] = ''
                    
                self.__etags[keys]['changed'] = True
            
        print '############################'
    
        
    def processArticles(self, listOfURLs):
        for url in listOfURLs:
            rd = createDom(url=url)
            rd.readDOMrecursive()

            pickleFilePath = self.__filesFolder+str(self.__domainDBkey)
            
            if os.path.isfile(pickleFilePath+'.json'):
                xpathValues = json.load(open(pickleFilePath+'.json', 'rb'))
                z = xpathValues.copy()
                z.update(rd._createDom__domDict)
                xml = dicttoxml.dicttoxml(z)
                f= open(pickleFilePath+'.xml', 'wb')
                f.write(xml)
                f.close()
                json.dump(z, open(pickleFilePath+'.json', 'wb'))

            else:
                json.dump(rd._createDom__domDict, open(pickleFilePath+'.json', 'wb'))
                xml = dicttoxml.dicttoxml(self.__domainDBkey)
                f= open(pickleFilePath+'.xml', 'wb')
                f.write(xml)
                f.close()
                
    def trainArticles(self, listOfURLs, domain):
        
        for url in listOfURLs: 
            cet = ContentExtractorTrainer(domain,url)
            cet.createXPathFromXMLFile()
            cet.evaluateXPathNodeContent()
            #===================================================================
            # cet.evaluateXPathNodeContentID()
            # cet.evaluateXPathNodeContentNoAttrib()
            #===================================================================
        
    def printFeedItems(self, key=''):
        for key in self.__etags.keys():
            self.__articleLinks = []
            self.getDomainKey(key) 

            if self.__etags[key]['changed']:
                
                feedEntry = self.__etags[key]['feed']
                
                for item in feedEntry['entries']:
                    #===========================================================
                    # CHECK IF IF 
                    #===========================================================
                    self.__articleLinks.append(item['link'])
                    
                if not os.path.exists(self.__filesFolder+str(self.__domainDBkey)+'.pickle'):
                    print 'Start new thread and train on new domain'
                    #===================================================================
                    # thread.start_new_thread(processArticles(articles),'trainModel' )
                    #===================================================================
                    self.processArticles(self.__articleLinks)
                    self.trainArticles(self.__articleLinks, self.__domainDBkey)

                for article in self.__articleLinks:
                    try:
                        ce = ContentExtractor(self.__domainDBkey,article)
                        ce.getDocumentIDKey()
                        ce.extractContent()
                        #=======================================================
                        # ce.extractContentID()
                        # ce.extractContentNoAttrib()
                        #=======================================================
                    except AttributeError:
                        print traceback.print_exc()
                        pass
                    