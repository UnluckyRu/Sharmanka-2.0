import re
import urllib
import yt_dlp
import requests

import time
from datetime import datetime

YDL_OPTIONS_SEARCH = {
   'format': 'bestaudio/best', 
   'noplaylist': 'True', 
   'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
   'noplaylist': True,
   'ignoreerrors': False,
   'no_warnings': True,
   'default_search': 'auto',
   'source_address': '0.0.0.0'
   }

YDL_OPTIONS_URL = {
   'format': 'bestaudio/best', 
   'noplaylist': 'True', 
   'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
   }

def debugWriter(data: any) -> None:
   with open(f'file_{datetime.now().strftime("%H%M%S")}.txt', 'w', encoding='utf-8') as file:
      file.write(str(data))
      file.close()
      print('Done!')

class YTDLSource():
   def __init__(self) -> None:
      self.audioObject = []

   def __getDownloadableLinks(self, searchSource: str = '') -> tuple:
      self.searchSource = searchSource.replace('\n', '')
      self.filteredSearch = ''.join(letter for letter in self.searchSource if letter.isalpha())
      self.symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
      self.completeString = self.filteredSearch.translate({ord(a):ord(b) for a, b in zip(*self.symbols)}).replace(' ', '+')

      #start = time.time()
      self.findRequest = requests.get(f"https://www.youtube.com/results?search_query={self.completeString}").text
      self.gettingResponse = re.findall(r"watch\?v=(\S{11})", self.findRequest)
      self.sortedID = ['https://www.youtube.com/watch?v='+ i for n, i in enumerate(self.gettingResponse) if i not in self.gettingResponse[:n]][:10]
      self.titlesList = [requests.get(f'https://noembed.com/embed?dataType=json&url={self.sortedID[n]}').json()['title'] for n in range(len(self.sortedID))]
      #print(time.time()-start)

      return [self.sortedID, self.titlesList]

   def _fromUrl(self, urlSource: str = '') -> dict:
      self.executableData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=urlSource, download=False)

      self.audioObject = {'title': self.executableData['title'], 
                        'duration': self.executableData['duration_string'], 
                        'audioLink': self.executableData['url'],
                        'thumbnail': self.executableData['thumbnail'].replace('maxresdefault', 'default')}
      
      return self.audioObject
      
   def _fromSearch(self, searchSource: str = '') -> dict:
      self.sortedID, _ = self.__getDownloadableLinks(searchSource)

      print(self.sortedID)

      self.executableData = yt_dlp.YoutubeDL(YDL_OPTIONS_SEARCH).extract_info(url=self.sortedID[0], download=False)
      #debugWriter(data=self.executableData)
      
      self.audioObject = {'title': self.executableData['title'], 
                        'duration': self.executableData['duration_string'], 
                        'audioLink': self.executableData['url'],
                        'thumbnail': self.executableData['thumbnail'].replace('maxresdefault', 'default')}
      
      return self.audioObject
   
   def _fromLists(self, searchSource: str = '') -> list:
      self.sortedID, self.titlesList = self.__getDownloadableLinks(searchSource)

      for index in range(len(self.sortedID)):
         self.audioObject.append({'rawLink': self.sortedID[index], 'title': self.titlesList[index]})

      return self.audioObject

class SearchEngine():
   def audioExtract(self, typeSearch: str = '', baseRequest: str = '') -> str:
      match typeSearch:
         case 'play':
            if re.match(r"http.://", baseRequest) is not None: 
               return YTDLSource()._fromUrl(url=baseRequest)
            else: 
               return YTDLSource()._fromSearch(search=baseRequest)            
         case 'search':
            return YTDLSource()._fromLists(searchSource=baseRequest)
      
#print(YTDLSource()._fromLists(searchSource='Хом - резонанс'))
