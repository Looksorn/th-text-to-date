from django.shortcuts import render
from django.http import HttpResponse

import requests
import os

from pythainlp.tokenize import dict_word_tokenize
import calendar
from datetime import *
from dateutil.relativedelta import *
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

now = datetime.now()

shortTimelist=['วันนี้','พรุ่งนี้','มะรืน','เมื่อวาน']
prefixTimelist=['ช่วง','วันที่']
rangeTimelist=['ถึง','จนถึง','-']
unitTimelist=['วัน','สัปดาห์','เดือน','ปี']
sufTimelist=['ก่อน','ที่แล้ว','หน้า','ข้างหน้า']

number_dict={'หนึ่ง':1,'สอง':2,'สาม':3,'สี่':4,'ห้า':5,'หก':6,'เจ็ด':7,'แปด':8,'เก้า':9,'สิบ':10,'สิบเอ็ด':11,'สิบสอง':12,'สิบสาม':13,'สิบสี่':14,'สิบห้า':15,'สิบหก':16,'สิบเจ็ด':17,'สิบแปด':18,'สิบเก้า':19,'ยี่สิบ':20,'ยี่สิบเอ็ด':21,'ยี่สิบสอง':22,'ยี่สิบสาม':23,'ยี่สิบสี่':24,'ยี่สิบห้า':25,'ยี่สิบหก':26,'ยี่สิบเจ็ด':27,'ยี่สิบแปด':28,'ยี่สิบเก้า':29,'สามสิบ':30,'สามสิบเอ็ด':31}
month_dict={'ม.ค.':1,'ก.พ.':2,'มี.ค.':3,'เม.ย.':4,'พ.ค.':5,'มิ.ย.':6,'ก.ค.':7,'ส.ค.':8,'ก.ย.':9,'ต.ค.':10,'พ.ย.':11,'ธ.ค.':12}

def tokenize(token,json_token,time_list):
	prefix,num,unit,suffix=None,None,None,None
	time_token=[None,1,None,1]
	for i in range(len(token)):
		for j in shortTimelist:
			if token[i]==j:
				time_token[2]=token[i]
				json_token.append(token[i])
				time_list.append(time_token)
				prefix,num,unit,suffix=None,None,None,None
				time_token=[None,1,None,1]
		for k in prefixTimelist:
			if token[i]==k:
				prefix=i
		if type(token[i]) is int:
			num=i
			if (token[i-1]=='วันที่'):
				temp=token[i-1]+str(token[i])
				time_token[0]=token[i-1]
				time_token[1]=token[i]
				try:
					time_token[2]=month_dict[token[i+1]]
					temp=temp+token[i+1]
				except:
					pass
				json_token.append(temp)
				time_list.append(time_token)
				prefix,num,unit,suffix=None,None,None,None
				time_token=[None,1,None,1]
		for l in unitTimelist:
			if token[i]==l:
				unit=i
				if token[i+1]=='นี้':
					json_token.append(token[i]+token[i+1])
					if token[i]!='วัน':
						time_token[0]='ช่วง'
					time_token[1]=0
					time_token[2]=token[i]
					time_list.append(time_token)
					prefix,num,unit,suffix=None,None,None,None
					time_token=[None,1,None,1]
		for m in sufTimelist:
			if token[i]==m:
				suffix=i
		for n in rangeTimelist:
			if token[i]==n:
				if time_list[-1][0]=='วันที่' and type(token[i+1]) is int:
					temp='-'+str(token[i+1])
					time_list[-1][0]='ช่วง'
					time_list[-1][3]=token[i+1]
					try:
						temp=temp+token[i+2]
						time_list[-1].append(month_dict[token[i+2]])
					except:
						pass
					json_token[-1]=json_token[-1]+temp
		if unit!=None and suffix!=None and suffix-unit==1:
			temp=''
			if prefix!=None and num!=None:
				if num-prefix==1 and unit-num==1:
					temp=token[prefix]+str(token[num])
					time_token[0]=token[prefix]
					time_token[1]=token[num]
				elif unit-num==1:
					temp=str(token[num])
					time_token[1]=token[num]
			elif prefix!=None and num==None:
				if unit-prefix==1:
					temp=token[prefix]
					time_token[0]=token[prefix]
			elif prefix==None and num!=None:
				if unit-num==1:
					temp=str(token[num])
					time_token[1]=token[num]
			temp=temp+token[unit]+token[suffix]
			time_token[2]=token[unit]
			if token[suffix]=='ข้างหน้า' or token[suffix]=='หน้า':
				time_token[3]=-1
			json_token.append(temp)
			time_list.append(time_token)
			prefix,num,unit,suffix=None,None,None,None
			time_token=[None,1,None,1]

