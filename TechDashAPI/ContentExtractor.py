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

from TechDashAPI.util import utilities
from TechDashAPI.topicModeling import techDashTopicModel
from TechDashAPI.mysqlUtilities import connectMySQL

#===============================================================================
# from stanford_corenlp_pywrapper import CoreNLP
# from pprint import pprint
#===============================================================================
from itertools import groupby
from operator import itemgetter
from cgitb import text

class ContentExtractor(object):
    '''
    classdocs
    '''
    
    '''
    steps:
        get serialized json file
    '''

    def __init__(self, domain, htmlFileURL, nerExtractor, dbConnection = ''):
        '''
        Constructor
        '''
        self.__fileURL = htmlFileURL
        self.__domainDBkey = domain
        
        try:
            self.__XpathList = pickle.load(open('/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'+str(self.__domainDBkey)+'.pickle', 'rb'))
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
        self.__topicModel = techDashTopicModel(destination='/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/', fileName='initalModel', modelName='500P_20T')
        
        #=======================================================================
        # OPEN URL
        #=======================================================================
        self.__htmlFile = self.__utilitiesFunctions.openULR(self.__fileURL)
        
        #=======================================================================
        # NER 
        #=======================================================================
        self.__extractNerStanford = nerExtractor

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
            consecutiveValues = ' '.join([entityList[conInd] for conInd in  consecutive ])
            entities.append(consecutiveValues)
     
        return entities
    
    
    def extractNER(self, text):
        
        data = self.__extractNerStanford.parse_doc(text)
        
        nerEntities = []
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
                        peopleEntitiesList = []
                        print traceback.print_exc()
                        pass
    
            except ValueError:
                peopleEntitiesList = []
                print traceback.print_exc()
                pass
        
        if len(nerEntities) > 0:
            nerEntities = ",".join(list(set(peopleEntitiesList)))
        else:
            nerEntities = ''
            
        return nerEntities.encode('utf-8')
        
    #===========================================================================
    # EXTRACT AND WRITE CONTENT TO DB
    #===========================================================================
    def extractContent(self):

        if self.__documentIDKey is not None:
            
            itemChildrenText = ''
            extractedContent = []
            pathStatistics = self.__utilitiesFunctions.getDomainStatistics(self.__domainDBkey)
            articleTitle = self.__htmlFile.find(".//title").text.encode('utf-8')
            
            for path in self.__XpathList:

                path = path.replace('"',"'")
                itemChildrenText = list(set(self.__utilitiesFunctions.extractContentBS(path, self.__htmlFile)))
                #===============================================================
                # self.__utilitiesFunctions.extractContentBS(path, self.__htmlFile)
                #===============================================================

                for elementChildText in itemChildrenText:
                    #===========================================================
                    # print elementChildText
                    #===========================================================
                    elementChildText = elementChildText.encode('utf-8','replace')
                    elementChildText = elementChildText.replace('"',"'")
                    
                    if len(elementChildText) > pathStatistics[u'50%']:
                        print "EXTRACTED:\t", path, pathStatistics[u'50%'], len(elementChildText)

                        NERs = self.extractNER(elementChildText)

                        topicModel = self.__topicModel.getDocumentTopics(elementChildText, 'initalModel', '500P_20T')

                        sqlQuery = '''INSERT INTO xpathValuesXPath (xpathValuesXPath, xpathValuesContent, xpathValuesdocumentID, xpathValuesXPathType, xpathValuesXPathContentLength,xpathValuesXPathMainTopic, xpathValuesXPathTitle,xpathValuesXPathNER) 
                        VALUES ("%s","%s","%s","%s","%s","%s","%s","%s")'''%(path,elementChildText,self.__documentIDKey,'Attribs',len(elementChildText),topicModel,articleTitle,NERs)
                        self.__db.executeQuery(sqlQuery)
                        self.__db._connectMySQL__connection.commit()
                    #===========================================================
                    # else:
                    #     print 'NOT EXTRACTED: ', path, elementChildText
                    #===========================================================

            print 'PROCESSED : Extracted content from %s \n =======================' %(self.__fileURL)
            


#===============================================================================
#                 
#     def extractContentID(self):
# 
#         if self.__documentIDKey is not None:
#             #===================================================================
#             # print 'Adding document %s to PROCESSED list' %(self.__fileURL) 
#             #===================================================================      
#             for path in self.__XpathListID:
#                 
#                 xpathContent = self.__htmlFile.xpath(path)
#             
#                 if len(xpathContent) > 0:
#                     for item in xpathContent:
#                         itemChildren = [child.text.lstrip().rstrip() for child in item.getchildren() if child.tag not in self.__htmlElements and child.text is not None]
#         
#                     itemChildrenText = ' '.join(itemChildren).encode('utf-8')
#                     itemChildrenText = itemChildrenText.replace("'",'"')
#                     path = path.replace("'","\\'")
#                     
#                     #===========================================================
#                     # if len(itemChildrenText) > 10:
#                     #===========================================================
#                     sqlQuery = "INSERT INTO xpathValuesXPath (xpathValuesXPath, xpathValuesContent, xpathValuesdocumentID, xpathValuesXPathType) VALUES ('%s','%s','%s','%s')"%(path,itemChildrenText,self.__documentIDKey,'ID')
#                     #===================================================================
#                     # print sqlQuery
#                     #===================================================================
#                     self.__db.executeQuery(sqlQuery)
#                     self.__db._connectMySQL__connection.commit()
#             print 'Extracted content from %s to PROCESSED list' %(self.__fileURL) 
#    
#     def extractContentNoAttrib(self):
# 
#         if self.__documentIDKey is not None:
#             #===================================================================
#             # print 'Adding document %s to PROCESSED list' %(self.__fileURL) 
#             #===================================================================
#             xpathContentsAll = []
#             path = ''
#             itemChildrenText = ''
#             
#             for path in self.__XpathListNoAttrib:
# 
#                 xpathContent = self.__htmlFile.xpath(path)
#                 
#                 if len(xpathContent) > 0:
#                     for item in xpathContent:
#                         itemChildren = [child.text.lstrip().rstrip() for child in item.getchildren() if child.text is not None]
#         
#                     itemChildrenTextTemp = ' '.join([item.lstrip().rstrip() for item in itemChildren  if item.lstrip().rstrip()]).encode('utf-8')
#                     itemChildrenTextTemp = itemChildrenText.replace("'",'"')
#                     
#                     if len(itemChildrenTextTemp) > len(itemChildrenText):
#                         itemChildrenText = itemChildrenTextTemp
#                         path = path.replace("'","\\'")
#                     
#             #===========================================================
#             # if len(itemChildrenText) > 10:
#             #===========================================================
#             sqlQuery = "INSERT INTO xpathValuesXPath (xpathValuesXPath, xpathValuesContent, xpathValuesdocumentID, xpathValuesXPathType) VALUES ('%s','%s','%s', '%s')"%(path,itemChildrenText,self.__documentIDKey, 'NoAttrib')
#             #===================================================================
#             # print sqlQuery
#             #===================================================================
#             self.__db.executeQuery(sqlQuery)
#             self.__db._connectMySQL__connection.commit()
#             print 'Extracted content from %s to PROCESSED list' %(self.__fileURL) 
#===============================================================================
