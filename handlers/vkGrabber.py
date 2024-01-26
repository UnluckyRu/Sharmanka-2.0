import os
from vkwave.api import API
from vkwave.client import AIOHTTPClient
from dotenv import load_dotenv, find_dotenv

try:
   from .handler import TimeHandler, AudioSample, PlaylistSample
except:
   from handler import TimeHandler, AudioSample, PlaylistSample

load_dotenv(find_dotenv())

VK_LOGIN = os.environ.get('VK_LOGIN')
VK_PASSWORD = os.environ.get('VK_PASSWORD')
VK_BOT_TOKEN = os.environ.get('VK_BOT_TOKEN')

class VkEngine():
   def __init__(self) -> None:
      self.tracksData = {}
      self.playlistTracks = []
      self.audioPicture = None

   async def singleAudio(self, sourceUrl: str = None) -> dict[str, any]:
      self.vk_client = AIOHTTPClient()
      self.vk_api=API(clients=self.vk_client, tokens=VK_BOT_TOKEN, api_version="5.90")

      self.shortUrl = sourceUrl[sourceUrl.find('audio')+len('audio')::]
      self.tracksData['audios'] = f"{self.shortUrl.split('_')[0]}_{self.shortUrl.split('_')[1]}"
      self.response = await self.vk_api.get_context().api_request(method_name='audio.getById', params=self.tracksData)
      self.audioData = self.response.get('response')[0]

      try:
         self.audioPicture = self.audioData['album']['thumb'].get('photo_300')
      except:
         self.audioPicture = 'https://play-lh.googleusercontent.com/tpok7cXkBGfq75J1xF9Lc5e7ydTix7bKN0Ehy87VP2555f8Lnmoj1KJNUlQ7-4lIYg4'

      return AudioSample(sourceUrl, 
                         self.audioData.get('title'), 
                         self.audioData.get('artist'), 
                         TimeHandler.timeConverter(self.audioData.get('duration')), 
                         self.audioPicture, 
                         self.audioData.get('url'))

   async def albumAudios(self, sourceUrl: str = None) -> dict[str, any]:
      self.vk_client = AIOHTTPClient()
      self.vk_api=API(clients=self.vk_client, tokens=VK_BOT_TOKEN, api_version="5.90")

      self.shortUrl = (sourceUrl.split('/')[-1]).split('_')
      if sourceUrl.rfind('&z=audio_playlist') != -1:
         self.shortUrl = sourceUrl[sourceUrl.find('playlist')+len('playlist')::].split('_')
         self.shortUrl.extend(self.shortUrl[-1].split('%'))
         self.shortUrl.pop(1)

      self.tracksData['owner_id'] = int(self.shortUrl[0])
      self.tracksData['playlist_id'] = int(self.shortUrl[1])

      try:
         self.tracksData['access_key'] = self.shortUrl[2]
      except:
         self.tracksData['access_key'] = None

      self.tracksResponse = await self.vk_api.get_context().api_request(method_name='audio.get', params=self.tracksData)
      self.audioData = self.tracksResponse.get('response')

      self.playlistResponse = await self.vk_api.get_context().api_request(method_name='audio.getPlaylistById', params=self.tracksData)
      self.playlistData = self.playlistResponse.get('response')

      for _, source in enumerate(self.audioData.get('items')):
         self.playlistTracks.append(AudioSample(title=source.get('title'), duration=TimeHandler.timeConverter(source.get('duration')), audioSource=source.get('url')))
      
      try:
         self.thumbnail = self.playlistData['photo'].get('photo_300')
      except KeyError:
         self.thumbnail = self.playlistData['thumbs'][0].get('photo_300')
      else:
         self.thumbnail = 'https://play-lh.googleusercontent.com/tpok7cXkBGfq75J1xF9Lc5e7ydTix7bKN0Ehy87VP2555f8Lnmoj1KJNUlQ7-4lIYg4'

      return PlaylistSample(rawSource=sourceUrl, title=self.playlistData.get('title'), thumbnail=self.thumbnail, playlist=self.playlistTracks)

   async def getTextToAudio(self, sourceText: str = None) -> dict[str, any]:
      self.vk_client = AIOHTTPClient()
      self.vk_api=API(clients=self.vk_client, tokens=VK_BOT_TOKEN, api_version="5.90")

      self.tracksData['q'] = sourceText
      self.tracksData['count'] = 1
      self.response = await self.vk_api.get_context().api_request(method_name='audio.search', params=self.tracksData)
      self.audioData = self.response.get('response')['items'][0]

      try:
         self.audioPicture = self.audioData['album']['thumb'].get('photo_300')
      except:
         self.audioPicture = 'https://play-lh.googleusercontent.com/tpok7cXkBGfq75J1xF9Lc5e7ydTix7bKN0Ehy87VP2555f8Lnmoj1KJNUlQ7-4lIYg4'

      return AudioSample(self.audioData.get('url'), 
                         self.audioData.get('title'), 
                         self.audioData.get('artist'), 
                         TimeHandler.timeConverter(self.audioData.get('duration')),
                         self.audioPicture,
                         self.audioData.get('url'),)

class VkGrabber(VkEngine):
   def __init__(self) -> None:
      super().__init__()

   async def getFromVk(self, sourceQuery: str = None, queryType: str = None) -> list: 
      match queryType:
         case 'linkSource':
            self.intermidiateData = await self.singleAudio(sourceQuery)
         case 'playlist':
            self.intermidiateData = await self.albumAudios(sourceQuery)
         case 'textSource':
            self.intermidiateData = await self.getTextToAudio(sourceQuery)

      return [queryType, self.intermidiateData]
   