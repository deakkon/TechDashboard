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
        self.__htmlElementsSkip = ['script','noscript']
        
    def extractContent(self, path, htmlFile):

        try:
            xpathContentFile = htmlFile.xpath(path)
        except AttributeError:
            print traceback.print_exc()
            return
         
        childrenValues = []
        
        try:
            for xpathElement in xpathContentFile:
                childrentext = ' '.join([child.text.strip() for child in xpathElement.getchildren() if child.text and child.tag not in self.__htmlElementsSkip])
                childrentext = ' '.join(childrentext.split())

                if childrentext.isspace() or len(childrentext) == 0:
                    childrenValues.append('empty')
                else:
                    childrenValues.append(childrentext)

        except:
            e = sys.exc_info()[0]
            print e
            print traceback.print_exc()
            childrenValues.append('empty')
            
        if len(childrenValues) == 0:
            childrenValues.append('empty')
            
        return list(set(childrenValues))
    
    def calculateRatio(self, itemChildrenTextFile, path, htmlFileBackgroundKnowledge, nodeBackgroundKnowledge):
        
        ratioList = []
    
        if len(itemChildrenTextFile) > 0:

            sumBkn = sum( [ htmlFileBackgroundKnowledge[key]['extractCount'] for key in htmlFileBackgroundKnowledge.keys()])
            extractCount = htmlFileBackgroundKnowledge[path]['extractCount']

            for itemChild in itemChildrenTextFile:
                ratio = []
                for itemBack in nodeBackgroundKnowledge:
                    ratio.append(editdistance.eval(itemChild, itemBack) * 2 / (len(itemChild)+len(itemBack)))
                
                print histogram2(ratio,2)
                ratioList.append(median(ratio))
                
        
        else:
            ratioList.append(0)

        print ratioList, mean(ratioList), median(ratioList)
        return mean(ratioList)