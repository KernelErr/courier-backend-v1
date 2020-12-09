"""
    Author: LI Rui lir@bupt.edu.cn
    All rights reserved.
"""
import boto3
import dateutil
from utils import crypto
from utils.misc import deBase64, enBase64
from botocore.client import Config
from utils.config import MINIO_SERVER

try: 
    s3Client = boto3.client('s3',
                        endpoint_url=MINIO_SERVER['remote'],
                        aws_access_key_id=MINIO_SERVER['access_key'],
                        aws_secret_access_key=MINIO_SERVER['secret_key'],
                        config=Config(signature_version='s3v4'),
                        region_name='us-east-1')
except:
    raise Exception("S3ERR")

def signPutURL(token, link, objectKey, nickname, filename, validPeriod, contentType, contentLength, hash):
    try:
        return s3Client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": "courier",
                "Key": objectKey,
                "ContentType": contentType,
                "ContentLength": contentLength,
                "ContentMD5": hash,
                "Metadata": {
                    "Link": enBase64(link),
                    "Nickname": enBase64(nickname),
                    "Filename": enBase64(filename),
                    "ValidPeriod": enBase64(validPeriod),
                    "Token": enBase64(token["ciphertext"]),
                    "Crypto": enBase64(token["tag"])
                }
            },
            ExpiresIn=600,
            HttpMethod="PUT",
        )
    except:
        raise Exception("S3ERR")

def signGetURL(objectKey, objectType, filename):
    contentType = "text/plain" if objectType.split("/")[0]=="text" else "application/octet-stream"
    return s3Client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": "courier",
            "Key": objectKey,
            "ResponseContentType": contentType,
            "ResponseContentDisposition": "attachment; filename=\"" + filename + "\""
        },
        ExpiresIn=1800,
        HttpMethod="GET"
    )

def parseEvent(event):
    result = {}
    try:
        if event["EventName"] == "s3:ObjectCreated:Put":
            result["name"] = "PUT"
            record = event["Records"][0]
            result["time"] = dateutil.parser.parse(record["eventTime"])
            result["IP"] = record["source"]["host"]
            result["userAgent"] = record["source"]["userAgent"]
            result["hash"] = record["s3"]["object"]["eTag"]
            result["objectKey"] = record["s3"]["object"]["key"]
            result["objectSize"] = record["s3"]["object"]["size"]
            result["objectType"] = record["s3"]["object"]["contentType"]
            userMetadata = record["s3"]["object"]["userMetadata"]
            result["objectLink"] = deBase64(userMetadata["X-Amz-Meta-Link"])
            result["nickname"] = deBase64(userMetadata["X-Amz-Meta-Nickname"])
            result["filename"] = deBase64(userMetadata["X-Amz-Meta-Filename"])
            result["validPeriod"] = int(deBase64(userMetadata["X-Amz-Meta-Validperiod"]))
            result["token"] = crypto.decryAES(deBase64(userMetadata["X-Amz-Meta-Token"]), deBase64(userMetadata["X-Amz-Meta-Crypto"]))
        return result
    except:
        return result