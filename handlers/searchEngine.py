import re
import yt_dlp
import aiohttp
import asyncio
import time

YDL_OPTIONS_URL = { 
   'ignoreerrors': True,
   'no_warnings': True,
   'format': 'bestaudio/best',
   'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
}

class ExtractManager():
   def getFromURL(self, sourceUrl: str = '') -> dict:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=sourceUrl, download=False)
      print('\n')

      self.audioData = dict([('title', self.intermidiateData['title']),
                             ('author', self.intermidiateData['channel']),
                             ('duration', self.intermidiateData['duration_string']),
                             ('thumbnail', self.intermidiateData['thumbnail'].replace('maxresdefault', 'default')),
                             ('audioSource', self.intermidiateData['url'])])

      return self.audioData

   def getFromText(self, textSource: str = '') -> dict:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=f'ytsearch:{textSource}', download=False)['entries'][0]
      print('\n')

      self.audioData = dict([('title', self.intermidiateData['title']),
                             ('author', self.intermidiateData['channel']),
                             ('duration', self.intermidiateData['duration_string']),
                             ('thumbnail', self.intermidiateData['thumbnail'].replace('maxresdefault', 'default')),
                             ('audioSource', self.intermidiateData['url'])])
      
      return self.audioData
   
   def getFromPlaylist(self, playlistSource: str = '') -> list[dict[str]]:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=playlistSource, download=False)
      print('\n')

      self.playlistData = {'title': self.intermidiateData['title'], 
                           'thumbnail': self.intermidiateData['thumbnails'][0]['url'], 
                           'playlist': [dict([('title', s['title']), 
                                             ('author', s['channel']), 
                                             ('duration', s['duration_string']), 
                                             ('thumbnail', s['thumbnail'].replace('maxresdefault', 'default')), 
                                             ('audioSource', s['url'])]) for i, s in enumerate(self.intermidiateData['entries']) if s is not None]}
      
      return self.playlistData

class SearchManager(ExtractManager):
   def __init__(self): ...

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
   
   async def audioList(self, searchQuery: str = '') -> list[dict[str]]:
      self.processedRequest = self.filterQuery(searchQuery)
      
      start = time.time()
      async with aiohttp.ClientSession() as session:
         async with session.get(f"https://www.youtube.com/results?search_query={self.processedRequest}") as response:
            self.findRequest = await response.text()

      self.gettingResponse = re.findall(r"watch\?v=(\S{11})", self.findRequest)
      self.sortedUrls = [f'https://www.youtube.com/watch?v={id}' for index, id in enumerate(self.gettingResponse) if id not in self.gettingResponse[:index]][:10]
      self.getInfoUrls = [f'https://noembed.com/embed?dataType=json&url={self.sortedUrls[index]}' for index, _ in enumerate(self.sortedUrls)]

      async with aiohttp.ClientSession() as session:
         self.preTask = await asyncio.gather(*[session.get(self.getInfoUrls[index]) for index, _ in enumerate(self.getInfoUrls)])
         self.fullTask = await asyncio.gather(*[source.json(content_type=None) for _, source in enumerate(self.preTask)])

      self.titlesList = [infoString['title'] for _, infoString in enumerate(self.fullTask)]
      self.authorsList = [infoString['author_name'] for _, infoString in enumerate(self.fullTask)]

      self.audioSource = [dict([('title', self.titlesList[i]), ('author', self.authorsList[i]), ('url', self.sortedUrls[i])]) for i, _ in enumerate(self.sortedUrls)]
      print(f'Request complite for: {format(time.time()-start, ".3f")}')

      return self.audioSource
