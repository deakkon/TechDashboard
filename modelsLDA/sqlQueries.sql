-- GET NUMER OF DOCUMENTS PER TOPIC FOR AN OVERVIEW GRAPH --
select count(*),lala.xpathValuesXPathMainTopic from 
	(select xpathValuesdocumentID, max(xpathValuesXPathContentLength),xpathValuesXPathMainTopic from xpathValuesXPath group by xpathValuesdocumentID)as lala  
    group by lala.xpathValuesXPathMainTopic order by lala.xpathValuesXPathMainTopic;

-- GET DOCUCMENT FROM SELECTED TOPIC --
select lala.xpathValuesdocumentID, lala.xpathValuesContent, lala.xpathValuesXPathTitle,lala.xpathValuesXPathMainTopic from 
	(select xpathValuesdocumentID, xpathValuesContent, xpathValuesXPathTitle, max(xpathValuesXPathContentLength) as xpathValuesXPathContentLength, xpathValuesXPathMainTopic,xpathValuesXPathDateTime from xpathValuesXPath group by xpathValuesdocumentID)as lala
    where lala.xpathValuesXPathMainTopic = '5' order by lala.xpathValuesXPathDateTime DESC;
    
-- GET NUMBER MYSQL CONNECTIONS --
show full processlist;

-- GET ALL VALUES WITH NO NER --
SELECT COUNT(*) FROM xpathValuesXPath WHERE xpathValuesXPathNER IS NULL;

-- GET ALL ELEMENTS WITH NER
SELECT xpathValuesID,xpathValuesXPathNER FROM xpathValuesXPath WHERE xpathValuesXPathNER IS NOT NULL AND xpathValuesXPathNER != '';