import re
import html

try:
   from .vkGrabber import VkGrabber
   from .ytGrabber import YtGrabber
   from .ymGrabber import YmGrabber
except:
   from vkGrabber import VkGrabber
   from ytGrabber import YtGrabber
   from ymGrabber import YmGrabber

class SearchManager():
   def __init__(self) -> None:
      ...

   async def findAudio(self, searchQuery: str = '', platform: str = 'Youtube', loop = None) -> [str, dict]:
      self.searchQuery = html.unescape(searchQuery).replace('\n', '')

      match self.searchQuery.startswith('https://www.youtube') or self.searchQuery.startswith('https://www.soundcloud'):
         case True:
            match bool(re.search(r".list=|/sets/", self.searchQuery)):
               case True:
                  return await YtGrabber().getFromSource(sourceQuery=self.searchQuery, queryType='playlist')
            
            match bool(loop):
               case True:
                  return await YtGrabber().getFromSource(sourceQuery=self.searchQuery, queryType='liveSource', loop=loop)
               case False:
                  return await YtGrabber().getFromSource(sourceQuery=self.searchQuery, queryType='linkSource')

      match self.searchQuery.startswith('https://vk.com'):
         case True:
            match bool(re.search(r'playlist|album|audio_playlist', self.searchQuery)):
               case True:
                  return await VkGrabber().getFromVk(sourceQuery=self.searchQuery, queryType='playlist')
               case False:
                  return await VkGrabber().getFromVk(sourceQuery=self.searchQuery, queryType='linkSource')\
      
      match self.searchQuery.startswith('https://music.yandex.ru/'):
         case True:
            match bool(re.search(r'track', self.searchQuery)):
               case True:
                  return YmGrabber().getFromYandex(sourceQuery=self.searchQuery, queryType='linkSource')
               case False:
                  return YmGrabber().getFromYandex(sourceQuery=self.searchQuery, queryType='playlist')
                  

      match (not self.searchQuery.startswith('https://')):
         case True:
            match platform:
               case 'Youtube':
                  return await YtGrabber().getFromSource(sourceQuery=self.searchQuery, queryType='textSource')
               case 'Vkontakte':
                  return await VkGrabber().getFromVk(sourceQuery=self.searchQuery, queryType='textSource')
               case 'Yandex':
                  return YmGrabber().getFromYandex(sourceQuery=self.searchQuery, queryType='textSource')

#asyncio.run(SearchManager('https://www.youtube.com/playlist?list=PLtVQfwi9HjrCDn5JpyF65dp1PxZY5sKcp').findAudio())