def shortTime(time_token):
	if time_token[2] == 'วันนี้':
		return now
	elif time_token[2] == 'พรุ่งนี้':
		return now+relativedelta(days=1)
	elif time_token[2] == 'มะรืน':
		return now+relativedelta(days=2)
	elif time_token[2] == 'เมื่อวาน':
		return now+relativedelta(days=-1)
	elif time_token[2] == 'วัน':
		return now+relativedelta(days=-time_token[1]*time_token[3])
	elif time_token[2] == 'สัปดาห์':
		return now+relativedelta(weeks=-time_token[1]*time_token[3])
	elif time_token[2] == 'เดือน':
		return now+relativedelta(months=-time_token[1]*time_token[3])
	elif time_token[2] == 'ปี':
		return now+relativedelta(years=-time_token[1]*time_token[3])
	elif time_token[0] == 'วันที่':
		try:
			return datetime(now.year,time_token[2],time_token[1])
		except:
			return datetime(now.year,now.month,time_token[1])

def daterange(time_token,date):
	flage=0
	dt_rage=[]
	cal=calendar.Calendar()
	if date is None:
		yeardate=now
		try:
			start_date=datetime(now.year,time_token[2],time_token[1])
		except:
			try:
				start_date=datetime(now.year,time_token[4],time_token[1])
			except:
				start_date=datetime(now.year,now.month,time_token[1])
		try:
			end_date=datetime(now.year,time_token[4],time_token[3])
		except:
			end_date=datetime(now.year,now.month,time_token[3])
	else:
		yeardate=date
		if int((now-date).days)>0:
			start_date=date
			end_date=now+relativedelta(days=-1)
		else:
			start_date=now+relativedelta(days=1)
			end_date=date
	for year in cal.yeardatescalendar(yeardate.year, 1):
		for month in year:
			for week in month:
				for day in week:
					for dt in dt_rage:
						if day==dt:
							flage=1
					if flage==0:
						if time_token[2] == 'วัน' or date is None:
							if int((day-start_date.date()).days)>=0 and int((end_date.date()-day).days)>=0:
								dt_rage.append(day)
						elif time_token[2] == 'สัปดาห์':
							if day == date.date():
								return week
						elif time_token[2] == 'เดือน':
							if day.month == date.date().month:
								dt_rage.append(day)
						elif time_token[2] == 'ปี':
							if day.year == date.date().year:
								dt_rage.append(day)
					flage=0
	return dt_rage

# Create your views here.
def index(request):
	token=[]
	time_token_list=[]
	data=[]
	userInput=request.GET.get('text')
	lm_token=dict_word_tokenize(userInput,file=os.path.join(BASE_DIR,"hello/wordlist.txt"),engine="longest-matching")
	for i in range(len(lm_token)):
		try:
			lm_token[i]=number_dict[lm_token[i]]
		except:
			pass
		try:
			lm_token[i]=int(lm_token[i])
		except:
			pass
	tokenize(lm_token,token,time_token_list)
	for n in range(len(token)):
		date=shortTime(time_token_list[n])
		if time_token_list[n][0]!='ช่วง':
			data.append({'token':token[n],'type':'single','date':date.strftime("%Y-%m-%d")})
		else:
			daterang=daterange(time_token_list[n],date)
			if daterang!=[]:
				data.append({'token':token[n],'type':'range','date':[dt.strftime("%Y-%m-%d") for dt in daterang]})
	json.dumps(data,ensure_ascii=False)
	return HttpResponse(data)