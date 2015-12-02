-- GET NUMBER OF DOCUMENTS PER TOPIC FOR AN OVERVIEW GRAPH --
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
SELECT COUNT(*) FROM xpathValuesXPath WHERE xpathValuesXPathNER IS NULL or xpathValuesXPathNER = "" or xpathValuesXPathNER="'" limit 200;

-- GET ALL ELEMENTS WITH NER
SELECT xpathValuesID, xpathValuesdocumentID,xpathValuesXPathNER FROM xpathValuesXPath WHERE xpathValuesXPathNER IS NOT NULL AND xpathValuesXPathNER != "'" and xpathValuesXPathNER != "";

-- GET ALL SIMILAR
select lala.xpathValuesdocumentID, lala.xpathValuesContent, lala.xpathValuesXPathTitle, lala.xpathValuesXPathMainTopic, lala.xpathValuesXPathDateTime, lala.xpathValuesXPathNER from
                    (select xpathValuesdocumentID, xpathValuesContent, xpathValuesXPathTitle, max(xpathValuesXPathContentLength) as xpathValuesXPathContentLength, xpathValuesXPathMainTopic,xpathValuesXPathDateTime, xpathValuesXPathNER
                    from xpathValuesXPath group by xpathValuesdocumentID) as lala
                    where lala.xpathValuesXPathNER LIKE '%Microsoft%' order by lala.xpathValuesdocumentID DESC;
                    
-- GET DOCUMENT FROM EXTRACTED TOPIC
select lala.xpathValuesdocumentID,lala.xpathValuesXPathMainTopic,lala.xpathValuesXPathMainTopic, lala.xpathValuesContent, lala.xpathValuesXPathNER, lala.xpathValuesXPathTitle from 
	(select xpathValuesdocumentID, max(xpathValuesXPathContentLength),xpathValuesXPathMainTopic, xpathValuesContent, xpathValuesXPathNER, xpathValuesXPathTitle  from xpathValuesXPath group by xpathValuesdocumentID)as lala  
	ORDER BY xpathValuesXPathDateTime DESC;
    
-- disable foreign key check
SET foreign_key_checks = 0;
truncate domainList;

-- GET LONGEST ENTRY PER DOCUMENT FOR LDA MODELING
SELECT distinct(xpathValuesdocumentID), xpathValuesContent 
FROM xpathValuesXPath WHERE (xpathValuesdocumentID,xpathValuesXPathContentLength) IN 
( SELECT distinct(xpathValuesdocumentID), MAX(xpathValuesXPathContentLength)
  FROM xpathValuesXPath
  GROUP BY xpathValuesdocumentID
);