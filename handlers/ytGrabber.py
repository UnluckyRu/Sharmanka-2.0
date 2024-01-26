import os
import json
import js2py
import aiohttp
import asyncio

from urllib.parse import unquote
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_KEY = os.environ.get('YOUTUBE_API_TOKEN')

try:
   from handler import TimeHandler, YoutubeUpdate, AudioSample, PlaylistSample
except:
   from .handler import TimeHandler, YoutubeUpdate, AudioSample, PlaylistSample

class YtEngine(YoutubeUpdate):
   def __init__(self) -> None:
      super().__init__()
      self.audioSources = []
      self.playlistTracks = []
      self.sortingList = []
      self.taskManager = []
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
      self.trackDuration = TimeHandler.timeConverter(self.metaData['lengthSeconds'])
      
      try:
         completeUrl = self.playableData['url']
      except KeyError:
         encodeSignature = self.playableData['signatureCipher']
         signature, _, rawUrl = encodeSignature.split('&')
         rawUrl = unquote(rawUrl.replace('url=', '')).split('Clmt')
         signature = unquote(signature.replace('s=', ''))

         decodeSignature = js2py.eval_js(self.jsonData['algorithm'])
         completeUrl = f"{rawUrl[0]}Clmt&sig={unquote(decodeSignature(signature))}{rawUrl[-1]}"
      
      return [self.title, self.uploaderName, self.trackDuration, self.thumbnailLink, completeUrl]

   async def getLiveAudio(self, getData: dict = None):
      return getData['streamingData']['hlsManifestUrl']

   async def getSingleAudio(self, sourceUrl: str = None):
      try:
         videoID = sourceUrl.split('?si=')[0].split('https://youtu.be/')[1]
      except:
         videoID = sourceUrl.split('watch?v=')[-1]

      self.trackData = await self.getTrackData(videoID)
      return AudioSample(sourceUrl, self.trackData[0], self.trackData[1], self.trackData[2], self.trackData[3], self.trackData[4])

   async def getPlaylistAudios(self, sourceUrl: str = None):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'{sourceUrl}&pbj=1') as response:
            self.playlistRequests = await response.json()

      self.title = self.playlistRequests[3]['response']['contents']['twoColumnWatchNextResults']['playlist']['playlist']['title']
      self.thumbnial = self.playlistRequests[3]['response']['contents']['twoColumnWatchNextResults']['playlist']['playlist']['contents'][0]['playlistPanelVideoRenderer']['thumbnail']['thumbnails'][-1]['url']

      for _, source in enumerate(self.playlistRequests[3]['response']['contents']['twoColumnWatchNextResults']['playlist']['playlist']['contents']):
         try:
            self.videosIDs.append(source['playlistPanelVideoRenderer']['videoId'])
         except:
            continue

      for _, videoId in enumerate(self.videosIDs):
         self.taskManager.append(asyncio.create_task(self.getTrackData(videoId)))
      self.extractInfo = await asyncio.gather(*self.taskManager)

      for _, source in enumerate(self.extractInfo):
         self.playlistTracks.append(AudioSample(title=source[0], duration=source[2], audioSource=source[4]))
         
      return PlaylistSample(rawSource=sourceUrl, title=self.title, thumbnail=self.thumbnial, playlist=self.playlistTracks)
   
   async def getTextToAudio(self, sourceQuery: str = None):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'https://youtube.com/results?search_query={sourceQuery}&pbj=1') as response:
            self.requestsTextInfo = await response.json()

      self.requestsTextInfo = self.requestsTextInfo[1]['response']['contents']

      try:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['videoId']
      except KeyError:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][1]['videoRenderer']['videoId']

      self.trackData = await self.getTrackData(videoID)
      return AudioSample(f'https://www.youtube.com/watch?v={videoID}', self.trackData[0], self.trackData[1], self.trackData[2], self.trackData[3], self.trackData[4])

   async def getLiveStream(self, sourceUrl: str = None, loop = None):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'{sourceUrl}&pbj=1') as response:
            self.completeData = await response.json()

      self.completeData = self.completeData[2]['playerResponse']
      self.streamData = self.completeData['videoDetails']
      self.audioSource = await loop.run_in_executor(None, lambda: self.getLiveAudio(self.completeData))
      return AudioSample(sourceUrl[0], self.streamData['title'], self.streamData['author'], 'LIVE', self.streamData['thumbnail']['thumbnails'][-1]['url'], self.audioSource)
   
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
