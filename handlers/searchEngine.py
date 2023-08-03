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
   def getFromSource(self, sourceQuery: str = '', queryType: str = '') -> dict:
      match queryType:
         case 'linkSource':
            self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=sourceQuery, download=False)
         case 'textSource':
            self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=f'ytsearch:{sourceQuery}', download=False)['entries'][0]
      
      print('\n')
      self.audioData = dict([('title', self.intermidiateData['title']),
                             ('author', (self.intermidiateData.get('channel') or self.intermidiateData.get('uploader'))),
                             ('duration', self.intermidiateData['duration_string']),
                             ('thumbnail', self.intermidiateData['thumbnail'].replace('maxresdefault', 'default')),
                             ('audioSource', self.intermidiateData['url']),
                             ('rawSource', self.intermidiateData['original_url'])])

      return self.audioData
   
   def getFromPlaylist(self, playlistSource: str = '') -> list[dict[str]]:
      self.intermidiateData = yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url=playlistSource, download=False)
      print('\n')

      self.playlistData = {'title': self.intermidiateData['title'], 
                           'thumbnail': self.intermidiateData['entries'][0]['thumbnails'][0]['url'], 
                           'playlist': [dict([('title', s['title']), 
                                             ('author', s.get('channel') or s.get('uploader')), 
                                             ('duration', s['duration_string']), 
                                             ('thumbnail', s['thumbnail'].replace('maxresdefault', 'default')), 
                                             ('audioSource', s['url'])]) for i, s in enumerate(self.intermidiateData['entries']) if s is not None]}
      
      return self.playlistData

class SearchManager(ExtractManager):
   def __init__(self, searchQuery: str = '') -> None:
      self.convertionAlphabet = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
      self.searchQuery = self.filterQuery(searchQuery)

   def filterQuery(self, initialRequest: str = '') -> str:
      self.replacingString = (initialRequest.replace('\n', '')).replace(' ', '+')
      self.translatedString = self.replacingString.translate({ord(a):ord(b) for a, b in zip(*self.convertionAlphabet)})
      return self.translatedString

   def findAudio(self) -> dict | list[dict[str]]:
      match re.match(r"http.://", self.searchQuery):
         case None:
            return self.getFromSource(sourceQuery=self.searchQuery, queryType='textSource')
         case _:
            match re.search(r"&list=", self.searchQuery) or re.search(r"/sets/", self.searchQuery):
               case None:
                  return self.getFromSource(sourceQuery=self.searchQuery, queryType='linkSource')
               case _:
                  return self.getFromPlaylist(playlistSource=self.searchQuery, queryType='Playlist')
   
   async def audioList(self) -> list[dict[str]]:
      start = time.time()
      async with aiohttp.ClientSession() as session:
         async with session.get(f"https://www.youtube.com/results?search_query={self.searchQuery}") as response:
            self.findRequest = re.findall(r"watch\?v=(\S{11})", await response.text())

      self.sortedUrls = [f'https://www.youtube.com/watch?v={id}' for index, id in enumerate(self.findRequest) if id not in self.findRequest[:index]][:10]
      self.getInfoUrls = [f'https://noembed.com/embed?dataType=json&url={self.sortedUrls[index]}' for index, _ in enumerate(self.sortedUrls)]

      async with aiohttp.ClientSession() as session:
         self.preTask = await asyncio.gather(*[session.get(self.getInfoUrls[index]) for index, _ in enumerate(self.getInfoUrls)])
         self.fullTask = await asyncio.gather(*[source.json(content_type=None) for _, source in enumerate(self.preTask)])

      self.titlesList = [infoString['title'] for _, infoString in enumerate(self.fullTask)]
      self.authorsList = [infoString['author_name'] for _, infoString in enumerate(self.fullTask)]
      self.audioSource = [dict([('title', self.titlesList[i]), ('author', self.authorsList[i]), ('url', self.sortedUrls[i])]) for i, _ in enumerate(self.sortedUrls)]
      print(f'Request complite for: {time.time()-start}')
   
      return self.audioSource
   