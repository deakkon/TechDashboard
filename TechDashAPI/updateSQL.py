'''
Created on 27 Nov 2015

@author: jurica
'''
from mysqlUtilities import connectMySQL
from spacy.en import English, LOCAL_DATA_DIR

db = connectMySQL(db='xpath', port=3366)
sqlQuery = "SELECT xpathValuesID, xpathValuesXPathNER FROM xpath.xpathValuesXPath where xpathValuesXPathNER like '%[%]' order by xpathValuesXPathDateTime desc"

db.executeQuery(sqlQuery)
for item in db._connectMySQL__results:
    #===========================================================================
    # print item[1], type(item[1])
    #===========================================================================
    #===========================================================================
    # print len(item[1]), item[1]
    #===========================================================================
    print '========'
    if len(item[1])>2:
        tempList = []
        for tem in item[1].split(','):
            stripped = tem.strip('"').strip("'").strip('[').strip("]")
            stripped = stripped.replace("'","")
            stripped = stripped.replace('"','')
            tempList.append(stripped)
            nerEntities = ",".join(list(set(tempList)))
            print nerEntities
    else:
        nerEntities = 'No NERs Recognized'
    sqlUpdate = "update xpathValuesXPath set xpathValuesXPathNER='%s' where xpathValuesID='%s'"%(nerEntities,item[0])
    db.executeQuery(sqlUpdate)
    db._connectMySQL__connection.commit()
    
        
        
    