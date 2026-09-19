from abc import ABC, abstractmethod
from app.domain.intent import ParsedEngineeringIntent
class EngineeringParser(ABC):
    @abstractmethod
    def parse(self,prompt:str)->ParsedEngineeringIntent: raise NotImplementedError
