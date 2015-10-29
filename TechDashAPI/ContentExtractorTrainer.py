# encoding=utf8

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
'''
Created on 9 Oct 2015

@author: jurica
'''

class ContentExtractorTrainer(object):
    '''
    classdocs
    //*[contains(@class,'wrap footer-links')]
    */body/div[contains(@id, 'content')][contains(@class,'container group')]
    'http://feeds.reuters.com/~r/reuters/technologyNews/~3/5nOmNuWjRts/story01.htm'
    
    http://lxml.de/api/lxml.html.clean.Cleaner-class.html - LXML CLEANING OPTIONS FOR FURTHER PREPROCESSING
    '''

    def __init__(self, domain, htmlFileURL):
        self.__domain = str(domain)
        self.__dictionaryPath = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'
        self.__domainDoctionary = json.load(open(self.__dictionaryPath + self.__domain + '.json', 'rb'))
        self.__domainDoctionaryXML = ET.parse(self.__dictionaryPath + self.__domain + '.xml')
        self.__htmlFileURL = htmlFileURL
        self.__xpathPaths = []
        self.__xpathPathsNoAttrib = []
        self.__xpathPathsID = []
        self.__htmlElements = ['body', 'header', 'nav', 'footer', 'article', 'section', 'aside', 'div', 'span']
        self.__htmlAttributes = ['id', 'class']
        self.__htmlElementsSkip = ['script']
        self.__utilitiesFunctions = utilities()
        
        #=======================================================================
        # LOAD BACKGROUND KNOWLEDGE
        #=======================================================================
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_bckKnowledge.pickle'):
            self.__htmlFileBackgroundKnowledge = pickle.load(open(self.__dictionaryPath + self.__domain + '_bckKnowledge.pickle', 'rb'))
        else:
            self.__htmlFileBackgroundKnowledge = {}
            
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_ID_bckKnowledge.pickle'):
            self.__htmlFileBackgroundKnowledgeID = pickle.load(open(self.__dictionaryPath + self.__domain + '_ID_bckKnowledge.pickle', 'rb'))
        else:
            self.__htmlFileBackgroundKnowledgeID = {}
            
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_ID_bckKnowledge.pickle'):
            self.__htmlFileBackgroundKnowledge_NoAttrib = pickle.load(open(self.__dictionaryPath + self.__domain + '_NoAttrib_bckKnowledge.pickle', 'rb'))
        else:
            self.__htmlFileBackgroundKnowledge_NoAttrib = {}
            
        #=======================================================================
        # SET UP KMEANS AND DEFINE CLUSTER CENTERS
        #=======================================================================
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_centroids.pickle'):
            centroids = pickle.load(open(self.__dictionaryPath + self.__domain + '_centroids.pickle', 'rb'))
            self.__kMeansValues = KMeans(n_clusters=2, init=centroids)
        else:
            self.__kMeansValues = KMeans(n_clusters=2)
            
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_ID_centroids.pickle'):
            centroids = pickle.load(open(self.__dictionaryPath + self.__domain + '_ID_centroids.pickle', 'rb'))
            self.__kMeansValues_ID = KMeans(n_clusters=2, init=centroids)
        else:
            self.__kMeansValues_ID = KMeans(n_clusters=2)
            
        if os.path.isfile(self.__dictionaryPath + self.__domain + '_NoAttrib_centroids.pickle'):
            centroids = pickle.load(open(self.__dictionaryPath + self.__domain + '_NoAttrib_centroids.pickle', 'rb'))
            self.__kMeansValues_NoAttrib = KMeans(n_clusters=2, init=centroids)
        else:
            self.__kMeansValues_NoAttrib = KMeans(n_clusters=2)
            
        try:
            print self.__htmlFileURL
            self.__htmlFile = html.parse(self.__htmlFileURL)
        except IOError:
            print ('Error opening the url')
            print traceback.print_exc()
            return
        
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
        #=======================================================================
        # self.__xpathPathsID = list(set(self.__xpathPathsID))
        # self.__xpathPathsNoAttrib = list(set(self.__xpathPathsNoAttrib))
        #=======================================================================

    def evaluateXPathNodeContent(self):
        '''
        compare content and backContent extracted from both resources xpath
        '''

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
            itemChildrenTextFile = self.__utilitiesFunctions.extractContent(path, self.__htmlFile)

            #===================================================================
            # CALCULTE DISTANCE BETWEEN BACKGROUND KNOWLEDGE
            #===================================================================
            ratio = self.__utilitiesFunctions.calculateRatio(itemChildrenTextFile, path, self.__htmlFileBackgroundKnowledge, nodeBackgroundKnowledge)

            #===================================================================
            # CREATE NODES IN THE DICT WITH CONTENT AND RATIO INFORMATION
            # MINIMUM RATIO VS AVERAGE RATIO
            # NORMALIZING VALUE OF NUMBER OF PATH IDENTIFICATIONS AS EXTRACTED PATHS
            #===================================================================
            
            self.__htmlFileBackgroundKnowledge[path]['ratio'] = ratio
            self.__htmlFileBackgroundKnowledge[path]['ratioValues'] = numpy.append(self.__htmlFileBackgroundKnowledge[path]['ratioValues'], ratio)
                        
            #===================================================================
            # if (numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) - numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])
            #     < ratio 
            #     < numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) + numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])):
            #===================================================================
            nodeBackgroundKnowledge.extend(itemChildrenTextFile)
            nodeBackgroundKnowledge = list(set(nodeBackgroundKnowledge))
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
        #=======================================================================
        # pickle.dump([self.__xpathPaths[i] for i in indexValues[numpy.argmax(self.__kMeansValues.cluster_centers_)]], open(self.__dictionaryPath + self.__domain + '.pickle', 'wb'))
        #=======================================================================
        
        self.__htmlFileURL
        print generatedClusters
        print self.__kMeansValues.cluster_centers_
        print paths2Extract
        print '***************************'
        
