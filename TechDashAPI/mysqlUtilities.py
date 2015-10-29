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
    GET METHODS
    '''    
    def get_user(self):
        return self.__user

    def get_pass(self):
        return self.__pass

    def get_db(self):
        return self.__db

    def get_host(self):
        return self.__host
    
    def get_results(self):
        return self.__results
    
    def get_cursor(self):
        return self.__cursor
    
    def get_connection(self):
        return self.__connection
    
    '''
    SET METHODS
    '''
    def set_user(self, value):
        self.__user = value

    def set_pass(self, value):
        self.__pass = value

    def set_db(self, value):
        self.__db = value

    def set_host(self, value):
        self.__host = value
        
    def set_connection(self, value):
        self.__connection = value

    def set_cursor(self, value):
        self.__cursor = value

    def set_results(self, value):
        self.__results = value

        
    '''
    DEL METHODS
    '''
    def del_user(self):
        del self.__user

    def del_pass(self):
        del self.__pass

    def del_db(self):
        del self.__db

    def del_host(self):
        del self.__host

    def del_connection(self):
        del self.__connection

    def del_cursor(self):
        del self.__cursor

    def del_results(self):
        del self.__results
        
        
    user = property(get_user, set_user, del_user, "user's docstring")
    pass_ = property(get_pass, set_pass, del_pass, "pass's docstring")
    db = property(get_db, set_db, del_db, "db's docstring")
    host = property(get_host, set_host, del_host, "host's docstring")
    connection = property(get_connection, set_connection, del_connection, "connection's docstring")
    cursor = property(get_cursor, set_cursor, del_cursor, "cursor's docstring")
    results = property(get_results, set_results, del_results, "results's docstring")
    
    '''
    CONNECTIONS AND QUERY EXECUTION
    '''
    def connectDB(self):
        try:
            #print self.__port
            self.__connection = MySQLdb.connect(user=self.__user, passwd=self.__pass, db=self.__db, host=self.__host, port=self.__port)
            self.__cursor = self.__connection.cursor()
        except MySQLdb.Error, e:
            print 'Error in connectDB:',e
            
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