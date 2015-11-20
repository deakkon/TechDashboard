from flask import Flask, jsonify, render_template, request
from gensim.models import LdaModel
from TechDashAPI.mysqlUtilities import connectMySQL
import json
import pprint
import time
from boto.dynamodb.item import Item


app = Flask(__name__)
#===============================================================================
# app.config["CACHE_TYPE"] = "null"
#===============================================================================


modelDestination = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/'
modelName ='500P_20T'
model = LdaModel.load(modelDestination+modelName+'.lda',  mmap=None)
#===============================================================================
# print dir(model)
#===============================================================================
db = connectMySQL(db='xpath', port=3366)

@app.route('/')
def initialize():
    topicKeywords = {}
    
    for i in range(0,model.num_topics):
        topicKeywords[i]=model.show_topic(i,20)
        
    #===========================================================================
    # SQL QUERY
    #===========================================================================
    query = "select lala.xpathValuesXPathMainTopic,count(*) from (select xpathValuesdocumentID, max(xpathValuesXPathContentLength),xpathValuesXPathMainTopic from xpathValuesXPath group by xpathValuesdocumentID)as lala group by lala.xpathValuesXPathMainTopic order by lala.xpathValuesXPathMainTopic"
    results = db.executeQuery(query)
    categroyArticles = [x for x in db.results]
    
    #===========================================================================
    # PREPARE JSON OBJECT
    #===========================================================================
    chartObject = {}
    chartObject['type'] = "ColumnChart"
    chartObject['options'] = {
        "title": "Documents per LDA topic - Technology Dashboard",
        "isStacked": True,
        "fill": 20,
        "displayExactValues": True,
        "vAxis": {
            "title": "Numer of documents", "gridlines": {"count": 6}
        },
        "hAxis": {
            "title": "LDA category"
        }
    };
    
    chartObject['data'] = {}
    chartObject['data']['cols'] = [{'id': "t", 'label': "LDA categroy", 'type': "string"},{'id': "s", 'label': "Number of documents", 'type': "number"}]
    chartObject['data']['rows'] = []

    for item in categroyArticles:
        chartObject['data']['rows'].append({'c':[{'v':item[0]},{'v':item[1]}]})
        
    
    return render_template('index.html',topicNumber=json.dumps({'topicNumber':model.num_topics,'topicKeywords':topicKeywords,'chartObject':chartObject}))

