# encoding=utf8
'''
Created on 4 Sep 2015

@author: jurica

DB Class: connect and execute queries

Atributes:
__user -> MySQL username
__pass_-> MySQL password
__db -> MySQL database
__host -> MySQL server address

'''
import MySQLdb

class connectMySQL():

    __user = None
    __pass= None
    __db = None
    __host = None
    __connection = None
    __cursor = None
    __results = None
    
    '''
    Initialize class, set up connection parameters.
    Default values: user='root', passw = '', db='', host='localhost'
        '''
    def __init__(self, user='root', passw = '', db='', host="127.0.0.1", port=3306):
        self.__user = user
        self.__pass = passw
        self.__db = db
        self.__host = host
        self.__port = port
    
    '''
    CONNECTIONS AND QUERY EXECUTION
    '''
    def connectDB(self):
        try:
            #print self.__port
            self.__connection = MySQLdb.connect(user=self.__user, passwd=self.__pass, db=self.__db, host=self.__host, port=self.__port)
            self.__connection.set_character_set('utf8')
            self.__cursor = self.__connection.cursor()
            self.__cursor.execute('SET NAMES utf8;')
            self.__cursor.execute('SET CHARACTER SET utf8;')
            self.__cursor.execute('SET character_set_connection=utf8;')
        except MySQLdb.Error, e:
            print 'Error in connectDB:',e
            
    #===========================================================================
    # @profile
    #===========================================================================
    def executeQuery(self, query):
        
        '''
        if self.__connection or self.__cursor is None:
            raise TypeError
            exit
        '''
        self.connectDB()
        
        try:
            self.__cursor.execute(query)
            self.__results = self.__cursor.fetchall()
            #return self.__results
        except MySQLdb.IntegrityError, e: 
            # handle a specific error condition
            print 'Error has occured: ', e
        except MySQLdb.Error, e:
            # handle a generic error condition
            print 'Error has occured: ', e
        except MySQLdb.Warning, e:
            # handle warnings, if the cursor you're using raises them
            print 'Warrning: ', e
            
        #=======================================================================
        # self.__connection.close()
        #=======================================================================