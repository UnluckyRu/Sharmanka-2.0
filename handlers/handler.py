class Handlers():
   def __init__(self) -> None:
      pass

   def timeConverter(self, time: int) -> str:
      self.seconds = time % 60
      self.minutes = (time // 60) % 60
      self.hours = time // 3600

      if self.seconds < 10: self.seconds = f'0{self.seconds}'
      if self.minutes < 10: self.minutes = f'0{self.minutes}'

      if self.hours > 0:
         return f'{self.hours}:{self.minutes}:{self.seconds}'
      else:
         return f'{self.minutes}:{self.seconds}'
      
   def millisecondsConverter(self, time: int) -> str:
      time = time//1000

      self.seconds = time % 60
      self.minutes = (time // 60) % 60
      self.hours = time // 3600

      if self.seconds < 10: self.seconds = f'0{self.seconds}'
      if self.minutes < 10: self.minutes = f'0{self.minutes}'

      if self.hours > 0:
         return f'{self.hours}:{self.minutes}:{self.seconds}'
      else:
         return f'{self.minutes}:{self.seconds}'