@app.route('/topic',methods=["GET", "POST"])
def getTopic():
    #===========================================================================
    # GET POST PARAMETER
    #===========================================================================
    post = request.get_json()
    topicId = post.get('topicId')
    #===========================================================================
    # print 'topicId: ',topicId
    #===========================================================================
    
    #===========================================================================
    # GET ALL DATA FOR PARAMETER AND RETURN IN JSON FORMAT
    #===========================================================================
    modelKeywords = [item for item in model.show_topic(topicId, topn=20)]
    cloudKeywords = [{'word':item[1],'size':1} for item in model.show_topic(topicId, topn=20)]

    #===========================================================================
    # GET ALL DOCUMENT BELONGING TO THIS TOPIC, SORTED BY DATE OF EXTRACTION DESCENDING
    #===========================================================================
    query1 = """
            select lala.xpathValuesdocumentID, lala.xpathValuesContent, lala.xpathValuesXPathTitle, lala.xpathValuesXPathMainTopic, lala.xpathValuesXPathDateTime, lala.xpathValuesXPathNER from 
                (select xpathValuesdocumentID, xpathValuesContent, xpathValuesXPathTitle, max(xpathValuesXPathContentLength) as xpathValuesXPathContentLength, xpathValuesXPathMainTopic,xpathValuesXPathDateTime, xpathValuesXPathNER from xpathValuesXPath group by xpathValuesdocumentID) as lala
                where lala.xpathValuesXPathMainTopic = '%s' order by lala.xpathValuesdocumentID DESC;
            """% (topicId)

    results = db.executeQuery(query1)
    categroyArticles = [x for x in db.results]

    categoryArticlesDict =[]
    summeryTopicNumbers = {}
    for item in categroyArticles:
        #=======================================================================
        # SUMMARY NUBMER OF DOCUMENTS PER DAY IN SELECTED TOPIC
        #=======================================================================

        if str(item[4].date()) in summeryTopicNumbers:
            summeryTopicNumbers[str(item[4].date())] += 1
        else:
            summeryTopicNumbers[str(item[4].date())] = 1
        
        #=======================================================================
        # ARTICLE INFORMATION
        #=======================================================================
        try:
            NERs = item[5].split(',')
        except AttributeError:
            NERs = item[5]
            
        categoryArticlesDict.append({'content':item[1],'title':item[2],'articleID':item[0],'NER':NERs, 'show':False})
        
    #===========================================================================
    # GET TOPIC-RELATED STATISTICS; DAY-2-DAY NUMBER OF ARTICLES IN TOPIC
    #===========================================================================
    chartObject = {}
    chartObject['type'] = "ColumnChart"
    chartObject['options'] = {
        "title": "Number of documents in LDA topic over time",
        "isStacked": True,
        "fill": 20,
        "displayExactValues": True,
        "vAxis": {
            "title": "Numer of documents", "gridlines": {"count": 6}
        },
        "hAxis": {
            "title": "Time"
        }
    };
    
    chartObject['data'] = {}
    chartObject['data']['cols'] = [{'id': "t", 'label': "Date", 'type': "string"},{'id': "s", 'label': "Number of documents", 'type': "number"}]
    chartObject['data']['rows'] = []

    
    for item in summeryTopicNumbers:
        chartObject['data']['rows'].append({'c':[{'v':item},{'v':summeryTopicNumbers[item]}]})

    #===========================================================================
    # return data to ajax call
    #===========================================================================
    return json.dumps({'status':'OK','modelKeywords':modelKeywords, 'categroyArticles':categoryArticlesDict, 'topicId':topicId, 'cloudKeywords':cloudKeywords, 'topicChartObject':chartObject});

@app.route('/bottomSheet',methods=["GET", "POST"])
def getBottomSheet():
    return render_template('bottom-sheet-grid-template.html')

@app.route('/dirPagination.tpl.html',methods=["GET", "POST"])
def paginationTemplate():
    return render_template('dirPagination.tpl.html')

@app.route('/getChart', methods=["GET", "POST"])
def getOverallChart():
    
    #===========================================================================
    # SQL QUERY
    #===========================================================================
    query = """select lala.xpathValuesXPathMainTopic,count(*) from (select xpathValuesdocumentID, max(xpathValuesXPathContentLength),xpathValuesXPathMainTopic from xpathValuesXPath group by xpathValuesdocumentID) as lala 
                group by lala.xpathValuesXPathMainTopic order by lala.xpathValuesXPathMainTopic"""
    results = db.executeQuery(query)
    categroyArticles = [x for x in db.results]
    
    #===========================================================================
    # PREPARE JSON OBJECT
    #===========================================================================
    chartValues = {}
    chartValues['type'] = "ColumnChart"
    chartValues['options'] = {
        "title": "Documents per LDA topic - Technology Dashboard",
        "isStacked": True,
        "fill": 20,
        "displayExactValues": True,
        "vAxis": {
            "title": "Numer of documents", "gridlines": {"count": 6}
        },
        "hAxis": {
            "title": "LDA category"
        }
    };
    
    chartValues['data'] = {}
    chartValues['data']['cols'] = [{'id': "t", 'label': "Topping", 'type': "string"},{'id': "s", 'label': "Slices", 'type': "number"}]
    chartValues['data']['rows'] = []

    for item in categroyArticles:
        chartValues['data']['rows'].append({'c':[{'v':item[0]},{'v':item[1]}]})
    
    #===========================================================================
    # print chartValues
    #===========================================================================
    return json.dumps({'type':chartValues['type'] ,'data':chartValues['data'], 'options':chartValues['options']})

