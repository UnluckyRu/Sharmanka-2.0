import time
import grequests
import requests
import xmltodict
import concurrent.futures

from hashlib import md5

try:
   from .handler import TimeHandler
except:
   from handler import TimeHandler

class YmEngine():
   def __init__(self) -> None:
      self.DECODE_VALUE = 'XGRlBW9FXlekgbPrRHuSiA'
      self.HEADERS = {'User-Agent': 'Yandex-Music-API',
                      'X-Yandex-Music-Client': 'YandexMusicAndroid/24023231',
                      'Authorization': 'OAuth y0_AgAAAAAmfsGrAAG8XgAAAADubN2RW7NfsgOGQgGQc_X2wyjgxa0E7yI',}
      
      self.trackIDs = []
      self.playlistTracks = []

   def getDirtectLink(self, trackID: str = ''):
      self.invocationInfo = requests.get(f'https://api.music.yandex.net/tracks/{trackID}/download-info', headers=self.HEADERS).json()
      self.downloadInfo = self.invocationInfo.get('result')[1]['downloadInfoUrl']
      self.audioVariables = xmltodict.parse(requests.get(url=self.downloadInfo, headers=self.HEADERS).text).get('download-info')

      servicesVaribles = list(self.audioVariables.values())
      sign = md5((self.DECODE_VALUE + servicesVaribles[1][1::] + servicesVaribles[-1]).encode('utf-8')).hexdigest()

      return f'https://{servicesVaribles[0]}/get-mp3/{sign}/{servicesVaribles[2]}{servicesVaribles[1]}'

   def getPlaylistMetadata(self, albumID: str = '', isAlbum: bool = False):
      if isAlbum:
         self.insertData = requests.get(f'https://api.music.yandex.net/albums/{albumID}/with-tracks').json().get('result')
         self.trackTitle = self.insertData.get('title')
         self.thumbnailLink = f"https://{self.insertData.get('coverUri').replace('%%', '200x200')}"

      if not isAlbum:
         self.insertData = requests.get(f'https://api.music.yandex.net/{albumID}').json().get('result')
         self.trackTitle = self.insertData.get('title')
         self.thumbnailLink = f"https://{self.insertData.get('cover')['uri'].replace('%%', '200x200')}"

      return [self.trackTitle, self.thumbnailLink]

   def getTrackMetadata(self, trackID: list = None):
      self.insertData = []
      self.tracksInfo = []

      if not isinstance(trackID, list):
         trackID = [trackID]

      self.linksArray = [f'https://api.music.yandex.net/tracks/{ID}' for ID in trackID]
      self.response = grequests.map((grequests.get(url) for url in self.linksArray))

      for _, source in enumerate(self.response):
         self.trackTitle = source.json()['result'][0].get('title')
         self.uploaderName = source.json()['result'][0].get('artists')[0]['name']
         self.thumbnailLink = f"https://{source.json()['result'][0].get('albums')[0]['coverUri'].replace('%%', '200x200')}"
         self.trackDuration = TimeHandler().millisecondsConverter(source.json()['result'][0].get('durationMs'))
         self.tracksInfo.append([self.trackTitle, self.uploaderName, self.trackDuration, self.thumbnailLink])

      return self.tracksInfo

   def getSingleAudio(self, sourceUrl: str = ''):
      self.splittedUrl = sourceUrl.split('/')[-1]
      self.metaData = self.getTrackMetadata(self.splittedUrl)[0]
      self.audioSource = self.getDirtectLink(self.splittedUrl)

      return {'rawSource': sourceUrl,
              'title': self.metaData[0],
              'author': self.metaData[1],
              'duration': self.metaData[2],
              'thumbnail': self.metaData[3],
              'audioSource': self.audioSource}

   def getPlaylistAudios(self, sourceUrl: str = ''):
      self.audioSources = []

      if sourceUrl.find('playlist') != -1:
         self.extractedUrl = sourceUrl[sourceUrl.rfind('ru/')+len('ru/')::]
         self.metaData = self.getPlaylistMetadata(self.extractedUrl)
         self.albumRequest = requests.get(f'https://api.music.yandex.net/{self.extractedUrl}', headers=self.HEADERS).json().get('result')['tracks']

      if sourceUrl.find('album') != -1:
         self.extractedUrl = sourceUrl[sourceUrl.rfind('/')+len('/')::]
         self.metaData = self.getPlaylistMetadata(self.extractedUrl, True)
         self.albumRequest = requests.get(f'https://api.music.yandex.net/albums/{self.extractedUrl}/with-tracks', headers=self.HEADERS).json().get('result')['volumes'][0]

      for i in range(len(self.albumRequest)):
         self.trackIDs.append(self.albumRequest[i]['id'])
      self.tracksInfo = self.getTrackMetadata(self.trackIDs)

      with concurrent.futures.ThreadPoolExecutor() as executor:
         self.threadData = [executor.submit(self.getDirtectLink, trackID) for trackID in self.trackIDs]
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

   def getTextToAudio(self, sourceText: str = ''):
      self.requestResultInfo = requests.get(f'https://api.music.yandex.net/search?text={sourceText}&type=track&page=0', headers=self.HEADERS).json().get('result')['tracks']['results'][0]
      self.metaData = self.getTrackMetadata(self.requestResultInfo["id"])[0]
      self.audioSource = self.getDirtectLink(self.requestResultInfo["id"])

      return {'rawSource': self.audioSource,
              'title': self.metaData[0],
              'author': self.metaData[1],
              'duration': self.metaData[2],
              'thumbnail': self.metaData[3],
              'audioSource': self.audioSource}

class YmGrabber(YmEngine):
   def __init__(self) -> None:
      super().__init__()

   def getFromYandex(self, sourceQuery: str = '', queryType: str = ''): 
      match queryType:
         case 'linkSource':
            self.intermidiateData = self.getSingleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = self.getPlaylistAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = self.getTextToAudio(sourceQuery)

      return [queryType, self.intermidiateData]

# start = time.time()
# print(YmGrabber().getFromYandex('https://music.yandex.ru/users/music-blog/playlists/2710', 'playlist'))
# print(time.time()-start)