#===============================================================================
# 
#     def evaluateXPathNodeContentID(self):
#         '''
#         compare content and backContent extracted from both resources xpath
#         '''
#         for path in self.__xpathPathsID:
#             #===================================================================
#             # GET BACKGROUND KNOWLEDEG AND CURRENT NODE
#             #===================================================================
#             if path in self.__htmlFileBackgroundKnowledgeID.keys():
#                 nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledgeID[path]['content']
#             else:
#                 self.__htmlFileBackgroundKnowledgeID[path] = {}
#                 self.__htmlFileBackgroundKnowledgeID[path]['content'] = ['empty']
#                 self.__htmlFileBackgroundKnowledgeID[path]['ratioValues'] = numpy.array([])
#                 nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledgeID[path]['content']
# 
#             #===================================================================
#             # GET ACTIVE PAGE PATH NODE CONTENT
#             #===================================================================
#             try:
#                 xpathContentFile = self.__htmlFile.xpath(path)
#             except AttributeError:
#                 print traceback.print_exc()
#                 return
# 
#             for item in xpathContentFile:
#                 itemChildrenFile = [child.text.lstrip().rstrip() for child in item.getchildren() if child.tag not in self.__htmlElements and child.text is not None]
# 
#             try:
#                 itemChildrenTextFile = ' '.join(itemChildrenFile).encode('utf-8')
#                 itemChildrenTextFile = ' '.join(itemChildrenTextFile.split())
#                 if len(itemChildrenTextFile) == 0:
#                     itemChildrenTextFile = 'empty'
#             except UnboundLocalError:
#                 print traceback.print_exc()
#                 itemChildrenTextFile = 'empty'
#                 
#             #===================================================================
#             # CALCULTE DISTANCE BETWEEN BACKGROUND KNOWLEDGE
#             #===================================================================
#             
#             ratio = min([(Levenshtein.distance(item, itemChildrenTextFile) * (2 / (len(item) + len(itemChildrenTextFile))))] for item in nodeBackgroundKnowledge)
#             
#             #===================================================================
#             # CREATE NODES IN THE DICT WITH CONTENT AND RATIO INFORMATION
#             #===================================================================
#             self.__htmlFileBackgroundKnowledgeID[path]['ratio'] = ratio[0]
#             self.__htmlFileBackgroundKnowledgeID[path]['ratioValues'] = numpy.append(self.__htmlFileBackgroundKnowledgeID[path]['ratioValues'], ratio[0])
#             #===================================================================
#             # if (numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) - numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])
#             #     < ratio 
#             #     < numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) + numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])):
#             #===================================================================
#             nodeBackgroundKnowledge.append(itemChildrenTextFile)
#             nodeBackgroundKnowledge = list(set(nodeBackgroundKnowledge))
#             self.__htmlFileBackgroundKnowledgeID[path]['content'] = nodeBackgroundKnowledge
#             
# 
#             with open(self.__dictionaryPath + self.__domain + '_ID_xpathNodesRatio.csv', 'a') as file:
#                 file.write(path + ';--;' + str(ratio) + '\n')
# 
#         #===================================================================
#         # KMEANS CLUSTERING
#         #===================================================================
#         data = numpy.asarray([[self.__htmlFileBackgroundKnowledgeID[key]['ratio']] for key in self.__htmlFileBackgroundKnowledgeID.keys()])
#         self.__kMeansValues_ID.fit(data, self.__htmlFileBackgroundKnowledgeID.keys())
#         generatedClusters = self.__kMeansValues_ID.predict(data)
#         
#         #=======================================================================
#         # print 'Generated clusters: ',generatedClusters, len(generatedClusters)
#         # print 'Cluster centers: ', self.__kMeansValues.cluster_centers_
#         # print 'Labels: ', self.__kMeansValues.labels_
#         # print "Max index",  numpy.argmax(self.__kMeansValues.cluster_centers_)
#         #=======================================================================
# 
#         uniq_y = {ind: [] for ind in list(set(generatedClusters))} 
#         for idx, el in enumerate(generatedClusters):
#             uniq_y[el].append(int(idx))
# 
#         indexValues = uniq_y.values()
# 
#         print 'Not in xPaths', [self.__htmlFileBackgroundKnowledgeID.keys()[i] for i in indexValues[numpy.argmin(self.__kMeansValues_ID.cluster_centers_)]]#, [data[i] for i in uniq_y.keys()[1]]
#         print 'Xpath cluster',[self.__htmlFileBackgroundKnowledgeID.keys()[i] for i in indexValues[numpy.argmax(self.__kMeansValues_ID.cluster_centers_)]]
#         print self.__domain
#         
#         #===================================================================
#         # PICKLE BACKGROUND KNOWLEDGE, CLUSTER CENTERS FOR FUTURE ITERATIONS AND LIST OF DYNAMIC PATHS
#         #===================================================================
#         pickle.dump(self.__htmlFileBackgroundKnowledgeID, open(self.__dictionaryPath + self.__domain + '_ID_bckKnowledge.pickle', 'wb'))
#         pickle.dump(self.__kMeansValues_ID.cluster_centers_, open(self.__dictionaryPath + self.__domain + '_ID_centroids.pickle', 'wb'))
#         pickle.dump([self.__htmlFileBackgroundKnowledgeID.keys()[i] for i in indexValues[numpy.argmax(self.__kMeansValues_ID.cluster_centers_)]], open(self.__dictionaryPath + self.__domain + '_ID.pickle', 'wb'))
# 
#     def evaluateXPathNodeContentNoAttrib(self):
#         '''
#         compare content and backContent extracted from both resources xpath
#         '''
# 
#         for path in self.__xpathPathsNoAttrib:
#             #===================================================================
#             # GET BACKGROUND KNOWLEDEG AND CURRENT NODE
#             #===================================================================
#             if path in self.__htmlFileBackgroundKnowledge_NoAttrib.keys():
#                 nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledge_NoAttrib[path]['content']
#             else:
#                 self.__htmlFileBackgroundKnowledge_NoAttrib[path] = {}
#                 self.__htmlFileBackgroundKnowledge_NoAttrib[path]['content'] = ['empty']
#                 self.__htmlFileBackgroundKnowledge_NoAttrib[path]['ratioValues'] = numpy.array([])
#                 nodeBackgroundKnowledge = self.__htmlFileBackgroundKnowledge_NoAttrib[path]['content']
# 
#             #===================================================================
#             # GET ACTIVE PAGE PATH NODE CONTENT
#             #===================================================================
#             try:
#                 xpathContentFile = self.__htmlFile.xpath(path)
#             except AttributeError:
#                 print traceback.print_exc()
#                 return
# 
#             for item in xpathContentFile:
#                 itemChildrenFile = [child.text.lstrip().rstrip() for child in item.getchildren() if child.tag not in self.__htmlElements and child.text is not None]
# 
#             try:
#                 itemChildrenTextFile = ' '.join(itemChildrenFile).encode('utf-8')
#                 itemChildrenTextFile = ' '.join(itemChildrenTextFile.split())
#                 if len(itemChildrenTextFile) == 0:
#                     itemChildrenTextFile = 'empty'
#             except UnboundLocalError:
#                 itemChildrenTextFile = 'empty'
#                 
#             #===================================================================
#             # CALCULTE DISTANCE BETWEEN BACKGROUND KNOWLEDGE
#             #===================================================================
#             
#             ratio = min([(Levenshtein.distance(item, itemChildrenTextFile) * (2 / (len(item) + len(itemChildrenTextFile))))] for item in nodeBackgroundKnowledge)
#             
#             #===================================================================
#             # CREATE NODES IN THE DICT WITH CONTENT AND RATIO INFORMATION
#             #===================================================================
#             self.__htmlFileBackgroundKnowledge_NoAttrib[path]['ratio'] = ratio[0]
#             self.__htmlFileBackgroundKnowledge_NoAttrib[path]['ratioValues'] = numpy.append(self.__htmlFileBackgroundKnowledge_NoAttrib[path]['ratioValues'], ratio[0])
#             #===================================================================
#             # if (numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) - numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])
#             #     < ratio 
#             #     < numpy.mean(self.__htmlFileBackgroundKnowledge[path]['ratioValues']) + numpy.std(self.__htmlFileBackgroundKnowledge[path]['ratioValues'])):
#             #===================================================================
#             nodeBackgroundKnowledge.append(itemChildrenTextFile)
#             nodeBackgroundKnowledge = list(set(nodeBackgroundKnowledge))
#             self.__htmlFileBackgroundKnowledge_NoAttrib[path]['content'] = nodeBackgroundKnowledge
#             
# 
#             with open(self.__dictionaryPath + self.__domain + '_NoAttrib_xpathNodesRatio.csv', 'a') as file:
#                 file.write(path + ';--;' + str(ratio) + '\n')
# 
#         #===================================================================
#         # KMEANS CLUSTERING
#         #===================================================================
#         data = numpy.asarray([[self.__htmlFileBackgroundKnowledge_NoAttrib[key]['ratio']] for key in self.__htmlFileBackgroundKnowledge_NoAttrib.keys()])
#         self.__kMeansValues_NoAttrib.fit(data, self.__htmlFileBackgroundKnowledge_NoAttrib.keys())
#         generatedClusters = self.__kMeansValues_NoAttrib.predict(data)
#         
#         #=======================================================================
#         # print 'Generated clusters: ',generatedClusters, len(generatedClusters)
#         # print 'Cluster centers: ', self.__kMeansValues.cluster_centers_
#         # print 'Labels: ', self.__kMeansValues.labels_
#         # print "Max index",  numpy.argmax(self.__kMeansValues.cluster_centers_)
#         #=======================================================================
# 
#         uniq_y = {ind: [] for ind in list(set(generatedClusters))} 
#         for idx, el in enumerate(generatedClusters):
#             uniq_y[el].append(int(idx))
# 
#         indexValues = uniq_y.values()
# 
#         print 'not in xPath: ', [self.__htmlFileBackgroundKnowledge_NoAttrib.keys()[i] for i in indexValues[numpy.argmin(self.__kMeansValues_NoAttrib.cluster_centers_)]]#, [data[i] for i in uniq_y.keys()[1]]
#         print 'Xpath cluster:',[self.__htmlFileBackgroundKnowledge_NoAttrib.keys()[i] for i in indexValues[numpy.argmax(self.__kMeansValues_NoAttrib.cluster_centers_)]]
#         print self.__domain
#         
#         #===================================================================
#         # PICKLE BACKGROUND KNOWLEDGE, CLUSTER CENTERS FOR FUTURE ITERATIONS AND LIST OF DYNAMIC PATHS
#         #===================================================================
#         pickle.dump(self.__htmlFileBackgroundKnowledge_NoAttrib, open(self.__dictionaryPath + self.__domain + '_NoAttrib_bckKnowledge.pickle', 'wb'))
#         pickle.dump(self.__kMeansValues_NoAttrib.cluster_centers_, open(self.__dictionaryPath + self.__domain + '_NoAttrib_centroids.pickle', 'wb'))
#         pickle.dump([self.__htmlFileBackgroundKnowledge_NoAttrib.keys()[i] for i in indexValues[numpy.argmax(self.__kMeansValues_NoAttrib.cluster_centers_)]], open(self.__dictionaryPath + self.__domain + '_NoAttrib.pickle', 'wb'))
#         
#===============================================================================



