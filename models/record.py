"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
from pydantic import BaseModel

class requestCreateRecord(BaseModel):
    nickname: str
    filename: str
    validPeriod: int
    contentType: str
    contentLength: int
    contentHash: str
