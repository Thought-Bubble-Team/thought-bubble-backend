from pydantic import BaseModel

class EntryRequest(BaseModel):
    entry_id: int
    
class SentimentResponse(BaseModel):
    entry_id: int
    content: str
    sentiment: str
    confidence_score: float