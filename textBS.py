from lxml import html, etree
from bs4 import BeautifulSoup
import urllib2
from lxml.html.clean import Cleaner

url = 'http://www.cnet.com/news/best-buy-tries-to-woo-consumers-with-another-pre-black-friday-sale/#ftag=CADf328eec'
xpathRule = '//*/div[contains(@class, "col-8")]'
htmlElements = ['body', 'header', 'nav', 'footer', 'article', 'section', 'aside', 'div', 'span']
htmlAttributes = ['id', 'class']
htmlElementsSkip = ['script']


page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(url)
htmlFile = html.parse(page)

xpathContentFile = htmlFile.xpath(xpathRule)

for xpathElement in xpathContentFile:
    directChildren = " ".join([etree.tostring(child) for child in xpathElement.getchildren() if child.tag not in htmlElementsSkip and child.tag not in htmlElements])
    soup = BeautifulSoup(directChildren, "lxml")
    extractedContent = soup.find_all(recursive=False)
    
    if len(extractedContent)>0:
        print extractedContent[0]
        print '\n\n'
        print " ".join((extractedContent[0].get_text()).split())
    print '-------------'