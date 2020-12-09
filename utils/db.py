"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
from utils.config import MONGODB_STRING
import pymongo
from utils.misc import genToken, checkFileType

try: 
    db = pymongo.MongoClient(MONGODB_STRING)
except:
    raise Exception("DBERR")

def addRecord(token, link, nickname, filename, objectKey, objectType, objectSize, objectHash, createdTime, expireTime, ip, userAgent):
    try:
        user = getUserFromToken(token)
        if user is None:
            return False
        if getRecordFromLink(link) is not None:
            return False
        recordDoc = {
            "link": link,
            "nickname": nickname,
            "filename": filename,
            "objectKey": objectKey,
            "objectType": objectType,
            "objectSize": objectSize,
            "objectHash": objectHash,
            "createdTime": createdTime,
            "expireTime": expireTime,
            "identifier": user["identifier"],
            "IP": ip,
            "userAgent": userAgent,
            "statistic":{
                "visitTimes": 0
            }
        }
        fileType = checkFileType(objectType, objectSize)
        userUpdateDoc = {}
        if fileType == "File":
            userUpdateDoc = {
                "$inc": {
                    "statistic.fileCount" : 1,
                    "statistic.allSize" : objectSize,
                }
            }
        elif fileType == "Code":
            userUpdateDoc = {
                "$inc": {
                    "statistic.codeCount" : 1,
                    "statistic.allSize" : objectSize,
                }
            }
        db.courier.records.insert_one(recordDoc)
        db.courier.users.update_one({"token":token}, userUpdateDoc)
        return True
    except:
        return False

def getUser(identifier, ip):
    user = db.courier.users.find_one({"identifier":identifier})
    if user is None:
        token = genToken()
        while getUserFromToken(token) is not None:
            token = genToken()
        newUserDoc = {
            "token":token,
            "identifier":identifier,
            "permission":{"postCode":True,"postFile":True,"admin":False},
            "statistic":{"codeCount":0,"fileCount":0,"allSize":0},
            "lastIP":ip
        }
        try:
            db.courier.users.insert_one(newUserDoc)
        except:
            raise Exception("DBERR")
        return newUserDoc
    else:
        updateDoc = {
            "$set":{
                "lastIP": ip
            }
        }
        try:
            db.courier.users.update_one({"identifier":identifier}, updateDoc)
        except:
            raise Exception("DBERR")
        return db.courier.users.find_one({"identifier":identifier})

def getUserFromToken(token):
    return db.courier.users.find_one({"token":token})

def getRecordFromLink(link):
    return db.courier.records.find_one({"link":link})

def visitRecord(link):
    if db.courier.records.find_one({"link":link}) is None:
        return None
    updateDoc = {
        "$inc":{
            "statistic.visitTimes": 1
        }
    }
    db.courier.records.update_one({"link":link}, updateDoc)
    return db.courier.records.find_one({"link":link})