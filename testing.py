import re
import time
import requests
import yt_dlp
from datetime import datetime

YDL_OPTIONS_URL = {
   'format': 'bestaudio/best', 
   'noplaylist': 'True', 
   'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
}

def debugWriter(data: any) -> None:
   with open(f'file_{datetime.now().strftime("%H%M%S")}.txt', 'w', encoding='utf-8') as file:
      file.write(str(data))
      file.close()
      print('Done!')

class MyClass():
   def tesdt(self, processedRequest):
      start = time.time()
      self.findRequest = requests.get(f"https://www.youtube.com/results?search_query={processedRequest}").text
      self.gettingResponse = re.findall(r"watch\?v=(\S{11})", self.findRequest)
      self.sortedUrls = ['https://www.youtube.com/watch?v='+ i for n, i in enumerate(self.gettingResponse) if i not in self.gettingResponse[:n]][:10]
      self.titlesList = [requests.get(f'https://noembed.com/embed?dataType=json&url={self.sortedUrls[n]}').json()['title'] for n in range(len(self.sortedUrls))]
      self.authorsList = [requests.get(f'https://noembed.com/embed?dataType=json&url={self.sortedUrls[n]}').json()['author_name'] for n in range(len(self.sortedUrls))]

      self.audioSource = [dict([('title', self.titlesList[i]), ('author', self.authorsList[i]), ('url', self.sortedUrls[i])]) for i in range(len(self.sortedUrls))]
      print(time.time()-start)

      print(self.audioSource)

#MyClass().tesdt('Home - resonanse')

print(yt_dlp.YoutubeDL(YDL_OPTIONS_URL).extract_info(url='https://www.youtube.com/watch?v=T1DoonCfSsA', download=False)['channel'])