@app.route('/getNERSearch', methods=["GET", "POST"])
def getNERSearch():
    post = request.get_json()
    nerKeywords = post.get('nerKeywords')
    overlappingArticles = []
    for keyword in nerKeywords:
        keyword = "%"+ keyword + "%"
        print keyword
        query1 = """
                select lala.xpathValuesdocumentID, lala.xpathValuesContent, lala.xpathValuesXPathTitle, lala.xpathValuesXPathMainTopic, lala.xpathValuesXPathDateTime, lala.xpathValuesXPathNER from 
                    (select xpathValuesdocumentID, xpathValuesContent, xpathValuesXPathTitle, max(xpathValuesXPathContentLength) as xpathValuesXPathContentLength, xpathValuesXPathMainTopic,xpathValuesXPathDateTime, xpathValuesXPathNER 
                    from xpathValuesXPath group by xpathValuesdocumentID) as lala 
                    where lala.xpathValuesXPathNER LIKE '%s' order by lala.xpathValuesdocumentID DESC;
                """% (keyword)
    
        db.executeQuery(query1)
        categroyArticles = [x for x in db.results]
        overlappingArticles.extend(categroyArticles)

    overlappingArticles = list(set(sorted(overlappingArticles, key=lambda x: x[4]))) 

    #=======================================================================
    #  
    #=======================================================================
    categoryArticlesDict =[]
    summeryTopicNumbers = {}
    for item in overlappingArticles:
        #=======================================================================
        # SUMMARY NUBMER OF DOCUMENTS PER DAY IN SELECTED TOPIC
        #=======================================================================

        if str(item[3]) in summeryTopicNumbers:
            summeryTopicNumbers[item[3]] += 1
        else:
            summeryTopicNumbers[item[3]] = 1
        
        #=======================================================================
        # ARTICLE INFORMATION
        #=======================================================================
        try:
            NERs = item[5].split(',')
        except AttributeError:
            NERs = item[5]
            
        categoryArticlesDict.append({'content':item[1],'title':item[2],'articleID':item[0],'NER':NERs, 'show':False})
        
    #===========================================================================
    # GET SELECTED KEYWORD-RELATED STATISTICS; DAY-2-DAY NUMBER OF ARTICLES IN TOPIC
    #===========================================================================
    chartObject = {}
    chartObject['type'] = "ColumnChart"
    chartObject['options'] = {
        "title": "Documents and topics for selected keywords",
        "isStacked": True,
        "fill": 20,
        "displayExactValues": True,
        "vAxis": {
            "title": "Numer of documents", "gridlines": {"count": 6}
        },
        "hAxis": {
            "title": "LDA Topic"
        }
    };
    
    chartObject['data'] = {}
    chartObject['data']['cols'] = [{'id': "t", 'label': "LDA Topic", 'type': "string"},{'id': "s", 'label': "Number of documents", 'type': "number"}]
    chartObject['data']['rows'] = []

    
    for item in summeryTopicNumbers:
        chartObject['data']['rows'].append({'c':[{'v':item},{'v':summeryTopicNumbers[item]}]})
        
    #===========================================================================
    # GET ALL KEYWORDS FOR TOPICS WHICH DEFINE THE ARTICLES
    #===========================================================================
    topicKeywords = []
    for key in summeryTopicNumbers.keys():
        print key, type(key)
        topicKeywords.extend([item for item in model.show_topic(int(key), topn=20)])
    
    print topicKeywords
    topicKeywords = sorted(topicKeywords, key=lambda x: x[0])
    #===========================================================================
    # return data to ajax call
    #===========================================================================
    return json.dumps({'modelKeywords':topicKeywords, 'categroyArticles':categoryArticlesDict, 'topicChartObject':chartObject});
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
    