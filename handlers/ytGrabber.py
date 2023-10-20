import re
import yt_dlp
import aiohttp
import asyncio
import concurrent.futures

class YtEngine():
   def __init__(self) -> None:
      self.YDL_OPTIONS_URL = {'ignoreerrors': True, 
                              'no_warnings': True, 
                              'format': 'bestaudio/best', 
                              'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': '192'}],
                              'cookies-from-browser': 'chrome',
                              'quiet': True,}

   def getAudioData(self, audioID):
      self.audioData = yt_dlp.YoutubeDL(self.YDL_OPTIONS_URL).extract_info(f'https://www.youtube.com/watch?v={audioID}', download=False)
      return {'title': self.audioData.get('title'), 'duration': self.audioData.get('duration_string'), 'audioSource': self.audioData.get('url')}

   async def audioList(self) -> list[dict[str]]:
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
   
      return self.audioSource
   
   async def extractPlaylist(self, sourceQuery: str = ''):
      self.playlistTracks: list = []
      self.playlistHeader: dict = {}

      async with aiohttp.ClientSession() as session:
         async with session.get(sourceQuery) as response:
            audioIDS = list(set(re.findall(r"watch\?v=(\S{11})", await response.text())))

      with concurrent.futures.ThreadPoolExecutor() as executor:
         self.threadsData = [executor.submit(self.getAudioData, audioID) for audioID in audioIDS[:50]]

      for _, source in enumerate(self.threadsData):
         try:
            self.playlistTracks.append(source.result())
         except:
            ...

      async with aiohttp.ClientSession() as session:
         async with session.get(f'https://www.youtube.com/oembed?url={sourceQuery}') as response:
            self.playlistHeader = await response.json()
      
      return {'rawSource': sourceQuery, 'title': self.playlistHeader['title'], 'thumbnail': self.playlistHeader['thumbnail_url'], 'playlist': self.playlistTracks}

class YtGrabber(YtEngine):
   def __init__(self) -> None:
      super().__init__()

   async def getFromSource(self, sourceQuery: str = '', queryType: str = '', *, loop = None) -> [str, dict]:
      match queryType:
         case 'linkSource':
            self.intermidiateData = yt_dlp.YoutubeDL(self.YDL_OPTIONS_URL).extract_info(url=sourceQuery, download=False)
         case 'textSource':
            self.intermidiateData = yt_dlp.YoutubeDL(self.YDL_OPTIONS_URL).extract_info(url=f'ytsearch:{sourceQuery}', download=False)['entries'][0]
         case 'liveSource':
            self.loop = loop or asyncio.get_event_loop()
            self.intermidiateData = await self.loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(self.YDL_OPTIONS_URL).extract_info(url=sourceQuery, download=False))
            
      match queryType: 
         case 'playlist':
            self.audioData = await self.extractPlaylist(sourceQuery)

         case 'linkSource' | 'textSource':
            self.audioData = {'rawSource': self.intermidiateData['original_url'],
                              'title': self.intermidiateData['title'],
                              'author': self.intermidiateData.get('channel') or self.intermidiateData.get('uploader'),
                              'duration': self.intermidiateData.get('duration_string') or 'LIVE',
                              'thumbnail': self.intermidiateData['thumbnail'].replace('maxresdefault', 'default'),
                              'audioSource': self.intermidiateData['url']}

      return [queryType, self.audioData]

#asyncio.run(YtGrabber().getFromSource('https://www.youtube.com/watch?v=LAUIqLDI6i4&list=PLC1og_v3eb4jyYjXlkdAyAMURj7kTcddQ', 'playlist'))