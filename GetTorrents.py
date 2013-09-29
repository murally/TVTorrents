# Jai Ganesha!

import vobject
import urllib2
import dateutil
import datetime
from datetime import datetime
import json
import time
import urllib
import os
from os import path


filename = 'd:\\next_episode_calendar.ics'
cal_url = 'http://next-episode.net/calendar.ics?u=murally&k=1035b737f0a8d8dc5cbf466de7920d59'
#torrent_query_url = 'http://fenopy.se/module/search/api.php?keyword=URL&limit=50&sort=peer&format=json'
torrent_query_url = 'http://isohunt.com/js/json.php?ihq=URL&sort=size&order=asc'
#torrent_query_url = 'http://isohunt.com/js/json.php?ihq=URL&rows=10&sort=size&order=desc'
torrent_job_url = 'http://127.0.0.1:12345/gui/?action=add-url&s='
maxsize = 400.00
minsize = 100.00

class GetTorrent(object):

	today = None
	logfile = None
	cal = None

	def __init__(self):
		self.today = datetime.today()
		nofile = os.path.exists(filename)

		if self.today.day == 1 or not nofile:
			urllib.urlretrieve(cal_url, filename)

	def initLogFile(self):

		self.logfile = open('d:\\Python27\\Torrent\\error.log','a+b')
		timenow = datetime.now()
		self.logfile.write("-"*50+"\r\n")
		self.logfile.write("Started on " + timenow.__str__()+"\r\n")
		self.logfile.write("-"*50+"\r\n")
		self.logfile.flush()

	def Log(self,str):

		self.logfile.write("\r\n"+str+"\r\n")
		self.logfile.flush()

	def obtainTorrentURL(self,event):

		# Extract summary to get show name and enclosure_URL

		summary = event.summary.value
		showname = summary.rsplit(' -')[0]
		showname = showname.replace(' ','+')
		epis = summary.rsplit('- ')[1]
		season = self.getFormattedString(epis.rsplit('x')[0],'S')
		episode = self.getFormattedString(epis.rsplit('x')[1],'E')

		torrent_query = showname + '+' + season + episode
		torrent_query = torrent_query_url.replace('URL',torrent_query)
		self.Log( "Sending "+ torrent_query)

		urlRet = self.openURL(torrent_query)
		json_data = json.load(urlRet)

		if json_data is not None:
			return self.getBestTorrentURL(json_data,season+episode)
		else:
			self.Log( "Something went wrong here in getting the torrent URL")

	def getBestTorrentURL(self,json_data,ep_info):
		
		items_list = json_data.get("items")
		if items_list is None:
			self.Log("No items for this episode")
			return None
		for i in json_data.get("items").get("list"):
			siz = i.get("size")
			if siz.find("GB") != -1 or siz.find("KB") != -1:
				continue
			siz = siz.replace(" MB","")

			# I don't wanna download huge files..Can't wait!
			# At the same time, I don't want crappy files.

			if float(siz) < maxsize and float(siz) > minsize:
				title = i.get("title")

				# Match episode id in title just to sure..torrent search
				# queries tend to return junk

				if title.find(ep_info) == -1:
					continue
				else:
					return i.get("enclosure_url")

	def launchTorrentDownloadJob(self,torrent_url):

		job_url = torrent_job_url + torrent_url
		ret = self.openURL2(job_url)
		if ret is None:
			self.Log( "Couldn't launch job even after retries")
			self.Log( "Check URL and command and service")

	def openURL2(self, url):

		password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
		top_level_url = "http://127.0.0.1:12345/gui/"
		password_mgr.add_password(None, top_level_url, 'admin', 'admin123')
		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		ret = opener.open(url)
		urllib2.install_opener(opener)

		retryCount = 0
		if ret.getcode() != 200:
			retryCount+= 1
			while retryCount <= 5:
				self.Log( 'Something went wrong with '+ job_url )
				self.Log( 'Retry count '+retryCount)
				time.sleep(retryCount * 30)
				ret = urllib.urlopen(torrent_query)
				if ret.getcode() == 200:
					break
				else: 
					continue

			if retryCount > 5:
				self.Log( 'Couldnt get torrent results even after 5 retries')
				self.Log( 'aborting now')
				return None
		return ret

	def openURL(self,query):
		ret = urllib.urlopen(query)
		retryCount = 0
		if ret.getcode() != 200:
			retryCount+= 1
			while retryCount <= 5:
				self.Log( 'Something went wrong with '+ job_url )
				self.Log( 'Retry count '+retryCount)
				time.sleep(retryCount * 30)
				ret = urllib.urlopen(torrent_query)
				if ret.getcode() == 200:
					break
				else: 
					continue

			if retryCount > 5:
				self.Log( 'Couldnt get torrent results even after 5 retries')
				self.Log( 'aborting now')
				return None

		return ret

	def getFormattedString(self,var,prefix):
		if int(var) < 10:
			var = prefix + '0' + var
		else: 
			var = prefix + var

		return var

	def processICal(self):

		# Read the ics file

		inpdata = open(filename)
		cal = vobject.readOne(inpdata)

		# Go through each event

		for evt in cal.vevent_list:
			caldt = evt.dtstart.value

			torrent_url = None
			if self.today.day == caldt.day:
				torrent_url = self.obtainTorrentURL(evt)

			if torrent_url is not None:
				self.launchTorrentDownloadJob(torrent_url)
			else:
				continue


if __name__ == '__main__':

	worker = GetTorrent()
	worker.initLogFile()
	worker.processICal()
	worker.logfile.close()

