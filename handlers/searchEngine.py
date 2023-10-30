import asyncio
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
   @classmethod
   async def findAudio(cls, searchQuery: str = None, platform: str = None, tracksAmount: int = None, loop = None) -> [str, dict]:
      cls.searchQuery = html.unescape(searchQuery).replace('\n', '')

      match cls.searchQuery.startswith('https://www.youtube'):
         case True:
            match bool(re.search(r".list=|/sets/", cls.searchQuery)):
               case True:
                  return await YtGrabber().getFromYoutube(sourceQuery=cls.searchQuery, queryType='playlist')
            
            match bool(loop):
               case True:
                  return await YtGrabber().getFromYoutube(sourceQuery=cls.searchQuery, queryType='liveSource', loop=loop)
               case False:
                  return await YtGrabber().getFromYoutube(sourceQuery=cls.searchQuery, queryType='linkSource')

      match cls.searchQuery.startswith('https://vk.com'):
         case True:
            match bool(re.search(r'playlist|album|audio_playlist', cls.searchQuery)):
               case True:
                  return await VkGrabber().getFromVk(sourceQuery=cls.searchQuery, queryType='playlist')
               case False:
                  return await VkGrabber().getFromVk(sourceQuery=cls.searchQuery, queryType='linkSource')
      
      match cls.searchQuery.startswith('https://music.yandex.ru/'):
         case True:
            match bool(re.search(r'track', cls.searchQuery)):
               case True:
                  return YmGrabber().getFromYandex(sourceQuery=cls.searchQuery, queryType='linkSource')
               case False:
                  return YmGrabber().getFromYandex(sourceQuery=cls.searchQuery, queryType='playlist')
                  
      
      match (not cls.searchQuery.startswith('https://')):
         case True:
            match platform:
               case 'p' | 'P':
                  return await YtGrabber().getFromYoutube(sourceQuery=cls.searchQuery, queryType='textSource')
               case 'vp' | 'VP':
                  return await VkGrabber().getFromVk(sourceQuery=cls.searchQuery, queryType='textSource')
               case 'yp' | 'YP':
                  return YmGrabber().getFromYandex(sourceQuery=cls.searchQuery, queryType='textSource')
               case 'sp' | 'SP':
                  return await YtGrabber().getFromYoutube(sourceQuery=cls.searchQuery, queryType='bulkRequests', tracksAmount=tracksAmount)

# async def x():
#    x = await SearchManager().findAudio('https://www.youtube.com/watch?v=Mapzl6JFkD0')
#    print(x)

# asyncio.run(x())
