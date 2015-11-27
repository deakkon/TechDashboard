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
import sys
import urllib2

#===============================================================================
# NER STUFF
#===============================================================================
from stanford_corenlp_pywrapper import CoreNLP
from spacy.en import English, LOCAL_DATA_DIR

#===============================================================================
# memory profileing
#===============================================================================
import memory_profiler

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
                'http://feeds.news.com.au/public/rss/2.0/news_tech_506.xml',
                'http://www.cnet.com/rss/all/',
                'http://www.wired.com/category/gear/feed/',
                'http://www.wired.com/category/science/feed/',
                'http://www.infoworld.com/index.rss',
                'http://www.pcworld.com/index.rss',
                'http://www.computerworld.com/index.rss',
                'http://www.networkcomputing.com/rss_simple.asp',
                'http://www.engadget.com/rss-full.xml',
                'http://www.digitaltrends.com/feed/',
                'http://www.independent.co.uk/life-style/gadgets-and-tech/rss',
                'http://rss.nytimes.com/services/xml/rss/nyt/Technology.xml',
                'http://rss.nytimes.com/services/xml/rss/nyt/Science.xml',
                'http://feeds.reuters.com/reuters/technologyNews?format=xml',
                'http://feeds.reuters.com/reuters/scienceNews',
                'http://feeds.bbci.co.uk/news/technology/rss.xml',
                'http://feeds.feedburner.com/Technibble',
                'http://feeds.feedburner.com/TechCrunch/',
                'http://feeds.feedburner.com/techradar/allnews',
                'http://feeds.news.com.au/public/rss/2.0/news_tech_506.xml',
                'http://feeds.arstechnica.com/arstechnica/index?format=xml',
                'http://feeds2.feedburner.com/ziffdavis/pcmag/breakingnews'
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
        #=======================================================================
        # self.__extractNerStanford = CoreNLP( "nerparse",corenlp_jars=["/Users/jurica/Downloads/stanford-corenlp-full-2015-04-20/*"])
        #=======================================================================
        self.__spacyData_dir = os.environ.get('SPACY_DATA', LOCAL_DATA_DIR)
        self.__SpacyNLP = English(data_dir=self.__spacyData_dir)
        
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
    
    #===========================================================================
    # BASIC XPATH CREATION THROUGH CREATING THE DOM AND TRAINIGN ON IT
    #===========================================================================
    def processArticles(self, listOfURLs, domain):
        #=======================================================================
        # CREATE XPATH LIST FOR TRAINING
        #=======================================================================
        for url in listOfURLs:
            print 'Processing ', url
            rd = createDom(url=url)
            rd.readDOMrecursive()
            
            pickleFilePath = self.__filesFolder+str(domain)
            
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
                xml = dicttoxml.dicttoxml(rd._createDom__domDict)
                f= open(pickleFilePath+'.xml', 'wb')
                f.write(xml)
                f.close()
    #@profile            
    def trainArticles(self, listOfURLs, domain):
        
        for url in listOfURLs: 
            #===================================================================
            # print 'Training on domain ', domain,'\t Looking @ ', url
            #===================================================================
            cet = ContentExtractorTrainer(domain,url)
            #===================================================================
            # cet.createXPathFromXMLFile()
            #===================================================================
            cet.evaluateXPathNodeContent()
            
    #===========================================================================
    # TRAINING ON XPATH DERIVED FROM LXML.GETPATH()
    #     1-STEP PROCESS, LXML.GETPATH GET ALL XPATHS FROM AN URL
    #    TRAIN ON THE XPATHS
    #    CREATE PICKLE FILE
    #===========================================================================

    #@profile
    def printFeedItems(self, key=''):
        
        for key in self.__etags.keys():

            if self.__etags[key]['changed']:
                
                feedEntry = self.__etags[key]['feed']
                articleDictionary = {}
                
                for item in feedEntry['entries']:
                    #===========================================================
                    # CHECK IF ARTICLE ALREADY IN DATABASE
                    #===========================================================
                    try:
                        url2Open = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(item['link']).geturl()
                        domain = str(self.__utilitiesFunctions.getDomainKey(url2Open))
                    except:
                        print traceback.print_exc()
                        print item['link']
                        return
                    
                    if domain not in articleDictionary:
                        articleDictionary[domain]=[]
                        
                    if self.__utilitiesFunctions.checkProcessedArticle(url2Open):
                        articleDictionary[domain].append(url2Open)
                    #===========================================================
                    # self.__articleLinks.append({'article':url2Open, 'domain':domain})
                    #===========================================================
                
                for key in articleDictionary:
                    
                    if len(articleDictionary[key]) > 0:
                        
                        if not os.path.exists(self.__filesFolder+str(key)+'.pickle') or self.__utilitiesFunctions.checkNumberOfProcessedArticle(key) < 50:
                            #===================================================
                            # print 'Training domain %s' %(key)
                            #===================================================
                            #===================================================
                            # self.processArticles(articleDictionary[key],key)
                            #===================================================
                            self.trainArticles(articleDictionary[key],key)

                        try:
                            #===================================================
                            # print 'Processing domain %s'%(key)
                            #===================================================
                            for article in articleDictionary[key]:
                                ce = ContentExtractor(key, article,spacyNER=self.__SpacyNLP)
                                ce.getDocumentIDKey()
                                ce.extractContent()

                        except AttributeError:
                            print traceback.print_exc()
                            pass
                        
                    else:
                        print 'No new articles to process on domain %s'%(domain)
                            

            
            
