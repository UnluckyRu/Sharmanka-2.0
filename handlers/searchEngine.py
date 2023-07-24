import re
import yt_dlp
import requests

YDL_OPTIONS_URL = {
   'format': 'bestaudio/best',
   'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
   'ignoreerrors': True,
   'no_warnings': True,
}

class ExtractManager():   
   def getFromURL(self, sourceUrl: str = '') -> dict:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=sourceUrl, download=False)

      self.audioData = dict([('title', self.intermidiateData['title']),
                             ('author', self.intermidiateData['channel']),
                             ('duration', self.intermidiateData['duration_string']),
                             ('thumbnail', self.intermidiateData['thumbnail'].replace('maxresdefault', 'default')),
                             ('audioSource', self.intermidiateData['url'])])

      return self.audioData

   def getFromText(self, textSource: str = '') -> dict:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=f'ytsearch:{textSource}', download=False)['entries'][0]

      self.audioData = dict([('title', self.intermidiateData['title']),
                             ('author', self.intermidiateData['channel']),
                             ('duration', self.intermidiateData['duration_string']),
                             ('thumbnail', self.intermidiateData['thumbnail'].replace('maxresdefault', 'default')),
                             ('audioSource', self.intermidiateData['url'])])
      
      return self.audioData
   
   def getFromPlaylist(self, playlistSource: str = '') -> list[dict[str]]:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=playlistSource, download=False)

      self.playlistData = {'title': self.intermidiateData['title'], 
                           'thumbnail': self.intermidiateData['thumbnails'][0]['url'], 
                           'playlist': [dict([('title', s['title']), 
                                             ('author', s['channel']), 
                                             ('duration', s['duration_string']), 
                                             ('thumbnail', s['thumbnail'].replace('maxresdefault', 'default')), 
                                             ('audioSource', s['url'])]) for i, s in enumerate(self.intermidiateData['entries']) if s is not None]}
      
      return self.playlistData

class SearchManager(ExtractManager):
   def __init__(self) -> None:
      self.requestsList = []

   def filterQuery(self, initialRequest: str = '') -> str:
      self.convertionAlphabet = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

      self.replacingString = (initialRequest.replace('\n', '')).replace(' ', '+')
      self.translatedString = self.replacingString.translate({ord(a):ord(b) for a, b in zip(*self.convertionAlphabet)})
      
      return self.translatedString

   def audioSearch(self, searchQuery: str = '') -> dict | None:
      self.processedRequest = self.filterQuery(searchQuery)

      if re.match(r"http.://", self.processedRequest) is not None: 
         return self.getFromURL(sourceUrl=self.processedRequest)
      else:
         return self.getFromText(textSource=self.processedRequest)
   
   def audioList(self, searchQuery: str = '') -> list[dict[str]]:
      self.processedRequest = self.filterQuery(searchQuery)
      
      self.findRequest = requests.get(f"https://www.youtube.com/results?search_query={self.processedRequest}").text
      self.gettingResponse = re.findall(r"watch\?v=(\S{11})", self.findRequest)
      self.sortedUrls = ['https://www.youtube.com/watch?v='+ i for n, i in enumerate(self.gettingResponse) if i not in self.gettingResponse[:n]][:10]

      for i in range(len(self.sortedUrls)):
         self.requestsList.append(requests.get(f'https://noembed.com/embed?dataType=json&url={self.sortedUrls[i]}').json())

      self.titlesList = [self.requestsList[n]['title'] for n in range(len(self.sortedUrls))]
      self.authorsList = [self.requestsList[n]['author_name'] for n in range(len(self.sortedUrls))]

      self.audioSource = [dict([('title', self.titlesList[i]), ('author', self.authorsList[i]), ('url', self.sortedUrls[i])]) for i in range(len(self.sortedUrls))]

      return self.audioSource
