from flask import Flask, jsonify, render_template, request
from gensim.models import LdaModel
from TechDashAPI.mysqlUtilities import connectMySQL
import json

app = Flask(__name__)
#===============================================================================
# app.config["CACHE_TYPE"] = "null"
#===============================================================================


modelDestination = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/'
modelName ='500P_20T'
model = LdaModel.load(modelDestination+modelName+'.lda',  mmap=None)
db = connectMySQL(db='xpath', port=3366)

@app.route('/')
def hello_world():
    #===========================================================================
    # return model.num_topics
    #===========================================================================
    return render_template('index.html',result=model.num_topics)

@app.route('/topic',methods=["GET", "POST"])
def getTopic():
    #===========================================================================
    # GET POST PARAMETER
    #===========================================================================
    post = request.get_json()
    topicId = post.get('topicId')
    print topicId
    
    #===========================================================================
    # GET ALL DATA FOR PARAMETER AND RETURN IN JSON FORMAT
    #===========================================================================
    modelKeywords = ','.join([item[1] for item in model.show_topic(topicId, topn=20)])
    #===========================================================================
    # print modelData
    #===========================================================================
    
    #===========================================================================
    # GET ALL DOCUMENT BELONGING TO THIS TOPIC, SORTED BY DATE OF EXTRACTION DESCENDING
    #===========================================================================
    query = "select distinct(xpathValuesContent) from xpathValuesXPath where xpathValuesXPathMainTopic ='%s' order by xpathValuesXPathDateTime DESC limit 20" % (topicId)
    results = db.executeQuery(query)
    categroyArticles = [x for x in db.results]
    
    #===========================================================================
    # return data to ajax call
    #===========================================================================
    return json.dumps({'status':'OK','modelKeywords':modelKeywords, 'categroyArticles':categroyArticles, 'topicId':topicId});

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')