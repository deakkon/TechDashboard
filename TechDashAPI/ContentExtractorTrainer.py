# encoding=utf8
'''
Created on 9 Oct 2015

@author: jurica
'''

from pprint import pprint
import sys, os
from lxml import etree as ET, html
import json
import Levenshtein
import pickle
from sklearn.cluster import *
import numpy
import traceback
from docutils.frontend import Values
from TechDashAPI.util import utilities
import urllib2
import logging

class ContentExtractorTrainer(object):
    '''
    classdocs
    //*[contains(@class,'wrap footer-links')]
    */body/div[contains(@id, 'content')][contains(@class,'container group')]
    'http://feeds.reuters.com/~r/reuters/technologyNews/~3/5nOmNuWjRts/story01.htm'
    
    http://lxml.de/api/lxml.html.clean.Cleaner-class.html - LXML CLEANING OPTIONS FOR FURTHER PREPROCESSING
    '''
    @profile
    def __init__(self, domain, htmlFileURL, dbConnection='', path=''):
        #=======================================================================
        # LOGGING INFORMATION
        #=======================================================================s
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        
        #=======================================================================
        # INITIAL VARIABLES
        #=======================================================================
        self.__domain = str(domain)
        self.__htmlFileURL = htmlFileURL
        self.__xpathPaths = []
        #=======================================================================
        # self.__xpathPathsNoAttrib = []
        #=======================================================================
        #=======================================================================
        # self.__xpathPathsID = []
        #=======================================================================
        
        #=======================================================================
        # SET UP THE DIRECTORY STRUCTURE; WHERE THE FILES ARE/WILL BE STORED
        #=======================================================================
        self.__dictionaryPath = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'
        self.__domainResourcesFile = self.__dictionaryPath + self.__domain
        
        #=======================================================================
        # DICTIONARY WITH KNOWLEDGE INFORMATION, only need when using 2-step xpath list creation, DEPRECATED
        #=======================================================================
        
        #=======================================================================
        # self.__domainDoctionary = json.load(open(self.__domainResourcesFile + '.json', 'rb'))
        # self.__domainDoctionaryXML = ET.parse(self.__domainResourcesFile + '.xml')
        #=======================================================================
        
        #=======================================================================
        # STRUCTURE AND CONTENT ELEMENTS FOR XPATH CREATION
        #=======================================================================
        self.__htmlElements = ['body', 'header', 'nav', 'footer', 'article', 'section', 'aside', 'div', 'span']
        self.__htmlAttributes = ['id', 'class']
        self.__htmlElementsSkip = ['script','style']
        
        #=======================================================================
        # LOAD BACKGROUND KNOWLEDGE
        #=======================================================================
        try:
        #=======================================================================
        # if os.path.isfile(self.__dictionaryPath + self.__domain + '_bckKnowledge.pickle'):
        #=======================================================================
            self.__htmlFileBackgroundKnowledge = pickle.load(open(self.__domainResourcesFile + '_bckKnowledge.pickle', 'rb'))
        except:
            self.__htmlFileBackgroundKnowledge = {}
            print traceback.print_exc()
            
        #=======================================================================
        # SET UP K-MEANS AND DEFINE CLUSTER CENTERS
        #=======================================================================
        try:
            #===================================================================
            # if os.path.isfile(self.__dictionaryPath + self.__domain + '_centroids.pickle'):
            #===================================================================
            centroids = pickle.load(open(self.__domainResourcesFile + '_centroids.pickle', 'rb'))
            self.__kMeansValues = KMeans(n_clusters=2, init=centroids)
        except:
            #===================================================================
            # print traceback.print_exc()
            #===================================================================
            self.__kMeansValues = KMeans(n_clusters=2)

        #=======================================================================
        # UTILITIES FUNCTION
        #=======================================================================
        self.__utilitiesFunctions = utilities()
        url2Open, self.__htmlFile = self.__utilitiesFunctions.openULR(self.__htmlFileURL)
        
    def createXPathFromXMLFile(self):
        '''
        load XML file created in createDOM
        get element, its children and build xpaths
        return created xpath (or for every xpath extract content of current file and compare with background knowledge)
        '''
        tempPaths = []
        for element in self.__domainDoctionaryXML.getiterator():
            if element.tag in self.__htmlElements:
                try:
                    parentNodesDummy = [ancestor for ancestor in element.iterancestors() if ancestor.tag in self.__htmlElements][::-1]
                    for parentElements in parentNodesDummy:
                        for child in parentElements.getchildren():
                            if child.tag == 'values':
                                for childElement in child:
                                    a = 0
                                    xPathValueTemp = ''
                                     
                                    for item in childElement:
                                        if a == 0:
                                            if item.text is not None:
                                                xPathValueTemp += "[contains(@class, '%s')]" % (item.text)
         
                                        if a == 1:
                                            if item.text is not None:
                                                xPathValueTemp += "[contains(@id, '%s')]" % (item.text)
 
                                        a += 1
 
                                    tempPaths.append('//*/'+parentElements.tag+xPathValueTemp)
                     
                except (ValueError, TypeError) as ve:
                    print ve
                    traceback.print_exc()
                    pass
        
        self.__xpathPaths = list(set(tempPaths))
        #=======================================================================
        # print self.__xpathPaths
        #=======================================================================
 
                     
    def createXPathFromXMLFile_FullPath(self):
        for element in self.__domainDoctionaryXML.getiterator():
            if element.tag in self.__htmlElements:
                try:
                    #===========================================================
                    # ALTERNATIVE VERSION
                    #===========================================================
                    parentNodes = [ancestor.tag for ancestor in element.iterancestors() if ancestor.tag in self.__htmlElements][::-1]
                    if len(parentNodes) > 0:
                        xPathValue = '//*/' + '/'.join(parentNodes) + '/' + element.tag
                    else:
                        xPathValue = '//*/' + element.tag
                         
                    childrenClassNodes = [(child.tag , child.text) for child in element.getchildren() if child.tag not in self.__htmlElements]
                    childrenIDNodes = [(child.tag , child.text) for child in element.getchildren() if child.tag not in self.__htmlElements]
                    childrenNodesInfo = [bla for bla in child.getchildren() for child in element.getchildren() if child.tag == 'values' and child.tag not in self.__htmlElements]
 
                    try:
                        for  child in childrenNodesInfo:
                            a = 0 
                            xPathValueTemp = xPathValue
                            xPathValueTempID = xPathValue
                             
                            for bla in child.getchildren():
                                if a == 0:
                                    if bla.text is not None:
                                        xPathValueTemp += "[contains(@class, '%s')]" % (bla.text)
 
                                if a == 1:
                                    if bla.text is not None:
                                        xPathValueTemp += "[contains(@id, '%s')]" % (bla.text)
                                        xPathValueTempID += "[contains(@id, '%s')]" % (bla.text)
                                         
                                a += 1
                                 
                                #=======================================================
                                # ADD DIFFERENT XPATH VALUES FOR EVALUATION
                                #=======================================================
                                self.__xpathPathsID.append(xPathValueTempID)
                                self.__xpathPaths.append(xPathValueTemp)
                                self.__xpathPathsNoAttrib.append(xPathValue)
                                 
                    except (IndexError, AttributeError, ValueError) as e:
                        print e
                        traceback.print_exc()
                        pass
                     
                except (ValueError, TypeError) as ve:
                    print ve
                    traceback.print_exc()
                    pass
         
        self.__xpathPaths = list(set(tempPaths))
        self.__xpathPathsID = list(set(self.__xpathPathsID))
        self.__xpathPathsNoAttrib = list(set(self.__xpathPathsNoAttrib))
    
    @profile
    def evaluateXPathNodeContent(self):
        '''
        compare content and backContent extracted from both resources xpath
        '''
        self.__xpathPaths = self.__utilitiesFunctions.extractXPaths_LXML(self.__domain, self.__htmlFileURL, self.__domainResourcesFile + '_candidates.pickle')
        
        try:
            for path in self.__xpathPaths:
                #===================================================================
                # GET BACKGROUND KNOWLEDEG AND CURRENT NODE
                #===================================================================
                if path in self.__htmlFileBackgroundKnowledge.keys():
                    nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledge[path]['content']
                else:
                    self.__htmlFileBackgroundKnowledge[path] = {}
                    self.__htmlFileBackgroundKnowledge[path]['content'] = ['empty']
                    self.__htmlFileBackgroundKnowledge[path]['ratioValues'] = numpy.array([])
                    self.__htmlFileBackgroundKnowledge[path]['extractCount'] = 0
                    nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledge[path]['content']
                
                #===================================================================
                # GET ACTIVE PAGE PATH NODE CONTENT
                #===================================================================
                itemChildrenTextFile = self.__utilitiesFunctions.extractContentBS(path, self.__htmlFile)

                #===================================================================
                # CALCULTE DISTANCE BETWEEN BACKGROUND KNOWLEDGE
                #===================================================================
                ratio = self.__utilitiesFunctions.calculateNormalizedRatio(itemChildrenTextFile, path, self.__htmlFileBackgroundKnowledge, nodeBackgroundKnowledge)
                self.__htmlFileBackgroundKnowledge[path]['ratio'] = ratio
                self.__htmlFileBackgroundKnowledge[path]['ratioValues'] = numpy.append(self.__htmlFileBackgroundKnowledge[path]['ratioValues'], ratio)

                #===============================================================
                # UPDATE BACKGROUND KNOWLEDGE - TO BE EXCHANGED WITH DATABASE CONTENT
                #===============================================================
                nodeBackgroundKnowledge.extend(itemChildrenTextFile)
                self.__htmlFileBackgroundKnowledge[path]['content'] = nodeBackgroundKnowledge
                
                with open(self.__dictionaryPath + self.__domain + '_xpathNodesRatio.csv', 'a') as file:
                    file.write(path + ';--;' + str(ratio) + '\n')
    
            #===================================================================
            # KMEANS CLUSTERING
            #===================================================================
            data = numpy.asarray([[self.__htmlFileBackgroundKnowledge[key]['ratio']] for key in self.__xpathPaths])
    
            self.__kMeansValues.fit(data, self.__xpathPaths)
            generatedClusters = self.__kMeansValues.predict(data)
    
            
            uniq_y = {ind: [] for ind in list(set(generatedClusters))} 
            for idx, el in enumerate(generatedClusters):
                uniq_y[el].append(int(idx))
    
            indexValues = uniq_y.values()
            paths2Extract = [self.__xpathPaths[i] for i in indexValues[numpy.argmax(self.__kMeansValues.cluster_centers_)]]
            
            for item in paths2Extract:
                self.__htmlFileBackgroundKnowledge[item]['extractCount']+=1
                    
    
            #===================================================================
            # PICKLE BACKGROUND KNOWLEDGE, CLUSTER CENTERS FOR FUTURE ITERATIONS AND LIST OF DYNAMIC PATHS
            #===================================================================
            pickle.dump(self.__htmlFileBackgroundKnowledge, open(self.__dictionaryPath + self.__domain + '_bckKnowledge.pickle', 'wb'))
            pickle.dump(self.__kMeansValues.cluster_centers_, open(self.__dictionaryPath + self.__domain + '_centroids.pickle', 'wb'))
            pickle.dump([self.__xpathPaths[i] for i in indexValues[numpy.argmax(self.__kMeansValues.cluster_centers_)]], open(self.__dictionaryPath + self.__domain + '.pickle', 'wb'))
            
            #===================================================================
            # self.__htmlFileURL
            # print generatedClusters
            # print self.__kMeansValues.cluster_centers_
            # print paths2Extract
            # print '***************************'
            #===================================================================
            
        except (ValueError,AttributeError,TypeError):
            traceback.print_exc()
            return False