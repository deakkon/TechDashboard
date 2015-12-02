# encoding=utf8
'''
Created on 2 Nov 2015

@author: jurica


GENSIM BASED TOPIC MODELING CODE

1) LDA APPLIED TO EXTRACTED CONTENT
2) UPDATE LDA MODELS WITH EACH INDIVIDUAL NEW CONTENT EXTRACTION
3) LOOK IN TO USING NGRAM FOR CONTENT REPRESENTATION
'''


import json
import string

from nltk.corpus import stopwords
from nltk import word_tokenize

from gensim import corpora
from gensim.models import LdaModel, LdaMulticore, HdpModel

import numpy as np
from scipy.spatial.distance import euclidean

import os.path, time
import re
import logging

from mysqlUtilities import connectMySQL



class techDashTopicModel(object):
    '''
    classdocs
    '''


    def __init__(self, destination, fileName, modelName='', ldaPasses='', topicNum=''):
        '''
        Constructor
        '''
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        
        self.__destination = destination
        self.__fileName = fileName
        self.__modelName = modelName
        self.__ldaPasses = ldaPasses
        self.__topicNum = topicNum
                
        #=======================================================================
        # STOP WORDS AND CAHRACTERS
        #=======================================================================
        self.__stopwords = stopwords.words('english')# + string.punctuation
        self.__chars_to_remove = [u'[', u']', u'(', u')', u'*', u'%', u'{', u'}', u'\n', u'\n\n', u'\t', u';',u'/',u'^',u'--',u'\\',u'+',u'-',u'.',u'?',u'&',u'#',u'',u'']
        self.__stopwords.extend(self.__chars_to_remove)
        self.__stopwords.extend([item for item in string.punctuation])

        #=======================================================================
        # DATABASE
        #=======================================================================
        self.__db = connectMySQL(db='xpath', port=3366)
        self.__queryResults = None
        self.__cleanedCorpus = []
        

        if modelName != '' and os.path.exists(self.__destination+modelName+'.lda'):
            self.__ldaModel = LdaModel.load(self.__destination+modelName+'.lda', mmap='r') 
            
        if fileName != '' and os.path.exists(self.__destination+fileName+'.dict'):
            self.__modelDict = corpora.Dictionary.load(self.__destination+fileName+'.dict')
        
    def getCorpusFromDB(self, dateSince=''):
        #=======================================================================
        # ADD PERIODICAL UPDATE BASED ON TIMESTAMPS
        #=======================================================================
        if dateSince == '':
            sqlQuery = '''
                SELECT xpathValuesContent 
                FROM xpathValuesXPath WHERE (xpathValuesdocumentID,xpathValuesXPathContentLength) IN 
                ( SELECT distinct(xpathValuesdocumentID), MAX(xpathValuesXPathContentLength)
                  FROM xpathValuesXPath
                  GROUP BY xpathValuesdocumentID
                )
            '''
            
        else:
            sqlQuery = '''
                SELECT xpathValuesContent 
                FROM xpathValuesXPath WHERE (xpathValuesdocumentID,xpathValuesXPathContentLength) IN 
                ( SELECT distinct(xpathValuesdocumentID), MAX(xpathValuesXPathContentLength)
                  FROM xpathValuesXPath where xpathValuesXPathDateTime >= "%s"
                  GROUP BY xpathValuesdocumentID
                )
            ''' %(dateSince)
            
        self.__db.executeQuery(sqlQuery)
        self.__queryResults = self.__db._connectMySQL__results
        print 'Extracted data from database'
        return self.__db._connectMySQL__results
        
        
    def cleanPreparedCorpus(self):
    
        for dox in self.__queryResults:
            dox = dox[0].decode('utf-8')
            line = [re.sub(r'\W+', '', i.strip()) for i in word_tokenize(dox.lower()) if i not in self.__stopwords]# and len(re.sub(r'\W+', '', i.strip())) > 0 and str.isalpha(re.sub(r'\W+', '', i.strip()))]
            line = [item for item in line if len(item) > 2 and unicode.isalpha(item)]
            self.__cleanedCorpus.append(line)
        #=======================================================================
        # print self.__cleanedCorpus
        #=======================================================================
        print 'Cleaned extracted documents'
       
    def createCorpusFiles(self):
        
        #=======================================================================
        # if sourceFileName=='':
        #     sourceFileName=self.__fileName
        #=======================================================================

        dict = corpora.Dictionary(self.__cleanedCorpus)
        dict.save(self.__destination+self.__fileName+'.dict')
         
        corpus = [dict.doc2bow(text) for text in self.__cleanedCorpus]
        corpora.MmCorpus.serialize(self.__destination+self.__fileName+'.mm', corpus)
        
        print 'Created dictionary and corpus files'
        
    def createLDA(self, fileName = '', modelName= '', ldaPasses='', topicNum=''):
        '''
        fileName -> file for the dictionary (.dict) and corpus (.mm) files 
        modelName -> model name for LDA to save to disk
        ldaPasses -~ number of passes, 10 default
        topicNum -> number of topics to generate, 100 by default
        '''
        if fileName == '':
            fileName = self.__fileName
            
        if ldaPasses == '':
            ldaPasses = self.__ldaPasses
    
        if topicNum == '':
            topicNum = self.__topicNum

        if modelName == '':
            modelName = fileName + '_' + str(ldaPasses) + 'P_' + str(topicNum) + 'T'
        
        dict = corpora.Dictionary.load(self.__destination+fileName+'.dict')
        mm = corpora.MmCorpus(self.__destination+fileName+'.mm')
        
        #lda = models.ldamodel.LdaModel(corpus=mm, id2word=dict, num_topics=6, update_every=1, chunksize=10000, passes=10)
        lda = LdaMulticore(corpus=mm, num_topics=topicNum, id2word=dict, chunksize=30000, passes=ldaPasses, workers=3)
        lda.save(self.__destination+modelName+'.lda')
        #=======================================================================
        # print lda
        #=======================================================================
        print 'Created LDA model %s'%self.__fileName 
        
    def createHDP(self, fileName = '', modelName= ''):
        '''
        fileName -> file for the dictionary (.dict) and corpus (.mm) files 
        modelName -> model name for LDA to save to disk
        ldaPasses -~ number of passes, 10 default
        topicNum -> number of topics to generate, 100 by default
        '''
        if fileName == '':
            fileName = self.__fileName
            
        if modelName == '':
            modelName = self.__fileName
        
        dict = corpora.Dictionary.load(self.__destination+fileName+'.dict')
        mm = corpora.MmCorpus(self.__destination+fileName+'.mm')

        hdp = HdpModel(corpus=mm, id2word=dict)
        hdp.save(self.__destination+modelName+'.hdp')
        print hdp
        print 'Created HDP model %s'%self.__fileName 


    def analyzeLDA(self, modelName='', numberOfTerms=''):
        '''
        modelName -> name of model to read in to memory without the extension
        '''
        
        if modelName=='':
            modelName=self.__fileName
            
        if numberOfTerms == '':
            numberOfTerms=100
            
        write2file = self.__destination+modelName+"_results_%s_SW.csv"%(numberOfTerms)
        #=======================================================================
        # allTopicsFile = self.__destination+modelName+"_results_AllTopics.csv"
        #=======================================================================
        
        resultsCSV = open(write2file, "wb")
        model = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)
         
        #and another way, only prints top words 
        for t in range(0, model.num_topics-1):
            #===================================================================
            # print 'topic {}: '.format(t) + ', '.join([v[1] for v in model.show_topic(t, numberOfTerms)])
            #===================================================================

            topicSet = [v[1].lstrip().rstrip() for v in model.show_topic(t, numberOfTerms) if v[1] not in self.__stopwords]
            listSet = set(topicSet)

            for key in self.__queryWords:  
                difference = set(topicSet).intersection(self.__queryWords[key])
                 
                if len(difference) > 0:
                    self.__overlapingTopics[key][t]=topicSet
        
        try:
            for key in self.__overlapingTopics:
                if self.__overlapingTopics[key]:
                    for topicKey in self.__overlapingTopics[key]:
                        topicTerms = [w.lstrip().rstrip() for w in self.__overlapingTopics[key][topicKey] if w not in self.__stopwords][:100]
                        #=======================================================
                        # topicTerms = [w.translate(None, ''.join(self.__chars_to_remove)) for w in topicTerms if w !='']
                        #=======================================================
                        resultsCSV.write(key+';'+str(topicKey)+';'+', '.join(topicTerms)+'\n\n')
                        print key,'\t',topicKey,'\t', topicTerms
                    resultsCSV.write('***************************************\n')
                print '*************************\n'
                
            write2fileJSON = self.__destination+modelName+"_results_%s_SW.json"%(numberOfTerms)
            with open(write2fileJSON, 'w') as fp:
                json.dump(self.__overlapingTopics, fp)
     
        except KeyError as e: 
            print e
            pass 
        
        resultsCSV.close()

        #pprint.pprint(self.__overlapingTopics)
        
    def analyzeUniqueLDA(self, modelName='', numberOfTerms=''):
        '''
        modelName -> name of model to read in to memory without the extension
        '''
        
        if modelName=='':
            modelName=self.__fileName
            
        if numberOfTerms=='':
            numberOfTerms=100
            
        write2File = self.__destination+modelName+"_results_unique_%sTerms.csv"%(numberOfTerms)
        resultsCSV = open(write2File, "wb")
        
        model = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)

         
        #and another way, only prints top words 
        for t in range(0, model.num_topics-1):
            #===================================================================
            # print 'topic {}: '.format(t) + ', '.join([v[1] for v in model.show_topic(t, 500)])
            #===================================================================
            # raw_input('prompt')
            topicSet = [v[1].lstrip().rstrip() for v in model.show_topic(t, numberOfTerms) if v[1] not in self.__stopwords]
            #===================================================================
            # print type(topicSet), topicSet
            #===================================================================
            listSet = set(topicSet)
            #print listSet
            #print type(topicSet), topicSet
            for key in self.__queryWords:  
                #print self.__queryWords[key]
                difference = set(topicSet).intersection(self.__queryWords[key])
                 
                if len(difference) > 0:
                    self.__overlapingTopics[key][t]=topicSet
        
        try:
            for key in self.__overlapingTopics:
                uniqueQueryTerms = []
                if self.__overlapingTopics[key]:
                    for topicKey in self.__overlapingTopics[key]:
                        topicTerms = [w for w in self.__overlapingTopics[key][topicKey] if w not in self.__stopwords]
                        uniqueQueryTerms.extend(topicTerms)
                        
                uniqueQueryTerms = [x for x in set(uniqueQueryTerms)]
                resultsCSV.write(key+';'+str(topicKey)+';'+', '.join(uniqueQueryTerms)+'\n\n')
                resultsCSV.write('***************************************\n')
                print key, uniqueQueryTerms
                print '*************************\n'

        except KeyError as e: 
            print e
            pass 
        
        resultsCSV.close()
        #pprint.pprint(self.__overlapingTopics)
        
    def getAllTopics(self, modelName='', numberOfTerms=100):
        '''
        modelName -> name of model to read in to memory without the extension
        '''
        
        returningData = {}
        
        if modelName=='':
            modelName=self.__fileName
            
        model = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)
        
        return model.show_topics(num_topics=model.num_topics,num_words=numberOfTerms, formatted=False)
    
    def getTopicdetails(self,topicId, numOfwords=100):
        
        model = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)
    
        return model.show_topic(topicId,numOfwords)
    
    def updateModel_LDA(self, dictname, modelName):
        
        #=======================================================================
        # GET LAST MODIFIED DATE IN MYSQL FORMAT
        #=======================================================================

        
        #=======================================================================
        # GET NEW DOCUMENTS SINCE LAST MODIFIED DATE AND PREPARE THEM
        #=======================================================================
        modelModified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(self.__destination+modelName+'.lda') ))
        self.getCorpusFromDB(modelModified)
        self.cleanPreparedCorpus()
        
        #=======================================================================
        # UPDATE DICT, CORPUT AND LDA MODEL WITH NEW DOCUMENTS
        #=======================================================================
        oldDict = corpora.Dictionary.load(self.__destination+dictname+'.dict')
        newCorpora = [oldDict.doc2bow(text) for text in self.__cleanedCorpus]
 #==============================================================================
 #        oldContent =  self.__destination+dictname+'.mm'
 #        print oldContent
 #         
 #        oldDict = corpora.Dictionary.load(self.__destination+dictname+'.dict')
 #        newDict = corpora.Dictionary(self.__cleanedCorpus)
 #        mergedDict = oldDict.merge_with(newDict)
 # 
 #        oldCorpora = corpora.MmCorpus(self.__destination+dictname+'.mm')
 #        newCorpora = [newDict.doc2bow(text) for text in self.__cleanedCorpus]
 #        mergedCorpus = itertools.chain(oldCorpora,mergedDict[newCorpora])
 #     
 #        mergedDict.save(self.__destination+dictname+'.dict')
 #        corpora.MmCorpus.serialize(self.__destination+dictname+'.mm', mergedCorpus)
 #==============================================================================

        #=======================================================================
        # dict = corpora.Dictionary.load(self.__destination+modelName+'.dict')
        # mm = corpora.MmCorpus(self.__destination+modelName+'.mm')
        #=======================================================================
        ldaModel = LdaModel.load(self.__destination+modelName+'.lda', mmap='r')
        ldaModel.update(newCorpora)
        lda.save(self.__destination+modelName+'.lda')
        
        
    def getDocumentTopics(self, documentContent, documentId=''):
        
        #===============================================================================
        # GET DOCUMENT AND PREPARE ITS CONTENT
        #===============================================================================
        document = documentContent.decode('utf-8')
        line = [re.sub(r'\W+', '', i.strip()) for i in word_tokenize(document.lower()) if i not in self.__stopwords]# and len(re.sub(r'\W+', '', i.strip())) > 0 and str.isalpha(re.sub(r'\W+', '', i.strip()))]
        line = [item for item in line if len(item) > 2 and unicode.isalpha(item)]
        
        #=======================================================================
        # OPEN LDA AND DICT FILES AND PROJECT DOCUMENT ON TO LDA MODEL
        #=======================================================================
        #=======================================================================
        # ldaModel = LdaModel.load(self.__destination+modelName+'.lda', mmap='r') 
        # modelDict = corpora.Dictionary.load(self.__destination+dictname+'.dict')
        #=======================================================================
        documentBOW = self.__modelDict.doc2bow(line)
        #=======================================================================
        # print documentBOW
        #=======================================================================
        assignedTopic = sorted(self.__ldaModel[documentBOW], key=lambda x: x[1], reverse=True)
        #=======================================================================
        # print assignedTopic
        #=======================================================================
        #=======================================================================
        # print assignedTopic[0][0]
        #=======================================================================
        
        #=======================================================================
        # UPDATE DATABASE WITH BGIHHEST MATHING CATEGORY
        #=======================================================================
        if documentId != '':
            sqlQuery = "update xpathValuesXPath set xpathValuesXPathMainTopic = '%s' where xpathValuesID='%s'" % (assignedTopic[0][0], documentId)
            #===================================================================
            # print sqlQuery
            #===================================================================
            self.__db.executeQuery(sqlQuery)
            self.__db._connectMySQL__connection.commit()
        #=======================================================================
        # RETURN SORTED DATA IF NEEDED
        #=======================================================================
        else:
            return assignedTopic[0][0]
    
    
    def updateAllNonTOpicDocuments(self):
        query = "select xpathValuesID, xpathValuesContent from xpathValuesXPath where xpathValuesXPathMainTopic is Null" 
        self.__db.executeQuery(query)
        
        for item in self.__db._connectMySQL__results:
            self.getDocumentTopics(item[1],'initalModel', '500P_20T',item[0])
    
        
    def normalizeLDA(self, modelName='', numberOfTerms=''):
        
        if modelName=='':
            modelName=self.__fileName
            
        if numberOfTerms == '':
            numberOfTerms=100

        ldaModel = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)
        summaryDict = dict.fromkeys(ldaModel.id2word.values(), 0)
        normalizedDict = {}
        #=======================================================================
        # NORMALIZATION AND SIMILAR TOPIC CALCULATION
        #=======================================================================
        #=======================================================================
        # vectors = []
        #=======================================================================
        print 'Summarizing over the LDA topics'
        for t in range(0, ldaModel.num_topics-1):
            topic = ldaModel.show_topic(t, ldaModel.num_terms)
            print 'Summarizing topic {}: '.format(t)
            for topicItem in topic:
                summaryDict[topicItem[1]]=summaryDict[topicItem[1]]+topicItem[0]
                
        print 'Normalizing'
        for t in range(0, ldaModel.num_topics-1):
            topicName = 'Normalizing topic {}: '.format(t)
            topicItems = ldaModel.show_topic(t, ldaModel.num_terms)
            topicItemsNormalized = [(float(x[0]/summaryDict[x[1]]), x[1].lstrip().rstrip()) if summaryDict[x[1]] != 0 else ((0, x[1].lstrip().rstrip())) for x in topicItems]
            topicItemsNormalized = sorted(topicItemsNormalized, key=lambda tup: tup[0], reverse=True)
            #==================================================================
            # extract weights for vectors and similarity calculations
            #===================================================================
            #===================================================================
            # topicItemsNormalizedVector = [x[0] for x in sorted(topicItemsNormalized, key=lambda tup: tup[1])]
            # vectors.append(topicItemsNormalizedVector)
            #===================================================================
            #===================================================================
            # print topicItems[:10]
            # print topicItemsNormalized[:10]
            #===================================================================
            #===================================================================
            # normalizedDict[topicName]=topicItemsNormalized[:numberOfTerms]
            #===================================================================
            normalizedDict[topicName]=topicItemsNormalized
 
        print 'Finished normalizing.\n Finding overlaping terms.\n'
         
         
         
        write2File = self.__destination+modelName+"_results_normalized_%sTerms_SW.csv"%(numberOfTerms)
        resultsCSV = open(write2File, "wb")
          
        write2FileUnique = self.__destination+modelName+"_results_normalized_unique_%sTerms_SW.csv"%(numberOfTerms)
        resultsCSVUnique = open(write2FileUnique, 'wb')
        #and another way, only prints top words
        for normalizedKey in normalizedDict.keys():
            #===================================================================
            # print 'topic {}: '.format(t) + ', '.join([v[1] for v in model.show_topic(t, 500)])
            #===================================================================
            print 'Overlaps in topic {}: '.format(normalizedKey)
             
            topicSet = [v[1].lstrip().rstrip() for v in normalizedDict[normalizedKey] if v[1].lstrip().rstrip() not in self.__stopwords][:numberOfTerms]
            listSet = set(topicSet)
            print listSet
            #print type(topicSet), topicSet
            for key in self.__queryWords:  
                #print self.__queryWords[key]
                difference = set(topicSet).intersection(self.__queryWords[key])
                   
                if len(difference) > 0:
                    self.__overlapingTopics[key][normalizedKey]=topicSet
                    #===========================================================
                    # TO DO: CALCULATE MOST SIMILAR NORMALIZED LDA TOPICS TO NORMALIZEDKEY
                    #===========================================================
        print 'Finished overlap.\nWriting to file %s'%(write2File)
          
        try:
            for key in self.__overlapingTopics:
                uniqueQueryTerms = []
                if self.__overlapingTopics[key]:
                    for topicKey in self.__overlapingTopics[key]:
                        topicTerms = [w for w in self.__overlapingTopics[key][topicKey] if w not in self.__stopwords]
                        resultsCSV.write(key+';'+str(topicKey)+';'+', '.join(topicTerms)+'\n\n')
                        uniqueQueryTerms.extend(topicTerms)
                    resultsCSV.write('***************************************\n')
                uniqueQueryTerms = [x for x in set(uniqueQueryTerms)]                
                resultsCSVUnique.write(key+';\t'+', '.join(uniqueQueryTerms)+'\n\n')
                resultsCSVUnique.write('***************************************\n')
  
            print "Done!"
        except KeyError as e: 
            print e
            pass 
          
        resultsCSV.close()
        
    def calculateLDADistance(self, modelName='', topNSimilar='', topicList=''):
        
        if modelName=='':
            modelName=self.__fileName
    
        if topNSimilar=='':
            topNSimilar=5       
            
        write2file = self.__destination+modelName+"_results_LDA_similarTopics.csv"
        resultsCSV = open(write2file, "wb")
        
        print 'Reading model data'
        gensimDict = corpora.Dictionary.load(self.__destination+self.__fileName+'.dict')
        ldaModel = LdaModel.load(self.__destination+modelName+'.lda',  mmap=None)
        topics = ldaModel.show_topics(num_topics=ldaModel.num_topics, num_words=len(gensimDict),formatted=False)
        #=======================================================================
        # num_topics=ldaModel.num_topics                             
        # num_words=len(gensimDict)
        #=======================================================================
        
        #=======================================================================
        # GET SIMILARITY VECTORS
        #=======================================================================
        print 'Extractig vectors'
        topicsSorted = [sorted(x,  key=lambda x: x[1]) for x in topics]
        vectors = []
            
        for topic in topicsSorted:
            vector = [item[0] for item in topic]
            vectors.append(vector)

        #=======================================================================    
        # CALCULATE SIMILARITIES BETWEEN TOPICS
        #=======================================================================
        print 'Calculating distances between LDA topics\n'
        results = []
        for topicListItem in topicList:
            distances = []
            for j in range (0, len(vectors)):
                dist = euclidean(vectors[topicListItem], vectors[j])
                #===============================================================
                # print topicListItem, j, dist
                #===============================================================
                distances.append(dist)
            results.append(distances)

        #=======================================================================
        # EXPORT TOP N SIMILAR TOPICS NAD PRINT OUT QUERY TERMS
        #=======================================================================
        print 'Writing found similar topics to file\n'
        for resultItem in range(0,len(results)):
            similarLDATopics = np.argsort(results[resultItem])[::-1]
              
            for similarItem in similarLDATopics[:topNSimilar]:
                #===============================================================
                # print topicList[resultItem],similarItem
                #===============================================================
                resultsCSV.write(str(topicList[resultItem])+'; '+str(similarItem)+'; '+', '.join(x[1].lstrip().rstrip() for x in topics[similarItem][:100])+'\n\n')
            resultsCSV.write('*******************************************\n\n')

#===============================================================================
# lda = techDashTopicModel( destination='/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/', fileName='fullModel')
# lda.getCorpusFromDB()
# lda.cleanPreparedCorpus()
# lda.createCorpusFiles()
# lda.createLDA(ldaPasses=100, topicNum=20)
#===============================================================================

#===============================================================================
# lda.createHDP()
# lda.updateModel_LDA('modelsLDAinitalModel', 'modelsLDA500P_20T')
#===============================================================================



