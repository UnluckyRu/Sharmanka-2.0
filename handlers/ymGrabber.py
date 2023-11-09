import time
import aiohttp
import xmltodict
import asyncio

from hashlib import md5

try:
   from .handler import TimeHandler
except:
   from handler import TimeHandler

class YmEngine():
   def __init__(self) -> None:
      self.DECODE_VALUE = 'XGRlBW9FXlekgbPrRHuSiA'
      self.HEADERS = {'User-Agent': 'Windows 10',
                      'X-Yandex-Music-Client': 'WindowsPhone/4.54',
                      'Authorization': 'OAuth y0_AgAAAAAmfsGrAAG8XgAAAADubN2RW7NfsgOGQgGQc_X2wyjgxa0E7yI',}
      
      self.trackIDs = []
      self.playlistTracks = []

   async def getPlaylistMetadata(self, albumID: str = '', isAlbum: bool = False):
      if isAlbum:
         async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.music.yandex.net/albums/{albumID}/with-tracks') as response:
               self.insertData = await response.json()

         self.insertData = self.insertData.get('result')
         self.trackTitle = self.insertData.get('title')
         self.thumbnailLink = f"https://{self.insertData.get('coverUri').replace('%%', '200x200')}"

      if not isAlbum:
         async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.music.yandex.net/{albumID}') as response:
               self.insertData = await response.json()

         self.insertData = self.insertData.get('result')
         self.trackTitle = self.insertData.get('title')
         self.thumbnailLink = f"https://{self.insertData.get('cover')['uri'].replace('%%', '200x200')}"

      return [self.trackTitle, self.thumbnailLink]

   async def getTrackData(self, trackID: str = None):
      async with aiohttp.ClientSession() as session:
         async with session.get(f'https://api.music.yandex.net/tracks/{trackID}') as response:
            self.trackGeneralData = await response.json()

      self.insertData = self.trackGeneralData['result'][0]

      self.trackTitle = self.insertData.get('title')
      self.uploaderName = self.insertData.get('artists')[0]['name']
      self.thumbnailLink = f"https://{self.insertData.get('albums')[0]['coverUri'].replace('%%', '200x200')}"
      self.trackDuration = TimeHandler().millisecondsConverter(self.insertData.get('durationMs'))

      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'https://api.music.yandex.net/tracks/{trackID}/download-info') as response:
            self.audioRawSource = await response.json()

      self.downloadInfo = self.audioRawSource.get('result')[1]['downloadInfoUrl']

      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(self.downloadInfo) as response:
               self.textResult = await response.text()

      self.audioVariables = xmltodict.parse(self.textResult).get('download-info')

      servicesVaribles = list(self.audioVariables.values())
      sign = md5((self.DECODE_VALUE + servicesVaribles[1][1::] + servicesVaribles[-1]).encode('utf-8')).hexdigest()

      return [[self.trackTitle, self.uploaderName, self.trackDuration, self.thumbnailLink], f'https://{servicesVaribles[0]}/get-mp3/{sign}/{servicesVaribles[2]}{servicesVaribles[1]}']

   async def getSingleAudio(self, sourceUrl: str = ''):
      self.splittedUrl = sourceUrl.split('/')[-1]
      self.metaData, self.audioSource = await self.getTrackData(self.splittedUrl)

      return {'rawSource': sourceUrl,
              'title': self.metaData[0],
              'author': self.metaData[1],
              'duration': self.metaData[2],
              'thumbnail': self.metaData[3],
              'audioSource': self.audioSource}

   async def getPlaylistAudios(self, sourceUrl: str = ''):
      self.taskManager = []

      if sourceUrl.find('playlist') != -1:
         self.extractedUrl = sourceUrl[sourceUrl.rfind('ru/')+len('ru/')::]
         self.metaData = await self.getPlaylistMetadata(self.extractedUrl)
         async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(f'https://api.music.yandex.net/{self.extractedUrl}') as response:
               self.insertData = await response.json()

         self.albumRequest = self.insertData.get('result')['tracks']

      if sourceUrl.find('album') != -1:
         self.extractedUrl = sourceUrl[sourceUrl.rfind('/')+len('/')::]
         self.metaData = self.getPlaylistMetadata(self.extractedUrl, True)
         async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(f'https://api.music.yandex.net/albums/{self.extractedUrl}/with-tracks') as response:
               self.insertData = await response.json()

         self.albumRequest = self.insertData.get('result')['volumes'][0]

      for _, element in enumerate(self.albumRequest):
         self.trackIDs.append(element['id'])

      for _, trackId in enumerate(self.trackIDs):
         self.taskManager.append(asyncio.create_task(self.getTrackData(trackId)))
      self.extractInfo = await asyncio.gather(*self.taskManager)

      for _, source in enumerate(self.extractInfo):
         self.playlistTracks.append({'title': source[0][0], 
                                     'duration': source[0][2], 
                                     'audioSource': source[1]})

      return {'rawSource': sourceUrl,
              'title': self.metaData[0], 
              'thumbnail': self.metaData[1], 
              'playlist': self.playlistTracks}

   async def getTextToAudio(self, sourceText: str = ''):
      async with aiohttp.ClientSession(headers=self.HEADERS) as session:
         async with session.get(f'https://api.music.yandex.net/search?text={sourceText}&type=track&page=0') as response:
            self.textResultInfo = await response.json()

      self.requestResultInfo = self.textResultInfo.get('result')['tracks']['results'][0]["id"]
      self.metaData, self.audioSource = await self.getTrackData(self.requestResultInfo)

      return {'rawSource': self.audioSource,
              'title': self.metaData[0],
              'author': self.metaData[1],
              'duration': self.metaData[2],
              'thumbnail': self.metaData[3],
              'audioSource': self.audioSource}

class YmGrabber(YmEngine):
   def __init__(self) -> None:
      super().__init__()

   async def getFromYandex(self, sourceQuery: str = '', queryType: str = ''): 
      match queryType:
         case 'linkSource':
            self.intermidiateData = await self.getSingleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = await self.getPlaylistAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = await self.getTextToAudio(sourceQuery)

      return [queryType, self.intermidiateData]

# start = time.time()
# print(asyncio.run(YmGrabber().getFromYandex('home resonance', 'textSource')))
# print(time.time()-start)