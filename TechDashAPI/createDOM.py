'''
Created on 14 Sep 2015

@author: jurica
'''
from bs4 import BeautifulSoup, Doctype
import urllib2
import csv
from urlparse import urlparse #domain extraction
from mysqlUtilities import connectMySQL #mysql operations -- ADD COMMIT FOR DELETE UPDATE INSERT VIA PARAMETER DO EXECUTEQUERY()
import json, os, sys, dpath, dicttoxml
import pprint
import traceback
from cookielib import CookieJar

class createDom(object):
    '''
    classdocs
    CREATE DOM STRUCTURE FROM FILE OR URL
    '''
    __html4Elements = ['div','span']
    __html5Elements = ['header','nav','footer','article','section','aside', 'div', 'span']
    __doctype = None
    __url = None
    __fileName = 'dummyFile.csv'
    __domain = None
    __domainDBkey = None

    def __init__(self, html4Elements=__html4Elements, html5Elements=__html5Elements, doctype=__doctype, url=__url, fileName=__fileName, domain=__domain, domainDBkey=__domainDBkey):
        #URL TO EXTRACT XPATH AND CONTENT FROM
        self.__url = url
        
        #BASED ON DOCTYPE, DIFFERENT SET OF STRUCTURE HTML ELEMENTS ARE USED
        self.__doctype = doctype
        self.__html4Elements = html4Elements
        self.__html5Elements = html5Elements
        self.__structureElements = None

        #INITAL EMPTY DICTIONARY FOR INITAL STAGE OF PARSING/EXTRACTING
        self.__domDict = {}

        #DB CONNECTIVITY AND FUNCTIONALITY
        self.__db = connectMySQL(db='xpath', port=3366)
        #print dir(self.__db)
        
        #domain information
        self.__domain = domain
        self.__domainDBkey = domainDBkey
        self.__documentIDKey = None
        
        #CSV file operations - DISCARDED FOR NOW, SWITHING TO MYSQL OPERATION
        self.__fileName = fileName
        try:
            self.__f = open(self.__fileName, "a")
            self.__spamwriter = csv.writer(self.__f, delimiter=';',
                            quotechar='/', quoting=csv.QUOTE_NONE)
        except:
            print("There is no file named", self.__filename)
            
        #GET DB KEY FOR CURRENT DOMAIN OR INSERT IN TO DB IF CONTENT FROM TAHT DOMAIN NOT YET ANALYZED
        self.getDomainKey()
        
        #=======================================================================
        # START CREATING DOM TREE
        #=======================================================================
        self.readDOMrecursive()
        
    def checkDoctype(self, soup):
        items = [item for item in soup.contents if isinstance(item, Doctype)]
        #=======================================================================
        # print items
        #=======================================================================
        if items[0] == 'html':
            self.__structureElements = self.__html5Elements
        else:
            self.__structureElements = self.__html4Elements
            
        return items[0] if items else None

    
    def getDomainKey(self):
        '''
        Check if at least one document from domain was already analyzed! 
        '''
        parsed_uri = urlparse(self.__url )
        self.__domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        #print self.__domain
        sqlQuery = 'select domainListID from domainList where domainName="%s"' %(self.__domain)
        #sqlQuery = 'select domainListID from domainList'
        self.__db.executeQuery(sqlQuery)
        #print self.__db._connectMySQL__results
        if len(self.__db._connectMySQL__results) == 1:
            #===================================================================
            # print "Domain already in the database! @ getDomainKey"
            #===================================================================
            results = self.__db._connectMySQL__results
            self.__domainDBkey = results[0][0]
        elif len(self.__db._connectMySQL__results) >= 1:
            print "Something is wrong in the domain -> DB Key mapping"
            sys.exit(0)
        else:
            print 'Adding domain %s to list @ getDomainKey' %(self.__domain) 
            sqlQuery = 'insert into domainList (domainName) values("%s")'%(self.__domain)
            self.__db.executeQuery(sqlQuery)
            self.__db._connectMySQL__connection.commit()
            self.__domainDBkey = self.__db._connectMySQL__cursor.lastrowid
            #===================================================================
            # print self.__domainDBkey
            #===================================================================
                    
    def readDOMrecursive(self, parentNodeElement='', parentNodeName='', parentNodeID='', dictPath=''):
        
        if self.__domDict:
            pass
        
        else:
            #print 'domDict is empty'
            try:
                #===============================================================
                # page=urllib2.urlopen(self.__url)
                #===============================================================
                page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(self.__url)
            except urllib2.HTTPError:
                print ('Error opening the url @ readDOMrecursive, %s') %(self.__url)
                return
            
            try:
                soup = BeautifulSoup(page.read(), "lxml")
                self.checkDoctype(soup)
            except IndexError:
                return
            
            docBody = soup.find('body')
            self.__domDict={}
            self.__domDict[docBody.name]={}
            self.readDOMrecursive(parentNodeElement=docBody)

        #=======================================================================
        # print '***********************'
        #=======================================================================
        try:
            for child in parentNodeElement.children:
                if child.name in self.__structureElements:
                    parentNodes = [tag.name for tag in child.find_parents() if tag.name in self.__structureElements][::-1]

                    #===========================================================
                    # EXTRACT ID AND CLASS ATTRIBUTES, PREPARE THEM FOR WRITTING 
                    #===========================================================
                    try:
                        if type(child.attrs['id']) is list or type(child.attrs['id']) is tuple:
                            idAttributeValue = ' '.join(child.attrs['id'])
                        else:
                            idAttributeValue = child.attrs['id']
                    except KeyError, e:
                        idAttributeValue = ''
                    
                    try:
                        if type(child.attrs['class']) is list or type(child.attrs['class']) is tuple:
                            classAttributeValue = ' '.join(child.attrs['class'])
                        else:
                            classAttributeValue = child.attrs['class']
                    except KeyError, e:
                        classAttributeValue = ''
                    
                    #===========================================================
                    # PREPARE THE DICT PATH FOR VALUES EXTRACTED ABOVE
                    #===========================================================
                    if len(parentNodes) > 0:
                        path2Dict = 'body/' + '/'.join(parentNodes) + '/' + child.name
                    else:
                        path2Dict = 'body/' + child.name
                    
                    try:
                        if dpath.util.search(self.__domDict,path2Dict):
                            value = dpath.util.get(self.__domDict,path2Dict+'/values')
                            value.append([classAttributeValue,idAttributeValue])
                            b_set = set(map(tuple,value)) 
                            value = map(list,b_set) 
                            dpath.util.set(self.__domDict, path2Dict+'/values', value)
                    
                        else:
                            #===================================================
                            # print 'Adding new key to dict', path2Dict
                            #===================================================
                            appendvalues = list()
                            appendvalues.append([classAttributeValue,idAttributeValue])
                            dpath.util.new(self.__domDict, path2Dict+'/values', appendvalues)


                    except (ValueError,Exception) as e:
                        print 'Error on path ',path2Dict, e
                        traceback.print_exc()
                        sys.exit()
                        
                    self.readDOMrecursive(child)

        except Exception, e:
            #===================================================================
            # print 'Exception: ', e
            #===================================================================
            pass
