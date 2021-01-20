##############################################################
# Functions to gattering data from WHO, CDC and CNN FAQ pages
# Author: Janneth Chicaiza
# Publication date: January 19, 2021
#############################################################


import requests
import urllib
import re
from bs4 import BeautifulSoup
import json
import os
import csv
import re
from datetime import date

regex = re.compile(r'[\n\r\t]')

##############
### Basic function to download content of webpages
##############
def download(url, user_agent='Mozilla/5.0', num_retries=2):
	#Descarga una url. En caso de existir errores errores [500 600], intentar nuevamente.
	#Función adaptada desde (Lawson Richard, 2015)
	print('Descargando: ', url)
	headers = {'User-agent': user_agent}
	request = urllib.request.Request(url, headers=headers)
	try:
		html = urllib.request.urlopen(request).read()
	except urllib.error.URLError as e:
		print('Error descargando:', e.reason)
		html = None
		if num_retries > 0:
			if hasattr(e, 'code') and 500 <= e.code < 600:
				return download(url, user_agent, num_retries-1)
	return html

##############
# WHO
# Method 1: https://www.cdc.gov/coronavirus/2019-ncov/faq.html
##############

def get:
	_root = 'https://www.who.int/'
	_domain = 'https://www.who.int/emergencies/diseases/novel-coronavirus-2019/question-and-answers-hub/'
	_date = ''
	categories = []

	# Get category name:
	getCategories(_domain)

	# Llenar QA pairs:
	fields = ['date', 'url', 'category', 'question', 'answer']
	with open('who_qapairs.csv','w') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerow(fields)

	for i in categories:
		getQA(i[0], i[1])	

def getCategories(_domain):
	html = download(_domain)
	soup = BeautifulSoup(html,"html.parser")
	a = soup.find_all(class_="sf-list-vertical__item")
	for i in a:
		url = i.attrs['href']
		cat =  i.find(class_='full-title').text
		categories.append([url, cat])

	fields = ['url', 'category']
	with open('who_categogies.csv','w') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerow(fields)
		w.writerows(categories)

def getQA(url, category):
	QA = []
	today = date.today().strftime("%d/%m/%Y")
	_page = _root + url 
	html = download(_page) 
	soup = BeautifulSoup(html,"html.parser") 
	q = soup.find_all(class_="sf-accordion__link")
	a = soup.find_all(class_="sf-accordion__content")
	i = 0
	for e in zip(q, a):
		qe = regex.sub("", e[0].text).strip()
		ae = regex.sub("", e[1].find('p').text).strip()
		QA.append([today, _page, category, qe, ae])  # question

	with open('who_qapairs.csv','a') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerows(QA)

##############
# CDC
# Method 1: https://www.cdc.gov/coronavirus/2019-ncov/faq.html
##############

def extractFAQCDC1():
	_page = 'https://www.cdc.gov/coronavirus/2019-ncov/faq.html'
	html = download(_page) 
	soup = BeautifulSoup(html,"html.parser") 

	#row = soup.find_all(class_="col-md-12")
	blocks = soup.find_all(class_="accordion indicator-plus accordion-white mb-3")
	QA_cdc = []
	for i in range(len(blocks)):
		questions = blocks[i].find_all(class_='card-title')
		answers = blocks[i].find_all(class_='card-body')
		for j in range(len(questions)):
			qe = regex.sub(" ", questions[j].text).strip()
			ae = regex.sub(" ", answers[j].text).strip()
			QA_cdc.append([date.today().strftime("%d/%m/%Y"), _page, i, qe, ae])

	# update category
	categoryCDC = soup.find_all(name='h2')  # only category
	for i in range(len(QA_cdc)):
		QA_cdc[i][2] = categoryCDC[QA_cdc[i][2]].text

	# Guardar QA pairs:
	fields = ['date', 'url', 'category', 'question', 'answer']
	with open('cdc_qapairs.csv','w') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerow(fields)
		w.writerows(QA_cdc)


########
# Method 2: from categories
########
def extractFAQCDC2():
	_root = 'https://faq.coronavirus.gov/'
	pageList = ['spread-transmission','covid-19-facts', 'food-drug-safety',
	'symptoms-and-testing', 'treatments-vaccines-immunity',
	'protect-yourself', 'cleaning-disinfecting-sanitizing',
	'pets-animals', 'caring-for-children', 'pregnancy', 'underlying-conditions',
	'activities-events-gatherings', 'workplace-safety',
	'travel', 'financial-help', 'food-housing-education-assistance', 'school-meals',
	'support-for-business']
	QA_cdc = []
	for p in pageList:
		category = p.replace('-', ' ').title()
		page = _root + p
		html = download(page) 
		soup = BeautifulSoup(html,"html.parser") 
		blocks = soup.find_all(class_="usa-accordion usa-accordion--bordered")
		for i in range(len(blocks)):
			questions = blocks[i].find_all(name='button')
			answers = blocks[i].find_all(class_='usa-accordion__content usa-prose')
			for j in range(len(questions)):
				qe = regex.sub(" ", questions[j].text).strip()
				ae = regex.sub(" ", answers[j].text).strip()
				QA_cdc.append([date.today().strftime("%d/%m/%Y"), page, category, qe, ae])


	# Save results
	fields = ['date', 'url', 'category', 'question', 'answer']
	with open('cdc_qapairs19dic.csv','w') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerow(fields)
		w.writerows(QA_cdc)



###########
# CNN: https://edition.cnn.com/interactive/2020/health/coronavirus-questions-answers/
##########

def extractFAQCNN():
	_page = 'https://edition.cnn.com/interactive/2020/health/coronavirus-questions-answers/'
	_date = ''
	regex = re.compile(r'[\n\r\t]')
	QA_cnn = []
	html = download(_page) 
	soup = BeautifulSoup(html,"html.parser") 
	blocksQ = soup.find_all(class_="question-q")
	blocksA = soup.find_all(class_="question-a")
	blocksC = soup.find_all(class_="question-t")
	lenQA = len(blocksQ)
	for i in range(lenQA):
		blocksc = blocksC[i].find_all(name="span")
		blocksc = [c.text for c in blocksc]
		blocksc = ";".join(blocksc)
		QA_cnn.append([date.today().strftime("%d/%m/%Y"), _page, blocksc, blocksQ[i].text, blocksA[i].text])

	# Guardar QA pairs:
	fields = ['date', 'url', 'category', 'question', 'answer']
	with open('cnn_qapairs.csv','w') as f:
		w = csv.writer(f, quoting=csv.QUOTE_ALL, quotechar='"')
		w.writerow(fields)
		w.writerows(QA_cnn)