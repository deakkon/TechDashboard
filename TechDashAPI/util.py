'''
Created on 26 Oct 2015

@author: jurica
'''
from __future__ import division
from lxml import *
import sys
import traceback
#===============================================================================
# import Levenshtein
#===============================================================================
import editdistance
from numpy import mean, median, amax, sum, array, append
from scipy.stats import histogram, histogram2


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
        
    def extractContent(self, path, htmlFile):

        try:
            xpathContentFile = htmlFile.xpath(path)
            childrenValues = []
            
            if len(xpathContentFile) == 0:
                childrenValues.append('empty')
            else:
                  
                for xpathElement in xpathContentFile:
                    childrentext = ' '.join([child.text.strip() for child in xpathElement.getchildren() if child.text and child.tag not in self.__htmlElementsSkip])
                    #===========================================================
                    # print '1',childrentext
                    #===========================================================
                    childrentext = ' '.join(childrentext.split())
                    #===========================================================
                    # print '2',childrentext
                    #===========================================================
    
                    if childrentext.isspace() or len(childrentext) == 0:
                        childrenValues.append('empty')
                    else:
                        childrenValues.append(childrentext)
                                
            #===================================================================
            # print '3',childrenValues
            # raw_input('prompt')                    
            #===================================================================
            print path, childrenValues
            return list(set(childrenValues))

        except AttributeError as er:
            print er
            e = sys.exc_info()[0]
            print e
            print traceback.print_exc()
            return
    
    def calculateRatio(self, itemChildrenTextFile, path, htmlFileBackgroundKnowledge, nodeBackgroundKnowledge):
        
        ratioList = []
    
        if len(itemChildrenTextFile) > 0:

            sumBkn = sum( [ htmlFileBackgroundKnowledge[key]['extractCount'] for key in htmlFileBackgroundKnowledge.keys()])
            extractCount = htmlFileBackgroundKnowledge[path]['extractCount']

            for itemChild in itemChildrenTextFile:
                ratio = []
                for itemBack in nodeBackgroundKnowledge:
                    ratio.append(editdistance.eval(itemChild, itemBack) * 2 / (len(itemChild)+len(itemBack)))
                
                #===============================================================
                # print histogram2(ratio,2)
                #===============================================================
                ratioList.append(median(ratio))
                
        
        else:
            ratioList.append(0)

        #=======================================================================
        # print ratioList, mean(ratioList), median(ratioList)
        #=======================================================================
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
            if element.tag in htmlElements:
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
        for element in domainDoctionaryXML.getiterator():
            if element.tag in htmlElements:
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
        
        xpathPaths = list(set(tempPaths))
        xpathPathsID = list(set(self.__xpathPathsID))
        xpathPathsNoAttrib = list(set(self.__xpathPathsNoAttrib))
        
        return(xpathPaths, xpathPathsID, xpathPathsNoAttrib)