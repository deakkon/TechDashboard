from TechDashAPI.mysqlUtilities import connectMySQL
from TechDashAPI.ContentExtractor import ContentExtractor
from TechDashAPI.ContentExtractorTrainer import ContentExtractorTrainer
from TechDashAPI.createDOM import createDom
from TechDashAPI.util import utilities
from TechDashAPI.topicModeling import techDashTopicModel

from gensim.models import LdaModel

db = connectMySQL(db='xpath', port=3366)
filesFolder = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/xpathModels/'
utilitiesFunctions = utilities()

modelDestination = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/'
modelName ='fullModel_100P_20T'
model = LdaModel.load(modelDestination+modelName+'.lda',  mmap=None)
topicModel = techDashTopicModel(destination='/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/', fileName='fullModel', modelName='fullModel_100P_20T')

#===============================================================================
# UPDATE ALL ARTICLES TO NEW TOPICS
#===============================================================================

sqlQuery = """SELECT `xpathValuesXPath`.`xpathValuesID`, `xpathValuesXPath`.`xpathValuesContent` FROM `xpath`.`xpathValuesXPath`; """

db.executeQuery(sqlQuery)

for item in db._connectMySQL__results:
    #===========================================================================
    # print item
    #===========================================================================
    topicModelCat = topicModel.getDocumentTopics(item[1])
    print topicModelCat
    sqlUpdate = """
        UPDATE `xpath`.`xpathValuesXPath`
        SET
        `xpathValuesXPathMainTopic` = '%s'
        WHERE `xpathValuesID` = '%s';
    """%(topicModelCat,item[0])
    db.executeQuery(sqlUpdate)
    db._connectMySQL__connection.commit()