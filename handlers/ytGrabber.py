import os
import re
import json
import js2py
import aiohttp

import time
import asyncio

from urllib.parse import unquote
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_KEY = os.environ.get('YOUTUBE_API_TOKEN')

try:
   from handler import TimeHandler, YoutubeUpdate
except:
   from .handler import TimeHandler, YoutubeUpdate

class YtEngine(YoutubeUpdate):
   def __init__(self) -> None:
      super().__init__()
      self.audioSources = []
      self.playlistTracks = []
      self.videosIDs = []

      self.HEADERS = {
         'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'),
         'referer': 'https://youtube.com',
         "x-youtube-client-version": '2.20231020.00.01',
         'x-youtube-client-name': "1",
      }

      with open('handlers/algorithmData.json', encoding='UTF-8') as file:
         self.jsonData = json.load(file)

   async def getTrackData(self, videoID: str = None) -> list:
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'https://youtube.com/watch?v={videoID}&pbj=1') as response:
            self.baseRequest = await response.json()

      self.metaData = self.baseRequest[2]['playerResponse']['videoDetails']
      self.playableData = self.baseRequest[2]['playerResponse']['streamingData']['adaptiveFormats'][-1]

      self.title = self.metaData['title']
      self.uploaderName = self.metaData['author']
      self.thumbnailLink = self.metaData['thumbnail']['thumbnails'][-1]['url']
      self.trackDuration = TimeHandler().timeConverter(self.metaData['lengthSeconds'])
      
      try:
         completeUrl = self.playableData['url']
      except KeyError:
         encodeSignature = self.playableData['signatureCipher']
         signature, _, rawUrl = encodeSignature.split('&')
         rawUrl = unquote(rawUrl.replace('url=', '')).split('Clmt')
         signature = unquote(signature.replace('s=', ''))

         decodeSignature = js2py.eval_js(self.jsonData['algorithm'])
         completeUrl = f"{rawUrl[0]}Clmt&sig={unquote(decodeSignature(signature))}{rawUrl[-1]}"
      
      return [[self.title, self.uploaderName, self.trackDuration, self.thumbnailLink], completeUrl]

   async def getPlaylistMetadata(self, playlistID: str = None) -> list:
      async with aiohttp.ClientSession() as session:
         async with session.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={playlistID}&key={API_KEY}') as response:
            self.snippetData = await response.json()

      self.metaData = self.snippetData['items'][0]['snippet']

      self.title = self.metaData['title']
      self.thumbnail = self.metaData['thumbnails']['high']['url']

      return [self.title, self.thumbnail]

   async def getSingleAudio(self, sourceUrl: str = None):
      videoID = sourceUrl.split('watch?v=')[-1]
      self.trackData, self.audioSource = await self.getTrackData(videoID)

      return {'rawSource': sourceUrl,
              'title': self.trackData[0],
              'author': self.trackData[1],
              'duration': self.trackData[2],
              'thumbnail': self.trackData[3],
              'audioSource': self.audioSource}

   async def getPlaylistAudios(self, sourceUrl: str = None):
      self.sortingList = []
      self.taskManager = []

      if sourceUrl.find('?list=') != -1:
         playlistID = sourceUrl.split('?list=')[-1]
      if sourceUrl.find('&list=') != -1:
         playlistID = sourceUrl.split('&list=')[-1]

      async with aiohttp.ClientSession() as session:
         async with session.get(f'https://www.youtube.com/playlist?list={playlistID}') as response:
            self.playlistRequests = await response.text()
            
      self.videosIDs = (re.findall(r'watch\?v=(\S{11})', self.playlistRequests))
      [self.sortingList.append(ID) for ID in self.videosIDs if ID not in self.sortingList]
      self.videosIDs = self.sortingList
      
      self.presentData = await self.getPlaylistMetadata(playlistID)

      for _, videoId in enumerate(self.videosIDs):
         self.taskManager.append(asyncio.create_task(self.getTrackData(videoId)))
      self.extractInfo = await asyncio.gather(*self.taskManager)
      
      for _, source in enumerate(self.extractInfo):
         self.playlistTracks.append({'title': source[0][0], 
                                     'duration': source[0][2], 
                                     'audioSource': source[1]})

      return {'rawSource': sourceUrl, 
              'title': self.presentData[0], 
              'thumbnail': self.presentData[1], 
              'playlist': self.playlistTracks}

   async def getTextToAudio(self, sourceQuery: str = None):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'https://youtube.com/results?search_query={sourceQuery}&pbj=1') as response:
            self.requestsTextInfo = await response.json()

      self.requestsTextInfo = self.requestsTextInfo[1]['response']['contents']

      try:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['videoId']
      except KeyError:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][1]['videoRenderer']['videoId']

      self.trackData, self.audioSource = await self.getTrackData(videoID)

      return {'rawSource': f'https://www.youtube.com/watch?v={videoID}',
              'title': self.trackData[0],
              'author': self.trackData[1],
              'duration': self.trackData[2],
              'thumbnail': self.trackData[3],
              'audioSource': self.audioSource}

   async def getLiveAudio(self, getData: dict = None):
      return getData['streamingData']['hlsManifestUrl']

   async def getLiveStream(self, sourceUrl: str = None, loop = None):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'{sourceUrl}&pbj=1') as response:
            self.completeData = await response.json()

      self.completeData = self.completeData[2]['playerResponse']
      self.streamData = self.completeData['videoDetails']
      self.audioSource = await loop.run_in_executor(None, lambda: self.getLiveAudio(self.completeData))

      return {'rawSource': sourceUrl[0],
              'title': self.streamData['title'],
              'author': self.streamData['author'],
              'duration': 'LIVE',
              'thumbnail': self.streamData['thumbnail']['thumbnails'][-1]['url'],
              'audioSource': self.audioSource}
   
   async def getManyAudios(self, textSource: str = None, tracksAmount: int = None):
      if tracksAmount is None: tracksAmount = 10
      self.audioSources = []

      self.DATA = {
         "query": f"{textSource}",
         "params": "EgIQAQ%3D%3D",
         "context": {"client": {"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, "thirdParty": {"embedUrl": "https://www.youtube.com"}},
         "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": f"{self.jsonData['timestamp']}"}}}

      async with aiohttp.ClientSession() as session:
         async with session.post(f'https://www.youtube.com/youtubei/v1/search?key={self.jsonData["download_key"]}', json=self.DATA) as response:
            self.requestsTextInfo = await response.json()

      self.requestsTextInfo = self.requestsTextInfo['contents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

      for i in range((tracksAmount)):
         try:
            self.audioSources.append({'title': self.requestsTextInfo[i]['compactVideoRenderer']['title']['runs'][0]['text'], 
                                    'author': self.requestsTextInfo[i]['compactVideoRenderer']['longBylineText']['runs'][0]['text'], 
                                    'url': f"https://www.youtube.com/watch?v={self.requestsTextInfo[i]['compactVideoRenderer']['videoId']}",})
         except IndexError:
            break
         
      return self.audioSources

class YtGrabber(YtEngine):
   def __init__(self) -> None:
      super().__init__()

   async def getFromYoutube(self, sourceQuery: str = None, queryType: str = None, tracksAmount: int = None, loop = None):
      match queryType:
         case 'linkSource':
            self.intermidiateData = await self.getSingleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = await self.getPlaylistAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = await self.getTextToAudio(sourceQuery)
         case 'bulkRequests':
            self.intermidiateData = await self.getManyAudios(sourceQuery, tracksAmount)
         case 'liveSource':
            self.intermidiateData = await self.getLiveStream(sourceQuery, loop)

      return [queryType, self.intermidiateData]

# start = time.time()
# print(asyncio.run(YtGrabber().getFromYoutube('https://www.youtube.com/watch?v=8GW6sLrK40k', 'linkSource')))
# print(time.time() - start)