"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
import json
import requests
import nanoid
from fastapi import FastAPI, Request, Depends, Response
from fastapi.security import OAuth2PasswordBearer
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from starlette.responses import RedirectResponse
from utils import db
from utils import s3
from utils import misc
from utils import crypto
from utils.config import MINIO_SERVER, OAUTH_YIBAN
from models.record import requestCreateRecord
from models.users import requestLoginUser, requestYibanUser
from utils.auth import checkPermission, yibanLogin

app = FastAPI(
    title="Courier Project",
    description="Courier dev ver",
    version="0.0.1",
)

oauth2Scheme = OAuth2PasswordBearer(tokenUrl="v1/user")

@app.post("/v1/record")
async def create_record(record: requestCreateRecord, response: Response, token: str = Depends(oauth2Scheme)):
    objectKey = nanoid.generate()
    user = db.getUserFromToken(token)
    if user is None:
        response.status_code = HTTP_401_UNAUTHORIZED
        return {"msg":"Wrong token"}
    if len(record.nickname) > 25:
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Nickname too large"}
    if len(record.filename) > 100:
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Filename too large"}
    if record.contentLength > 1024*1024*1024*3:
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Upload size too large"}
    if not misc.checkMIME(record.contentType):
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Invalid MIME type"}
    fileType = misc.checkFileType(record.contentType, record.contentLength)
    if fileType == "File":
        if not checkPermission(user, "postFile"):
            response.status_code = HTTP_403_FORBIDDEN
            return {"msg":"Permission denied"}
    else:
        if not checkPermission(user, "postCode"):
            response.status_code = HTTP_403_FORBIDDEN
            return {"msg":"Permission denied"}
    validPeriod = misc.checkValidPeriod(record.validPeriod, fileType)
    if validPeriod == 0:
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Invalid valid period"}
    try:
        link = misc.genLink()
        while db.getRecordFromLink(link) is not None:
            link = misc.genLink()
        cryToken = crypto.encryAES(token)
        s3Link = s3.signPutURL(cryToken, link, objectKey, record.nickname, record.filename, validPeriod, record.contentType, record.contentLength, record.contentHash)
        response.status_code = HTTP_200_OK
        headers = {
                    "Content-Type": record.contentType,
                    "Content-Length": record.contentLength,
                    "Content-MD5": record.contentHash,
                    "x-amz-meta-link": misc.enBase64(link),
                    "x-amz-meta-nickname": misc.enBase64(record.nickname),
                    "x-amz-meta-filename": misc.enBase64(record.filename),
                    "x-amz-meta-validperiod": misc.enBase64(validPeriod),
                    "x-amz-meta-token": misc.enBase64(cryToken["ciphertext"]),
                    "x-amz-meta-crypto": misc.enBase64(cryToken["tag"])
                }
        curlCommand = misc.genCURL("PUT", headers, s3Link)
        response.status_code = HTTP_200_OK
        return {
                "link": link,
                "validPeriod": validPeriod,
                "endpoint": s3Link,
                "headers": headers,
                "cURL": curlCommand
            }
    except:
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        return {"msg":"Internal error"}

@app.get("/v1/record/{link}")
def get_record(link: str, response: Response):
    try:
        record = db.visitRecord(link)
        if record is None:
            response.status_code = HTTP_404_NOT_FOUND
            return {
                "msg":"Not found"
            }
        expired = misc.checkExpired(record["expireTime"])
        if expired:
            response.status_code = HTTP_404_NOT_FOUND
            return {
                "msg":"Not found"
            }
        s3Link = s3.signGetURL(record["objectKey"], record["objectType"], record["filename"])
        response.status_code = HTTP_200_OK
        return {
            "link": record["link"],
            "nickname": record["nickname"],
            "filename": record["filename"],
            "contentType": record["objectType"],
            "contentLength": record["objectSize"],
            "contentHash": record["objectHash"],
            "visitTimes": record["statistic"]["visitTimes"],
            "endpoint": s3Link,
        }
    except:
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        return {"msg":"Internal error"}

@app.get("/raw/{link}")
def get_raw_record(link: str, response: Response):
    try:
        record = db.visitRecord(link)
        if record is None:
            response.status_code = HTTP_404_NOT_FOUND
            return {
                "msg":"Not found"
            }
        expired = misc.checkExpired(record["expireTime"])
        if expired:
            response.status_code = HTTP_404_NOT_FOUND
            return {
                "msg":"Not found"
            }
        s3Link = s3.signGetURL(record["objectKey"], record["objectType"], record["filename"])
        return RedirectResponse(s3Link)
    except:
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        return {"msg":"Internal error"}

@app.get("/raw/{link}/{filename}")
async def get_raw_record(link: str, filename: str, response: Response):
    record = db.visitRecord(link)
    if record is None:
        response.status_code = HTTP_404_NOT_FOUND
        return {
            "msg":"Not found"
        }
    expired = misc.checkExpired(record["expireTime"])
    if expired:
        response.status_code = HTTP_404_NOT_FOUND
        return {
            "msg":"Not found"
        }
    s3Link = s3.signGetURL(record["objectKey"], record["objectType"], record["filename"])
    return RedirectResponse(s3Link)

@app.post("/v1/user")
def login_user(loginCredit: requestLoginUser, request: Request, response: Response):
    if loginCredit.type == 1:
        if yibanLogin(loginCredit.username, loginCredit.password):
            identifier = {
                "content": loginCredit.username,
                "type": "yiban"
            }
            try:
                user = db.getUser(identifier, request.client.host)
                response.status_code = HTTP_200_OK
                return {"token": user["token"]}
            except:
                response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
                return {"msg":"Internal error"}
        else:
            response.status_code = HTTP_401_UNAUTHORIZED
            return {"msg":"Wrong credit"}
    else:
        response.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        return {"msg":"Wrong login type"}

@app.post("/v1/user/yiban")
def yiban_oauth(loginCredit: requestYibanUser, request: Request, response: Response):
    try:
        data = {
            "client_id": OAUTH_YIBAN["client_id"],
            "client_secret": OAUTH_YIBAN["client_secret"],
            "code": loginCredit.code,
            "redirect_uri": "http://local.bupt.host:8000/oauth/yiban"
        }
        req = requests.post("https://openapi.yiban.cn/oauth/access_token", data=data)
        userData = json.loads(req.content)
        req = requests.get("https://openapi.yiban.cn/user/me?access_token=" + userData["access_token"])
        userInfo = json.loads(req.content)
        yibanID = userInfo["info"]["yb_userid"]
        identifier = {
                "content": yibanID,
                "type": "yiban"
        }
        user = db.getUser(identifier, request.client.host)
        response.status_code = HTTP_200_OK
        return {"token": user["token"]}
    except:
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        return {"msg":"Internal error"}

@app.post("/v1/webhook")
async def webhook(request: Request, response: Response, token: str = Depends(oauth2Scheme)):
    if token != MINIO_SERVER["webhook_auth"]:
        response.status_code = HTTP_401_UNAUTHORIZED
        return {"msg":"Wrong credit"}
    try:
        data = json.loads(await request.body())
        data = s3.parseEvent(data)
        validPeriod = misc.convertValidPeriod(data["validPeriod"])
        db.addRecord(data["token"], data["objectLink"], data["nickname"], data["filename"],
                        data["objectKey"], data["objectType"], data["objectSize"], data["hash"],
                        validPeriod[0], validPeriod[1], data["IP"], data["userAgent"])
        response.status_code = HTTP_200_OK
        return {"msg":"Record created"}
    except:
        response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
        return {"msg":"Internal error"}
