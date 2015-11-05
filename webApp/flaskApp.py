from flask import Flask, jsonify, render_template, request
from gensim.models import LdaModel

app = Flask(__name__)
#===============================================================================
# app.config["CACHE_TYPE"] = "null"
#===============================================================================


modelDestination = '/Users/jurica/Documents/workspace/eclipse/TechDashboard/modelsLDA/'
modelName ='modelsLDA500P_20T'
model = LdaModel.load(modelDestination+modelName+'.lda',  mmap=None)

@app.route('/')
def hello_world():
    #===========================================================================
    # return model.num_topics
    #===========================================================================
    return render_template('index.html',result=model.num_topics)

@app.route('/topic/<topicId>')
def getTopic(topicId):
    #===========================================================================
    # a = request.args.get('a', 0, type=int)
    #===========================================================================
    return 'Blah %s' %(topicId)
    return 


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')