import os
import re
import time
import json
import js2py
import asyncio
import grequests
import requests
import concurrent.futures

from urllib.parse import unquote
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
API_KEY = os.environ.get('YOUTUBE_API_TOKEN')

try:
   from .handler import TimeHandler
except:
   from handler import TimeHandler

class Youtube():
   def __init__(self) -> None:
      self.audioSources = []
      self.playlistTracks = []
      self.videosIDs = []
      self.checkUpdate()

   def checkUpdate(self) -> None:
      print('[Utilite] Checking update...')
      self.CIPHER_VERSION = (requests.get('https://www.youtube.com/iframe_api').text).split(';')[0].split('/')[5].replace('\\', '')
      with open('./utilities/algorithmData.json', encoding='UTF-8') as file:
         jsonData = json.load(file)

      match jsonData['version'] != self.CIPHER_VERSION:
         case True:
            functionParser = (requests.get(f'https://www.youtube.com/s/player/{self.CIPHER_VERSION}/player_ias.vflset/en_US/base.js').text).replace('\n', '')
            mainFunction = re.search(r"[\{\d\w\(\)\\.\=\"]*?;(..\...\(.\,..?\)\;){3,}.*?}", functionParser)[0]
            subFunction = re.findall(r"var "+re.findall(r'(\w\w)\...', mainFunction)[0]+r"={.+?};", functionParser)[0]

            jsonData['timestamp'] = re.findall(r'signatureTimestamp:\S{5}', functionParser)[-1].replace('signatureTimestamp:', '')
            jsonData['version'] = self.CIPHER_VERSION
            jsonData['algorithm'] = f'{subFunction} {mainFunction};'

            with open('./utilities/algorithmData.json', 'w') as file:
               json.dump(jsonData, file, ensure_ascii=False)
      print('[Utilite] Update complete...')

class YtEngine(Youtube):
   def __init__(self) -> None:
      super().__init__()

      with open('./utilities/algorithmData.json', encoding='UTF-8') as file:
         self.jsonData = json.load(file)

   def getDirectLink(self, videoID: str = None) -> str:
      self.DATA = {
         "videoId": f"{videoID}",
         "context": {"client": {"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, "thirdParty": {"embedUrl": "https://www.youtube.com"}},
         "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": f"{self.jsonData['timestamp']}"}}}
      
      baseRequest = requests.post(f'https://www.youtube.com/youtubei/v1/player?key={self.jsonData["download_key"]}', json=self.DATA).json()

      try:
         completeUrl = baseRequest['streamingData']['adaptiveFormats'][-4]['url']
      except KeyError:
         encodeSignature = baseRequest['streamingData']['adaptiveFormats'][-4]['signatureCipher']
         signature, _, rawUrl = encodeSignature.split('&')
         rawUrl = unquote(rawUrl.replace('url=', '')).split('Clmt')
         signature = unquote(signature.replace('s=', ''))

         decodeSignature = js2py.eval_js(self.jsonData['algorithm'])
         completeUrl = f"{rawUrl[0]}Clmt&sig={unquote(decodeSignature(signature))}{rawUrl[-1]}"

      return completeUrl

   def getPlaylistMetadata(self, playlistID: str = None) -> list:
      self.metaData = requests.get(f'https://www.googleapis.com/youtube/v3/playlists?part=snippet&id={playlistID}&key={API_KEY}').json()['items'][0]

      self.title = self.metaData['snippet']['title']
      self.thumbnail = self.metaData['snippet']['thumbnails']['high']['url']

      return [self.title, self.thumbnail]

   def getTrackMetadata(self, videoID: str|list = None) -> list:
      self.tracksInfo = []

      if not isinstance(videoID, list):
         videoID = [videoID]

      self.dataList = [{
         "videoId": f"{ID}",
         "context": {"client": {"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, "thirdParty": {"embedUrl": "https://www.youtube.com"}},
         "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": f"{self.jsonData['timestamp']}"}}} for ID in videoID]

      self.manyResponse = grequests.map(grequests.post(f'https://www.youtube.com/youtubei/v1/player?key={self.jsonData["download_key"]}', json=data) for data in self.dataList)

      for _, response in enumerate(self.manyResponse):
         self.currentResponse = response.json()
         self.title = self.currentResponse['videoDetails']['title']
         self.uploaderName = self.currentResponse['videoDetails']['author']
         self.thumbnailLink = self.currentResponse['videoDetails']['thumbnail']['thumbnails'][-1]['url']
         self.trackDuration = TimeHandler().timeConverter(self.currentResponse['videoDetails']['lengthSeconds'])
         self.tracksInfo.append([self.title, self.uploaderName, self.trackDuration, self.thumbnailLink])

      return self.tracksInfo

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

      playlistID = sourceUrl.split('?list=')[-1]
      self.playlistRequests = requests.get(f'https://www.youtube.com/playlist?list={playlistID}').text
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
      self.DATA = {
         "query": f"{sourceQuery}",
         "context": {"client": {"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, "thirdParty": {"embedUrl": "https://www.youtube.com"}},
         "playbackContext": {"contentPlaybackContext": {"signatureTimestamp": f"{self.jsonData['timestamp']}"}}}

      self.requestsTextInfo = requests.post(f'https://www.youtube.com/youtubei/v1/search?key={self.jsonData["download_key"]}', json=self.DATA).json()
      videoID = self.requestsTextInfo['contents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['compactVideoRenderer']['videoId']

      self.trackData = self.getTrackMetadata(videoID)[0]
      self.audioSource = self.getDirectLink(videoID)

      return {'rawSource': f'https://www.youtube.com/watch?v={videoID}',
              'title': self.trackData[0],
              'author': self.trackData[1],
              'duration': self.trackData[2],
              'thumbnail': self.trackData[3],
              'audioSource': self.audioSource}

   def getLiveAudio(self, postData: dict = None):
      self.audioManifest = requests.post(f'https://www.youtube.com/youtubei/v1/player?key={self.jsonData["download_key"]}', json=postData).json()
      return self.audioManifest['streamingData']['hlsManifestUrl']

   async def getLiveStream(self, sourceUrl: str = None, loop = None):
      streamID = sourceUrl.split("?v=")[-1]

      self.DATA = {
         "videoId": f"{streamID}",
         "context": {"client": {"clientName": "WEB", "clientVersion": "2.20231020.00.01"}}}

      self.completeData = requests.post(f'https://www.youtube.com/youtubei/v1/player?key={self.jsonData["download_key"]}', json=self.DATA).json()
      self.streamData = self.completeData['videoDetails']
      self.audioSource = await loop.run_in_executor(None, lambda: self.getLiveAudio(self.DATA))

      return {'rawSource': sourceUrl,
              'title': self.streamData['title'],
              'author': self.streamData['author'],
              'duration': 'LIVE',
              'thumbnail': self.streamData['thumbnail']['thumbnails'][-1]['url'],
              'audioSource': self.audioSource}

class YtGrabber(YtEngine):
   def __init__(self) -> None:
      super().__init__()

   async def getFromYoutube(self, sourceQuery: str = None, queryType: str = None, loop = None): 
      match queryType:
         case 'linkSource':
            self.intermidiateData = self.getSingleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = self.getPlaylistAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = self.getTextToAudio(sourceQuery)
         case 'liveSource':
            self.intermidiateData = await self.getLiveStream(sourceQuery, loop)

      return [queryType, self.intermidiateData]

'''start = time.time()
asyncio.run(YtGrabber().getFromYoutube('черниковская хата спектакль окончен', 'textSource'))
print(time.time() - start)'''
