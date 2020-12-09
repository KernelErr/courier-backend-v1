"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
from pydantic import BaseModel

class requestLoginUser(BaseModel):
    username: str
    password: str
    type: int

class requestYibanUser(BaseModel):
    code: str

class responseLoginUser(BaseModel):
    token: str