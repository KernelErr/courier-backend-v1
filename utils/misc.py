"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
import nanoid
import base64
import datetime

def genLink():
    return nanoid.generate("123456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ", 8)

def genToken():
    return nanoid.generate("123456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ", 32)

def checkValidPeriod(validPeriod, type):
    validPeriod = int(validPeriod)
    if type == "File":
        maxPeriod = 7
        if validPeriod > maxPeriod or validPeriod <= 0:
            return 0
        return validPeriod
    else:
        if validPeriod < -1 or validPeriod == 0:
            return 0
        return validPeriod

def convertValidPeriod(validPeriod):
    validPeriod = int(validPeriod)
    currentTime = datetime.datetime.utcnow()
    if validPeriod != -1:
        return [currentTime,
                currentTime + datetime.timedelta(days=validPeriod),
                validPeriod]
    else:
        return [currentTime,
                datetime.datetime(2999,12,31,0,0,0,0),
                validPeriod]

def enBase64(s):
    s = str(s)
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")

def deBase64(s):
    return base64.b64decode(s).decode("utf-8")

def checkHeader(request, needed):
    for header in needed:
        if header not in request.headers:
            return False
    return True

def checkFileType(contentType, length):
    if length > 1024*1024*3:
        return "File"
    elif contentType.split("/")[0] == "text":
        return "Code"
    else:
        return "File"

def checkMIME(s):
    try:
        genType, _ = s.split('/')
        if genType not in ["application","audio","font","example","image","message","model","multipart","text","video"]:
            return False
        return True
    except:
        return False

def genCURL(method, headers, endpoint):
    base = "curl"
    base = base + " -X " + method
    for key in headers:
        base = base + " -H " + "'" + key + ": " + str(headers[key]) + "'"
    base = base + " '" + endpoint + "'"
    if method == "PUT":
        base = base + " --data-binary [CURLFILE]"
    return base

def checkExpired(expireTime):
    currentTime = datetime.datetime.utcnow()
    if currentTime > expireTime:
        return True
    else:
        return False