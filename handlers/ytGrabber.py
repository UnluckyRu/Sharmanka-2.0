import os
import re
import json
import js2py
import grequests
import concurrent.futures

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

   def getDirectLink(self, videoID: list = None) -> str:
      if not isinstance(videoID, list):
         videoID = [videoID]

      self.baseRequest = grequests.map(grequests.get(f'https://youtube.com/watch?v={ID}&pbj=1', headers=self.HEADERS) for ID in videoID)
      self.baseRequest = self.baseRequest[0].json()[2]['playerResponse']['streamingData']['adaptiveFormats'][-1]

      try:
         completeUrl = self.baseRequest['url']
         return completeUrl
      
      except KeyError:
         encodeSignature = self.baseRequest['signatureCipher']
         signature, _, rawUrl = encodeSignature.split('&')
         rawUrl = unquote(rawUrl.replace('url=', '')).split('Clmt')
         signature = unquote(signature.replace('s=', ''))

         decodeSignature = js2py.eval_js(self.jsonData['algorithm'])
         completeUrl = f"{rawUrl[0]}Clmt&sig={unquote(decodeSignature(signature))}{rawUrl[-1]}"

         return completeUrl

   def getTrackMetadata(self, videoID: str|list = None) -> list:
      self.tracksInfo = []

      if not isinstance(videoID, list):
         videoID = [videoID]

      self.manyResponse = grequests.map(grequests.get(f'https://youtube.com/watch?v={ID}&pbj=1', headers=self.HEADERS) for ID in videoID)

      for _, response in enumerate(self.manyResponse):
         self.currentResponse = response.json()[2]['playerResponse']
         self.title = self.currentResponse['videoDetails']['title']
         self.uploaderName = self.currentResponse['videoDetails']['author']
         self.thumbnailLink = self.currentResponse['videoDetails']['thumbnail']['thumbnails'][-1]['url']
         self.trackDuration = TimeHandler().timeConverter(self.currentResponse['videoDetails']['lengthSeconds'])
         self.tracksInfo.append([self.title, self.uploaderName, self.trackDuration, self.thumbnailLink])

      return self.tracksInfo

   def getPlaylistMetadata(self, playlistID: list = None) -> list:
      if not isinstance(playlistID, list):
         playlistID = [playlistID]

      self.metaData = grequests.map(grequests.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={ID}&key={API_KEY}') for ID in playlistID)
      self.metaData = self.metaData[0].json()['items'][0]

      self.title = self.metaData['snippet']['title']
      self.thumbnail = self.metaData['snippet']['thumbnails']['high']['url']

      return [self.title, self.thumbnail]

   def getSingleAudio(self, sourceUrl: str = None):
      videoID = sourceUrl.split('watch?v=')[-1]
      self.trackData = self.getTrackMetadata(videoID)[0]
      self.audioSource = self.getDirectLink(videoID)

      return {'rawSource': sourceUrl,
              'title': self.trackData[0],
              'author': self.trackData[1],
              'duration': self.trackData[2],
              'thumbnail': self.trackData[3],
              'audioSource': self.audioSource}

   def getPlaylistAudios(self, sourceUrl: str = None):
      self.sortingList = []

      if sourceUrl.find('?list=') != -1:
         playlistID = sourceUrl.split('?list=')[-1]
      if sourceUrl.find('&list=') != -1:
         playlistID = sourceUrl.split('&list=')[-1]

      playlistID = [playlistID]

      self.playlistRequests = grequests.map(grequests.get(f'https://www.youtube.com/playlist?list={ID}') for ID in playlistID)[0].text
      self.videosIDs = (re.findall(r'watch\?v=(\S{11})', self.playlistRequests))
      [self.sortingList.append(ID) for ID in self.videosIDs if ID not in self.sortingList]
      self.videosIDs = self.sortingList
      
      self.metaData = self.getPlaylistMetadata(playlistID)
      self.tracksInfo = self.getTrackMetadata(self.videosIDs)

      with concurrent.futures.ThreadPoolExecutor() as executor:
         self.threadData = [executor.submit(self.getDirectLink, ID) for ID in self.videosIDs]
      for _, source in enumerate(self.threadData):
         self.audioSources.append(source.result())

      for index, source in enumerate(self.tracksInfo):
         self.playlistTracks.append({'title': source[0], 
                                     'duration': source[2], 
                                     'audioSource': self.audioSources[index]})

      return {'rawSource': sourceUrl, 
              'title': self.metaData[0], 
              'thumbnail': self.metaData[1], 
              'playlist': self.playlistTracks}

   def getTextToAudio(self, sourceQuery: str = None):
      if not isinstance(sourceQuery, list):
         sourceQuery = [sourceQuery]

      self.requestsTextInfo = grequests.map(grequests.get(f'https://youtube.com/results?search_query={text}&pbj=1', headers=self.HEADERS) for text in sourceQuery)
      self.requestsTextInfo = self.requestsTextInfo[0].json()[1]['response']['contents']

      try:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['videoRenderer']['videoId']
      except KeyError:
         videoID = self.requestsTextInfo['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][1]['videoRenderer']['videoId']

      self.trackData = self.getTrackMetadata(videoID)[0]
      self.audioSource = self.getDirectLink(videoID)

      return {'rawSource': f'https://www.youtube.com/watch?v={videoID}',
              'title': self.trackData[0],
              'author': self.trackData[1],
              'duration': self.trackData[2],
              'thumbnail': self.trackData[3],
              'audioSource': self.audioSource}

   def getLiveAudio(self, getData: dict = None):
      return getData['streamingData']['hlsManifestUrl']

   async def getLiveStream(self, sourceUrl: str = None, loop = None):
      sourceUrl = [sourceUrl]

      self.completeData = grequests.map(grequests.get(f'{Url}&pbj=1', headers=self.HEADERS) for Url in sourceUrl)
      self.completeData = self.completeData[0].json()[2]['playerResponse']
      self.streamData = self.completeData['videoDetails']
      self.audioSource = await loop.run_in_executor(None, lambda: self.getLiveAudio(self.completeData))

      return {'rawSource': sourceUrl[0],
              'title': self.streamData['title'],
              'author': self.streamData['author'],
              'duration': 'LIVE',
              'thumbnail': self.streamData['thumbnail']['thumbnails'][-1]['url'],
              'audioSource': self.audioSource}
   
   def getManyAudios(self, textSource: str = None, tracksAmount: int = None):
      if tracksAmount is None: tracksAmount = 10
      self.audioSources = []

      self.DATA = {
         "query": f"{textSource}",
         "params": "EgIQAQ%3D%3D",
         "context": {"client": {"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, "thirdParty": {"embedUrl": "https://www.youtube.com"}},
         "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": f"{self.jsonData['timestamp']}"}}}

      self.DATA = [self.DATA]

      self.requestsTextInfo = grequests.map(grequests.post(f'https://www.youtube.com/youtubei/v1/search?key={self.jsonData["download_key"]}', json=DATA) for DATA in self.DATA)
      self.requestsTextInfo = self.requestsTextInfo[0].json()['contents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

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
            self.intermidiateData = self.getSingleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = self.getPlaylistAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = self.getTextToAudio(sourceQuery)
         case 'bulkRequests':
            self.intermidiateData = self.getManyAudios(sourceQuery, tracksAmount)
         case 'liveSource':
            self.intermidiateData = await self.getLiveStream(sourceQuery, loop)

      return [queryType, self.intermidiateData]

# start = time.time()
# print(asyncio.run(YtGrabber().getFromYoutube('Resonanse - HOME', 'textSource')))
# print(time.time() - start)