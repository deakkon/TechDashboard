'''
Created on 7 Sep 2015

@author: jurica
'''

#===============================================================================
# MY STUFF
#===============================================================================
from TechDashAPI.mysqlUtilities import connectMySQL
from TechDashAPI.ContentExtractor import ContentExtractor
from TechDashAPI.ContentExtractorTrainer import ContentExtractorTrainer
from TechDashAPI.createDOM import createDom
from TechDashAPI.util import utilities

#===============================================================================
# VARIOUS STUFF
#===============================================================================
import os
import json
import dicttoxml
import traceback
import feedparser
from datetime import datetime 
from urlparse import urlparse #domain extraction
import sys


#===============================================================================
# NER STUFF
#===============================================================================
from stanford_corenlp_pywrapper import CoreNLP

class parseNewsFeed(object):
    __feedURL = None
    __parsedFeed = None
    __entries = None
    __etags = None
    
    def __init__(self, feedURL= ''):
        
        #=======================================================================
        # https://news.ycombinator.com/rss
        # http://skimfeed.com/tech.html
        # https://gcn.com/rss-feeds/all.aspx',
        #=======================================================================
                
        if feedURL == '':
            self.__feedURL = [
                'http://feeds.reuters.com/reuters/technologyNews?format=xml',
                'http://feeds.reuters.com/reuters/scienceNews',
                'http://www.cnet.com/rss/all/',
                'http://www.wired.com/category/gear/feed/',
                'http://www.wired.com/category/science/feed/',
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'http://www.infoworld.com/index.rss',
                'http://feeds.news.com.au/public/rss/2.0/news_tech_506.xml',
                'http://www.pcworld.com/index.rss',
                'http://www.computerworld.com/index.rss',
                'http://feeds.arstechnica.com/arstechnica/index?format=xml',
                'http://www.networkcomputing.com/rss_simple.asp',
                'http://feeds2.feedburner.com/ziffdavis/pcmag/breakingnews',
                'http://www.engadget.com/rss-full.xml',
                'http://www.digitaltrends.com/feed/',
                'http://www.pcworld.com/index.rss',
                'http://www.independent.co.uk/life-style/gadgets-and-tech/rss',
                'http://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
                'http://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
                'http://feeds.feedburner.com/Technibble',
                'http://feeds.feedburner.com/TechCrunch/',
                'http://feeds.feedburner.com/techradar/allnews'
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
        
        #=======================================================================
        # STANFORD NER 
        #=======================================================================
        self.__extractNerStanford = CoreNLP( "nerparse",corenlp_jars=["/Users/jurica/Downloads/stanford-corenlp-full-2015-04-20/*"])
            
    def getDomainKey(self, url):
        '''
        Check if at least one document from domain was already analyzed! 
        '''
        parsed_uri = urlparse(url)
        
        if '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri) == 'http://feeds.feedburner.com/':
            self.__domain = '{uri.scheme}://{uri.netloc}{uri.path}'.format(uri=parsed_uri)
        else:
            self.__domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            
        sqlQuery = 'select domainListID from domainList where domainName="%s"' %(self.__domain)
        #sqlQuery = 'select domainListID from domainList'
        self.__db.executeQuery(sqlQuery)
        #print self.__db._connectMySQL__results
        if len(self.__db._connectMySQL__results) == 1:
            #===================================================================
            # print "Analyzing existing domain %s!"%(self.__domain)
            #===================================================================
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
            try:
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
            except AttributeError:
                self.__etags[keys]['changed'] = False
            
        print '############################'
    
        
    def processArticles(self, listOfURLs):

        for url in listOfURLs:
            print 'Processing ', url
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
            print 'Training on ',url
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
                    # CHECK IF ARTICLE ALREADY IN DATABASE
                    #===========================================================
                    if self.__utilitiesFunctions.checkProcessedArticle(item['link']):
                        self.__articleLinks.append(item['link'])
                    
                if not os.path.exists(self.__filesFolder+str(self.__domainDBkey)+'.pickle') or self.__utilitiesFunctions.checkNumberOfProcessedArticle(self.__domainDBkey) < 200:
                    print 'Training on domain %s' %(self.__domainDBkey)
                    self.processArticles(self.__articleLinks)
                    self.trainArticles(self.__articleLinks, self.__domainDBkey)

                for article in self.__articleLinks:
                    try:
                        print article
                        ce = ContentExtractor(self.__domainDBkey,article, self.__extractNerStanford)
                        ce.getDocumentIDKey()
                        ce.extractContent()
                        #=======================================================
                        # ce.extractContentID()
                        # ce.extractContentNoAttrib()
                        #=======================================================
                    except AttributeError:
                        print traceback.print_exc()
                        pass
            
            
