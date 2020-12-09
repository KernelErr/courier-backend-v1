# Courier Backend

这是北邮Paste Bin，或内部代号Courier的初代后端代码，现以MPL 2.0协议开源。北邮Paste Bin是一款基于MongoDB和S3服务的代码、文件分享应用。

## 依赖

- FastAPI
- S3-like
- MongoDB

## API参考文档

#### 登录用户

Endpoint: /v1/user

Method: Post

Body: JSON

```json
{
  "username": "111",
  "password": "123",
  "type": 1
}
```

username - 用户名

password - 密码

type - 认证类型，目前只有1

Response: JSON

```json
{
    "token": "RtqSjc21xkxEqD7e6hFn5vr37QpTFVa5"
}
```

代表当前用户的Token

#### 上传代码/文件

Endpoint: /v1/record

Method: Post

Authoritarian: Bearer Token

Body: JSON

```json
{
    "nickname":"li",
    "validPeriod": 3,
    "contentType": "application/x-iso9660-image",
    "contentLength": 2502909952,
    "contentHash": "rA1gLZ8LdHJcADtqWhGShg==",
    "filename": "System.iso"
}
```

nickname - 用户填写的昵称

validPeriod - 有效期，整数天数

contentType - 文件类型，如果为代码的话使用“text/语言”，如"text/python"，文件则保持原状

contentLength - 文件长度

contentHash - 2进制MD5哈希后Base64，openssl的生成方法是`openssl dgst -md5 -binary System.iso | base64`

fileName - 文件名称，注意，如果用户没有指定代码的文件名称的话，那就生成`语言 日期.后缀`，如`Python 2020-11-3 21:24.py`

Response: JSON

```json
{
    "link": "BKMTjFc3",
    "validPeriod": 3,
    "endpoint": "http://127.0.0.1:9000/***********",
    "headers": {
        "Content-Type": "application/x-iso9660-image",
        "Content-Length": 2502909952,
        "Content-MD5": "rA1gLZ8LdHJcADtqWhGShg==",
        "x-amz-meta-link": "QktNVGpGYzM=",
        "x-amz-meta-nickname": "bGk=",
        "x-amz-meta-filename": "*********",
        "x-amz-meta-validperiod": "Mw==",
        "x-amz-meta-token": "*********",
        "x-amz-meta-crypto": "*********"
    },
    "cURL": "curl -X PUT -H 'Content-Type: application/x-iso9660-image' -H 'Content-Length: 2502909952' -H 'Content-MD5: rA1gLZ8LdHJcADtqWhGShg==' -H 'x-amz-meta-link: QktNVGpGYzM=' -H 'x-amz-meta-nickname: bGk=' -H 'x-amz-meta-filename: V2luZG93c183XzMy5L2NX+S4reaWh+S4k+S4mueJiC5pc28=' -H 'x-amz-meta-validperiod: Mw==' -H 'x-amz-meta-token: U2wrOVUvZk1FT0xrb240Uzg2VDRheVZYK1BVYkZnOGQ4OVRHTjhEeUJtbz0=' -H 'x-amz-meta-crypto: ZmtyMGJSSkJxZTJEVGpRS0lnb1Bmdz09' 'http://127.0.0.1:9000/***********' --data-binary [CURLFILE]"
}
```

link - 生成的短链接

validPeriod - 有效期，用于确认

endpoint - 上传文件的链接，直接put即可

headers - 上传文件应该带有的header，错误即无法上传

cURL - cURL命令示例

#### 下载文件

有两个链接，用户从 http://domain/s/link 或者 http://domain/raw/link 进入

##### s

这时候会从后台查询数据展示在网页上，注意判断是文件还是代码。（如果文件类型以text开头且大小小于3M算代码，否则让用户下载）

Endpoint: v1/record/{link}

Method: Get

Response: JSON

```json
{
    "link": "HY3UZRbp",
    "nickname": "li",
    "filename": "sun.png",
    "contentType": "image/png",
    "contentLength": 4039,
    "contentHash": "398319897239c86b21ad901f88dc4a4b",
    "visitTimes": 2,
    "endpoint": "http://127.0.0.1:9000/***********"
}
```

link - 链接

nickname - 上传者昵称

filename - 文件名

contentType - 文件类型

contentLength - 文件大小

contentHash - 十进制的md5，`md5sum`即可生成

visitTimes - 访问次数

endpoint - 直链下载地址

##### raw

会直接跳转到下载的直链地址，可以直接放进第三方下载工具。

Endpoint: /raw/{link}

## 搭建开发环境

1. 修改 `utils/config.py` 中的相关配置。

2. 安装Python依赖:

   ```
   python -m pip install -r requirements.txt
   ```

3. 运行！

   ```
   uvicorn main:app --reload
   ```
