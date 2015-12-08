# encoding=utf8
'''
Created on 9 Oct 2015

@author: jurica
'''
import pickle
from lxml import etree as ET, html
from lxml.html.clean import Cleaner
from mysqlUtilities import connectMySQL
import os
from pprint import pprint
from pickle import PicklingError
import urllib2
import traceback
from pprint import pprint
from time import gmtime, strftime

from TechDashAPI.util import utilities
from TechDashAPI.topicModeling import techDashTopicModel
from TechDashAPI.mysqlUtilities import connectMySQL

#===============================================================================
# from stanford_corenlp_pywrapper import CoreNLP
# from pprint import pprint
#===============================================================================
from itertools import groupby
from operator import itemgetter

#===============================================================================
# Wordseer CoreNLP libraries
#===============================================================================
import jsonrpclib
from simplejson import loads


class ContentExtractor(object):
    '''
    classdocs
    '''
    
    '''
    steps:
        get serialized json file
    '''
    @profile
    def __init__(self, domain, htmlFileURL, pwd, CoreNLPner='',spacyNER='', dbConnection = ''):
        '''
        Constructor
        '''
        self.__fileURL = htmlFileURL
        self.__domainDBkey = domain
        
        try:
            self.__XpathList = pickle.load(open(pwd+'/xpathModels/'+str(self.__domainDBkey)+'.pickle', 'rb'))
            #===================================================================
            # self.__XpathListID = pickle.load(open('/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'+str(self.__domainDBkey)+'_ID.pickle', 'rb'))
            # self.__XpathListNoAttrib = pickle.load(open('/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'+str(self.__domainDBkey)+'_NoAttrib.pickle', 'rb'))
            #===================================================================
        except PicklingError, e:
            print e
        
        self.__htmlElements = ['body','header','nav','footer','article','section','aside', 'div', 'span']
        self.__htmlAttributes = ['id','class']
        self.__documentIDKey = ''
        self.__utilitiesFunctions = utilities()
        
        #DB CONNECTIVITY AND FUNCTIONALITY
        self.__db = connectMySQL(db='xpath', port=3366)
        self.__topicModel = techDashTopicModel(destination=pwd+'/modelsLDA/', fileName='fullModel', modelName='fullModel_100P_20T')
        
        #=======================================================================
        # OPEN URL
        #=======================================================================
        url2Open, self.__htmlFile = self.__utilitiesFunctions.openULR(self.__fileURL)
        
        #=======================================================================
        # NER 
        #=======================================================================
        self.__extractNerStanford = CoreNLPner
        self.__extractNerSpacy = spacyNER

    def getDocumentIDKey(self):
        '''
        Check if document already analyzed
        '''

        sqlQuery = 'select documentID from document where documentURL="%s"' %(self.__fileURL)
        #=======================================================================
        # print self.__db
        #=======================================================================
        self.__db.executeQuery(sqlQuery)

        if len(self.__db._connectMySQL__results) > 0:
            print "Document %s has already been analyzed and in the database!"%(self.__fileURL)
            self.__documentIDKey = None
        else:
            sqlQuery = 'insert into document (documentDomainListID,documentURL) values("%s","%s")'%(self.__domainDBkey, self.__fileURL)
            self.__db.executeQuery(sqlQuery)
            self.__db._connectMySQL__connection.commit()
            self.__documentIDKey = self.__db._connectMySQL__cursor.lastrowid
            
    
    #===========================================================================
    # EXTRACT NER 
    #===========================================================================
            
    def checkNeighbour(self, indexList, entityList):
        
        #===========================================================================
        # print indexList
        # print entityList
        #===========================================================================
        entities = []
        
        for k, g in groupby(enumerate(indexList), lambda (i, x): i-x):
                                                                         
            consecutive = map(itemgetter(1), g)        
            consecutiveValues = ' '.join([entityList[conInd].strip('"').strip("'") for conInd in  consecutive ])
            entities.append(consecutiveValues)
     
        return entities
    
    
    def extractNER(self, text):
        #=======================================================================
        # https://github.com/brendano/stanford_corenlp_pywrapper
        #=======================================================================
        
        data = self.__extractNerStanford.parse_doc(text)
        
        peopleEntitiesList = []
        
        for item in data['sentences']:
            #===========================================================================
            # for key in item.keys():
            #===========================================================================
            try:
                
                nerIndex = [i for i, x in enumerate(item['ner']) if x == u'PERSON' or x == u'ORGANIZATION']
                
                if len(nerIndex)> 0:
                    try:
                        peopleEntitiesList.extend(self.checkNeighbour(nerIndex,item['tokens']))
                    except AttributeError:
                        print traceback.print_exc()
                        pass
    
            except ValueError:
                print traceback.print_exc()
                pass
        
        if len(peopleEntitiesList) > 0:
            nerEntities = ",".join(list(set(peopleEntitiesList)))
        else:
            nerEntities = ''
            
        nerEntities = nerEntities.replace("'","\'")
        return nerEntities.encode('utf-8')

    def extractNER_Wordseer(self, text):
        #=======================================================================
        # https://github.com/Wordseer/stanford-corenlp-python
        #=======================================================================
        print 'in wordseer'
        server = jsonrpclib.Server("http://localhost:1111")
        result = loads(server.parse(text))
        print result.keys()
        #=======================================================================
        # 
        # for item in result['sentences']:
        #     print item
        #=======================================================================
            
        raw_input('prompt')
    
    @profile
    def extractNER_Spacy(self, text):
        
        returnNERTypes =['PERSON','ORG','WORK_OF_ART','PRODUCT']
        doc = self.__extractNerSpacy(text.decode('utf-8'))
        nerEntities = [str(ent).strip('"').strip("'") for ent in doc.ents if ent.label_ in returnNERTypes]

        
        if len(nerEntities) > 0:
            nerEntities = ",".join(list(set(nerEntities)))
        else:
            nerEntities = ''

        print nerEntities
        return nerEntities

    #===========================================================================
    # EXTRACT AND WRITE CONTENT TO DB
    #===========================================================================
    @profile
    def extractContent(self):

        if self.__documentIDKey is not None:
            
            itemChildrenText = ''
            extractedContent = []
            #===================================================================
            # pathStatistics = self.__utilitiesFunctions.getDomainStatistics(self.__domainDBkey)
            #===================================================================
            articleTitle = self.__htmlFile.find(".//title").text.encode('utf-8')
            extracted = False
            articleLength = -1
            articlePath = ''
            
            for path in self.__XpathList:

                path = path.replace('"',"'")
                itemChildrenText = list(set(self.__utilitiesFunctions.extractContentBS(path, self.__htmlFile)))
                #===============================================================
                # print itemChildrenText
                #===============================================================

                for elementChildText in itemChildrenText:
                    elementChildText = elementChildText.encode('utf-8','replace')
                    elementChildText = elementChildText.replace('"',"'")
                    #===========================================================
                    # print path,'\t', len(elementChildText),'\t',elementChildText
                    #===========================================================
                    
                    if len(elementChildText)  > articleLength:
                        extractedContent = elementChildText
                        articlePath = path
                        extracted = True
                        articleLength = len(elementChildText)
            
            if extracted:
                NERs = self.extractNER_Spacy(extractedContent)
                topicModel = self.__topicModel.getDocumentTopics(extractedContent)
                sqlQuery = '''INSERT INTO xpathValuesXPath (xpathValuesXPath, xpathValuesContent, xpathValuesdocumentID, xpathValuesXPathType, xpathValuesXPathContentLength,xpathValuesXPathMainTopic, xpathValuesXPathTitle,xpathValuesXPathNER) 
                VALUES ("%s","%s","%s","%s","%s","%s","%s","%s")'''%(articlePath,extractedContent,self.__documentIDKey,'Attribs',len(extractedContent),topicModel,articleTitle,NERs)
                self.__db.executeQuery(sqlQuery)
                self.__db._connectMySQL__connection.commit()
                #===============================================================
                # print 'EXTRACTED\t', articlePath,'\t', extractedContent,'\t',len(extractedContent), NERs
                #===============================================================
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()), ', PROCESSED : Extracted content from %s \n =======================' %(self.__fileURL)
            else:
                print strftime("%Y-%m-%d %H:%M:%S", gmtime()), ', NOT PROCESSED : NO content from %s extracted \n =======================' %(self.__fileURL)