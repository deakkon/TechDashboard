'''
Created on 26 Oct 2015

@author: jurica
'''

#===============================================================================
# FLOATING POINT DIVISIONS
#===============================================================================
from __future__ import division
from time import gmtime, strftime
#===============================================================================
# SYS ORIENTED IMPORTS
#===============================================================================
import sys
import traceback
import editdistance

#===============================================================================
# NUMPY PANDAS DATA MANIPULATION AND CALUCLATIONS
#===============================================================================
import numpy as np
from numpy import mean, median, sum
import pandas as pd
import pickle
import os
#===============================================================================
# OPEN AND MANUPULATE WITH HTML DOCUMENTS FROM URL
#===============================================================================
import urllib2
from lxml import html, etree
from lxml.html.clean import Cleaner
from lxml.etree import tostring
from bs4 import BeautifulSoup
from itertools import chain
from urlparse import urlparse #domain extraction
import httplib

#===============================================================================
# USE MYSQL DATABASE
#===============================================================================
from TechDashAPI.mysqlUtilities import connectMySQL


class utilities(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.__htmlElements = ['body', 'header', 'nav', 'footer', 'article', 'section', 'aside', 'div', 'span']
        self.__htmlAttributes = ['id', 'class']
        self.__htmlElementsSkip = ['script']
        self.__db = connectMySQL(db='xpath', port=3366)
        
        #=======================================================================
        # LXML CLEANER
        #=======================================================================
        self.__cleaner = Cleaner()
        self.__cleaner.javascript = True
        self.__cleaner.scripts = True
        self.__cleaner.style = True
        self.__cleaner.comments = True
        self.__cleaner.embedded = True
        self.__cleaner.frames = True
        self.__cleaner.meta = True
        
        
    #===============================================================================
    # OPEN URL WITH COOKIES ENABLED AND EXCEPTING ERRORS 
    #===============================================================================
    def openULR(self, fileURL):
        try:
            #===================================================================
            # NO CLEANING PERFORMED
            #===================================================================
            url2Open = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(fileURL).geturl()
            page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(url2Open)
            htmlFile = html.parse(page)
            
            #===================================================================
            # LXML CLEANER USED OT GET RID OF JS
            #===================================================================
            #===================================================================
            # page = urllib2.build_opener(urllib2.HTTPCookieProcessor).
            # htmlFile = self.__cleaner.clean_html(html.parse(page))
            # print htmlFile
            #===================================================================

        except (IOError, httplib.BadStatusLine, httplib.HTTPException):
            print ('Error opening the url %s')%(fileURL)
            htmlFile = None
            url2Open = None
            print traceback.print_exc()

        return (url2Open, htmlFile)
    
    #===========================================================================
    # GET PROCESSED URL PAGE ORIGINAL LINK
    #===========================================================================
    def getDomainKey(self, url):
        '''
        Check if at least one document from domain was already analyzed! 
        '''
        parsed_uri = urlparse(url)
        domain = parsed_uri.netloc
        sqlQuery = 'select domainListID from domainList where domainName="%s"' %(domain)
        
        self.__db.executeQuery(sqlQuery)
        #print self.__db._connectMySQL__results
        if len(self.__db._connectMySQL__results) == 1:
            #===================================================================
            # print "Analyzing existing domain %s!"%(self.__domain)
            #===================================================================
            results = self.__db._connectMySQL__results
            domainDBkey = results[0][0]
        elif len(self.__db._connectMySQL__results) > 1:
            print "Something is wrong in the domain -> DB Key mapping"
            sys.exit(0)
        else:
            print 'Adding new domain %s to database' %(domain)
            sqlQuery = 'insert into domainList (domainName) values("%s")'%(domain)
            self.__db.executeQuery(sqlQuery)
            self.__db._connectMySQL__connection.commit()
            domainDBkey = self.__db._connectMySQL__cursor.lastrowid
            
            
        return domainDBkey
    
    #===========================================================================
    # CHECK IF ARTILE ALREADY IN DATABASE
    #===========================================================================
    @profile
    def checkProcessedArticle(self, fileURL):
        
        sqlQuery = 'select documentID from document where documentURL="%s"' %(fileURL)

        self.__db.executeQuery(sqlQuery)
        
        if len(self.__db._connectMySQL__results) > 0:
            documentIDKey = False
        else:
            documentIDKey = True
            
        return documentIDKey
    
    #===========================================================================
    # LXML BASED XPATH EXTRACTION
    # TO DO:
    #     CLEAN TREE FROM SCRIPT AND CSS BEFORE PARSING
    #===========================================================================
    @profile
    def extractXPaths_LXML(self, domain, url, filePath):
        #=======================================================================
        # USE LXML 
        #=======================================================================
        url, htmlFile = self.openULR(url)
        xpathList = []
        currentXpathValues = []
        print strftime("%Y-%m-%d %H:%M:%S", gmtime()), 'extractXPaths_LXML'
        #=======================================================================
        # GET XPATHS FROM FILE @ URL
        #=======================================================================
        for e in htmlFile.iter():
            if e.tag in self.__htmlElements:
                #===============================================================
                # print e, e.tag, type(e), htmlFile.getpath(e) 
                #===============================================================
                xpathValue = htmlFile.getpath(e)
                #===============================================================
                # xpathElements = htmlFile.getpath(e).split('/')
                # if xpathElements[1] == 'div':
                #     xpathValue = '/html'+xpathValue[4:]
                #===============================================================
                    
                xpathList.append(xpathValue)
        
        #=======================================================================
        # CREATE A FILE WITH XPATS OR MERGE WITH EXISTING FILE
        #=======================================================================
        if os.path.isfile(filePath):
            currentXpathValues = pickle.load(open(filePath,'rb'))

        mergedlist = list(set(currentXpathValues + xpathList))
        pickle.dump(mergedlist, open(filePath, 'wb'))
        return mergedlist
    
    #===========================================================================
    # EXTRACT CONTENT - BASIC NATIVE IMPLEMENTATION
    #===========================================================================
    def extractContent(self, path, htmlFile):
    
        try:
            xpathContentFile = htmlFile.xpath(path)
            childrenValues = []
            
            if len(xpathContentFile) == 0:
                childrenValues.append('empty')
            else:
                  
                for xpathElement in xpathContentFile:
                        
                    childrentext = ' '.join([child.xpath("string()") for child in xpathElement.getchildren() if child.text and child.tag not in self.__htmlElementsSkip])
                    childrentext = ' '.join(childrentext.split())
                     
                    
                    if childrentext.isspace() or len(childrentext) == 0:
                        childrenValues.append('empty')
                    else:
                        childrenValues.append(childrentext)
                    
            return list(set(childrenValues))
    
        except AttributeError as er:
            print er
            e = sys.exc_info()[0]
            print e
            print traceback.print_exc()
            return
    
    #===========================================================================
    # EXTRACT CONTENT WITH BEAUTIFUL SOUP
    #===========================================================================
    @profile
    def extractContentBS(self, path, htmlFile):
        print strftime("%Y-%m-%d %H:%M:%S", gmtime()), ' extractContentBS'
        try:
            xpathContentFile = htmlFile.xpath(path)
            childrenValues = []
            
            if len(xpathContentFile) == 0:
                childrenValues.append('empty')
            else:
                  
                for xpathElement in xpathContentFile:
                    
                    directChildren = " ".join([tostring(child) for child in xpathElement.getchildren() if child.tag not in self.__htmlElementsSkip and child.tag not in self.__htmlElements])
                
                    soup = BeautifulSoup(directChildren, "lxml")
                    childrentextSoup = soup.find_all(recursive=False)
    
                    if len(childrentextSoup)>0:
                        childrenTextHTML = childrentextSoup[0]
                        childrenTextClean = " ".join((childrentextSoup[0].get_text()).split())
                        if len(childrenTextClean)>0:
                            childrenValues.append(childrenTextClean)
                        else:
                            childrenValues.append('empty')
                    else:
                        childrenValues.append('empty')
    
            return list(set(childrenValues))
    
        except Exception, err:
            print err, sys.exc_info()[0]
            print traceback.print_exc()
            return False
        
    #===========================================================================
    # EXTRACT CONTENT WITH LXML FUNCTION - NOT GOOD AS IT EXTRACTS TEXT FROM ALL CHILDREN DATA MAKING IMPOSSIBRU TO DETECT THE ACTUAL CONTENT NODES
    #===========================================================================
    def extractContentLXML(self, path, htmlFile):

        try:
            xpathContentFile = htmlFile.xpath(path)
            childrenValues = []
            
            if len(xpathContentFile) == 0:
                childrenValues.append('empty')
            else:
                  
                for xpathElement in xpathContentFile:
                    childrentext = ' '.join(self.__cleaner.clean_html(xpathElement).text_content().split())
                    
                    if childrentext.isspace() or len(childrentext) == 0:
                        childrenValues.append('empty')
                    else:
                        childrenValues.append(childrentext)

            return list(set(childrenValues))

        except AttributeError as er:
            print er
            e = sys.exc_info()[0]
            print e
            print traceback.print_exc()
            return None
    
    #===========================================================================
    # DIFFERENT WAYS OF CALCULATING RATIOS
    #===========================================================================
    def calculateRatio(self, itemChildrenTextFile, path, htmlFileBackgroundKnowledge, nodeBackgroundKnowledge):
        '''
        Character based Levenshtein Distance 
        '''
        
        ratioList = []
    
        if len(itemChildrenTextFile) > 0:
            
            

            sumBkn = sum( [ htmlFileBackgroundKnowledge[key]['extractCount'] for key in htmlFileBackgroundKnowledge.keys()])
            extractCount = htmlFileBackgroundKnowledge[path]['extractCount']

            for itemChild in itemChildrenTextFile:
                ratio = []
                for itemBack in nodeBackgroundKnowledge:
                    
                    #===========================================================
                    # print 'calculateRatio ',itemChild, '\n', itemBack, '\n', editdistance.eval(itemChild, itemBack) * 2 / (len(itemChild)+len(itemBack))
                    #===========================================================
                    
                    ratio.append(editdistance.eval(itemChild, itemBack) * 2 / (len(itemChild)+len(itemBack)))
                
                #===============================================================
                # if extractCount > 0:
                #     ratioList.append(median(ratio) * (extractCount / len(itemChildrenTextFile)))
                # else:
                #===============================================================
                ratioList.append(median(ratio))
                #===============================================================
                # raw_input('prompt')
                #===============================================================
        
        else:
            ratioList.append(0)

        return mean(ratioList)
    
    @profile
    def calculateNormalizedRatio(self, itemChildrenTextFile, path, htmlFileBackgroundKnowledge, nodeBackgroundKnowledge):
        '''
        Character based Levenshtein Distance 
        '''
        
        ratioList = []
    
        try:
            if len(itemChildrenTextFile) > 0:
    
                #===============================================================
                # sumBkn = sum( [ htmlFileBackgroundKnowledge[key]['extractCount'] for key in htmlFileBackgroundKnowledge.keys()])
                # extractCount = htmlFileBackgroundKnowledge[path]['extractCount']
                #===============================================================
    
                for itemChild in itemChildrenTextFile:
                    ratio = []
                    for itemBack in nodeBackgroundKnowledge:
                        
                        #===========================================================
                        # print itemChild, len(itemChild), '\t', itemBack, len(itemBack),'\t', itemChildrenTextFile, len(itemChildrenTextFile)
                        #===========================================================
                        
                        distanceValue = editdistance.eval(itemChild, itemBack) * (2 / (len(itemChild)+len(itemBack))) * (1/len(itemChildrenTextFile))
                        ratio.append(distanceValue)
                        print distanceValue
                        print strftime("%Y-%m-%d %H:%M:%S", gmtime()),'Edit distance calculation'
                    #===============================================================
                    # if extractCount > 0:
                    #     ratioList.append(median(ratio) * (extractCount / len(itemChildrenTextFile)))
                    # else:
                    #===============================================================
                    
                    #===============================================================
                    # print median(ratio)
                    #===============================================================
                    ratioList.append(median(ratio))
                    #===============================================================
                    # raw_input('prompt')
                    #===============================================================
            
            else:
                ratioList.append(0)
        except TypeError:
            ratioList.append(0)
            pass
        
        return mean(ratioList)


    def calculateRatioNGram(self, itemChildrenTextFile, path, htmlFileBackgroundKnowledge, nodeBackgroundKnowledge):
        '''
        
        N-Gram distance measure - to be developed 
        n-gram overlap
        https://pythonhosted.org/ngram/index.html
        http://odur.let.rug.nl/~vannoord/TextCat/textcat.pdf
        
        '''
        ratioList = []
    
        if len(itemChildrenTextFile) > 0:

            sumBkn = sum( [ htmlFileBackgroundKnowledge[key]['extractCount'] for key in htmlFileBackgroundKnowledge.keys()])
            extractCount = htmlFileBackgroundKnowledge[path]['extractCount']

            for itemChild in itemChildrenTextFile:
                ratio = []
                for itemBack in nodeBackgroundKnowledge:
                    ratio.append(editdistance.eval(itemChild, itemBack) * 2 / (len(itemChild)+len(itemBack)))
                
                ratioList.append(median(ratio) / len(itemChildrenTextFile))
                
        
        else:
            ratioList.append(0)

        return mean(ratioList)    
    
    #===============================================================================
    # CREATING XPATH PATHS
    #===============================================================================

    def createXPathFromXMLFile_ShortPath(self, domainDoctionaryXML):
        '''
        load XML file created in createDOM
        get element, its children and build xpaths
        return created xpath (or for every xpath extract content of current file and compare with background knowledge)
        '''
        tempPaths = []
        for element in domainDoctionaryXML.getiterator():
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
                                    
        xpathPaths = list(set(tempPaths))
        return xpathPaths

                    
    def createXPathFromXMLFile_FullPath(self,domainDoctionaryXML):
        #=======================================================================
        # DEPRECATED
        #=======================================================================
        for element in domainDoctionaryXML.getiterator():
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
        
        #=======================================================================
        # xpathPaths = list(set(tempPaths))
        # xpathPathsID = list(set(self.__xpathPathsID))
        # xpathPathsNoAttrib = list(set(self.__xpathPathsNoAttrib))
        # 
        # return(xpathPaths, xpathPathsID, xpathPathsNoAttrib)
        #=======================================================================
    
    def checkNumberOfProcessedArticle(self, domain):
        sqlQuery = 'select count(*) from document  where documentDomainListID = %s' %(domain)
        self.__db.executeQuery(sqlQuery)
        return self.__db._connectMySQL__results[0][0]
            
    def getXpathStatistics(self, xpath, domain):
        sqlQuery = 'SELECT xpathValuesXPathContentLength FROM xpathValuesXPath where xpathValuesXPath = "%s" and xpathValuesXPathContentLength is not Null and xpathValuesdocumentID in (select documentID from document where documentDomainListID = "%s")' %(xpath, domain)
        self.__db.executeQuery(sqlQuery)
        
        results = self.__db._connectMySQL__results
        
        if len(results) > 0:
            pdResults = pd.Series(np.array([item[0] for item in results]))
        else:
            pdResults = pd.Series(np.array([0]))
            
        statDescRes = pdResults.describe(percentiles=[.25,.35,.50, .75, .95])
        print statDescRes
        return statDescRes
        
    def getDomainStatistics(self, domain):
        sqlQuery = 'SELECT xpathValuesXPathContentLength FROM xpathValuesXPath where xpathValuesXPathContentLength is not Null and xpathValuesdocumentID in (select documentID from document where documentDomainListID = "%s")' %(domain)
        self.__db.executeQuery(sqlQuery)
        
        results = self.__db._connectMySQL__results
        
        if len(results) > 0:
            pdResults = pd.Series(np.array([item[0] for item in results]))
        else:
            pdResults = pd.Series(np.array([0]))
            
        statDescRes = pdResults.describe(percentiles=[.1,.25,.35,.50, .75, .95])
        #=======================================================================
        # print statDescRes.keys()
        #=======================================================================
        return statDescRes
        
    def updateLengthInfo(self):
        
        sqlQuery = 'SELECT xpathValuesID, xpathValuesContent FROM xpathValuesXPath where xpathValuesXPathContentLength is Null'
        self.__db.executeQuery(sqlQuery)
        
        results = self.__db._connectMySQL__results
        
        for item in results:
            sqlUpdate = 'update xpathValuesXPath set xpathValuesXPathContentLength = "%s" where xpathValuesID = "%s"'%(len(item[1]),item[0])
            #===================================================================
            # print sqlUpdate
            #===================================================================
            self.__db.executeQuery(sqlUpdate)
            self.__db._connectMySQL__connection.commit()
            
#===============================================================================
# ut = utilities()
# print ut.getXpathStatistics("//*/section[contains(@class, 'page')]", 32)
# print ut.getDomainStatistics(32)
# ut.extractContent(path, htmlFile)
#===============================================================================