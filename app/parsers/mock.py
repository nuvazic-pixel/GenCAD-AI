from app.domain.intent import ParsedEngineeringIntent
from app.parsers.base import EngineeringParser
class MockParser(EngineeringParser):
    def __init__(self,result:ParsedEngineeringIntent): self._result=result
    def parse(self,prompt:str)->ParsedEngineeringIntent: return self._result
