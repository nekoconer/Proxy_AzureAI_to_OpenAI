from pydantic import BaseModel

class CreateKeyRequest(BaseModel):
    company: str
    num:int
    
class DeleteKeyRequest(BaseModel):
    company: str
    key:str

class AddKeyRequest(BaseModel):
    company: str
    key:str
    add_num:int

class KeyStatusRequest(BaseModel):
    company: str