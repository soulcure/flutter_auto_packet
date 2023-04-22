#!/usr/bin/python3
import json
import os
import qrcode
import re
import requests
import shutil
import subprocess
import sys
import time
import sys
import platform

#argv: build.py 1.0.1 2 main false 3.7.10
print(sys.argv)
version = sys.argv[1]
build_number = sys.argv[2]
branch = sys.argv[3]
flutterSdk = sys.argv[4]

# flutter build path
appPath = "build/ios/iphoneos/Runner.app"
apkPath = "build/app/outputs/flutter-apk/app-release.apk"

dateTime = time.strftime("%Y-%m-%d_%H_%M_%S")
outPutPath = "build/all/" + dateTime
destAppPath = f"{outPutPath}/droneId_v{version}_{build_number}.ipa"
destApkPath = f"{outPutPath}/droneId_v{version}_{build_number}.apk"

httpsUrl = "https://192.168.112.40:8001"
httpUrl = "http://192.168.112.40:8000"
logDay = 5

#企业微信群机器人web hook url
webhook = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa"

# 飞书 token
qywechat_token = ''

# 修改版本号
def change_yaml_version():
    print('修改版本号')
    file = open("pubspec.yaml", "r")
    content = file.read()
    file.close()
    # 处理数据
    arr = content.split()
    index = arr.index('version:')
    currentVersion = arr[index+1]
    content = content.replace(currentVersion,f'{version}+{build_number}',1)
    # 修改数据
    file = open("pubspec.yaml", "w")
    file.write(content)
    file.close()

# 清除缓存
def clear_cache():
    print('清除缓存')
    if os.path.exists('ios/Flutter/Flutter.podspec'):
        os.remove('ios/Flutter/Flutter.podspec')   #删除文件
    os.system('fvm flutter clean')
    if os.path.exists(appPath):
        shutil.rmtree(appPath)
    if os.path.exists(apkPath):
        os.unlink(apkPath)

# 初始化
def init():
    print('初始化')
    if not os.path.exists("build"):
        os.mkdir("build")
    if not os.path.exists("build/all"):
        os.mkdir("build/all")
    os.mkdir(outPutPath)

# build iOS
def buildIOS():
    print('🍏🍏🍏🍏===iOS开始打包===🍏🍏🍏🍏')

    os.system('fvm flutter build ipa -t lib/main.dart --release')

    if os.path.exists(appPath):
        print('fvm flutter build ios success')
        os.chdir('ios')
        if os.path.exists("build/ios.ipa"):
            shutil.move("build/ios.ipa",f"../{destAppPath}")
        else:
            print('生成ipa失败')
        os.chdir('..')
    else:
        print('打包失败')

    # 清空fastlane缓存
    if os.path.exists("ios/build"):
        shutil.rmtree("ios/build")

def buildAndroid():
    print('🤖🤖🤖🤖===android开始打包===🤖🤖🤖🤖')

    os.system('fvm flutter build apk -t lib/main.dart --target-platform=android-arm64 --release')

    if os.path.exists(apkPath):
        print('apk 打包成功')
        shutil.move(apkPath,destApkPath)
    else:
        print('apk 打包失败')


# 获取企业微信token
def getToken():
    global qywechat_token
    if len(qywechat_token) > 0:
        return qywechat_token
    
    Url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    Data = {
            "corpid": "cli_9e62c8e53639100d",
            "corpsecret": "xPM1CNYeqoDsXfDLFNvXygWZ58UYaiqL"
    }
    r = requests.get(url=Url, params=Data)
    qywechat_token = r.json()['access_token']
    return qywechat_token

##上传到图片素材  图片url
def uploadImage(path): 
    Gtoken = getToken()
    img_url = "https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg?access_token={}".format(Gtoken)
    files = {'media': open(path, 'rb')}
    r = requests.post(img_url, files=files)
    re = json.loads(r.text)
    # print("media_id: " + re['media_id'])
    return re['url']


# 发生文本信息
def sendMessage(content) :
    # 发送消息
    sendRes = requests.post(webhook,
                            data=json.dumps({"msg_type": "text", "content": {"text": content}}),
                            headers={"Content-Type": "application/json"})
    if sendRes.status_code != 200 or sendRes.json()['code'] != 0:
        print('企业微信消息发送失败')

# 发生富文本信息
def sendSuccessMessage(title,content,appUrl,appDevelopmentUrl,apkUrl,appImageUrl,apkImageKey,log) :
    url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(getToken())
    data = {
        "toparty": "",
        "msgtype": "text",
        "agentid": "",
        "text": {
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [{"tag": "text", "text":content}],
                            [{"tag": "text", "text":'iOS:'},{"tag": "a","text": "安装地址","href": appUrl},],
                            [{"tag": "text", "text":'iOS包:'},{"tag": "a","text": "下载地址","href": appDevelopmentUrl}],
                            [{"tag":"img","image_key":appImageUrl}],
                            [{"tag": "text", "text":'android:'},{"tag": "a","text": "下载地址","href": apkUrl}],
                            [{"tag":"img","image_key":apkImageKey}],
                            [{"tag": "text", "text": "日志:\n" + log }]
                        ]
                    }
                }
            }
        },
        "safe": "0"
    }
    result = requests.post(url=url, data=json.dumps(data))
    return result.text


def writeIpaHtml():
    content = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>droneId</title>
        </head>
        <body>
            <h1 style="font-size:80pt">如果点击无法下载安装，请复制超链接到浏览器中打开<h1/>
            <h1 style="font-size:100pt">
                <a title="iPhone" href="itms-services://?action=download-manifest&url={httpsUrl}/{dateTime}/ipa.plist">Iphone Download</a>
            <h1/>
        </body>
    </html>"""
    file = open(f"{outPutPath}/{dateTime}/ipa.html", "w")
    file.write(content)
    file.close()


# plist IOS企业用户提供的无线分发安装方式所使用的协议
# <key>url</key>
# {httpsUrl}/{dateTime}/droneId-{dateTime}.ipa  //ipa文件下载地址

# <key>bundle-identifier</key>
# <string>com.idreamsky.droneId</string> //唯一标识符

# <key>bundle-version</key>
# <string>{version}</string>
def writeIpaPlist():
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>items</key>
        <array>
            <dict>
                <key>assets</key>
                <array>
                    <dict>
                        <key>kind</key>
                        <string>software-package</string>
                        <key>url</key>
                        <string>{httpsUrl}/{dateTime}/droneId-{dateTime}.ipa</string>
                    </dict>
                </array>
                <key>metadata</key>
                <dict>
                    <key>bundle-identifier</key>
                    <string>com.idreamsky.droneId</string>
                    <key>bundle-version</key>
                    <string>{version}</string>
                    <key>kind</key>
                    <string>software</string>
                    <key>title</key>
                    <string>droneId</string>
                </dict>
            </dict>
        </array>
    </dict>
    </plist>"""
    file = open(f"{outPutPath}/{dateTime}/ipa.plist", "w")
    file.write(content)
    file.close()

def getLastCommit():
    if os.path.exists("log.txt"):
        file = open("log.txt", "r")
        content = file.readline()
        file.close()
        logRes = content.split(' | ')
        if len(logRes) >= 2 and re.match(r'^\w+$', logRes[0]):
            return logRes[0]
        else:
            return None
    else:
        return None

def getLog():
    logTypes = {}
    lastCommit = getLastCommit()
    print('lastCommit：', lastCommit)
    query = [
        'git',
        'log',
        '--since=5 days ago',
        '--no-merges',
        '--pretty=format:%H | %ci | %s | [%an]'
    ]
    if lastCommit is not None:
        query = [
            'git',
            'log',
            lastCommit + '..HEAD',
            '--no-merges',
            '--pretty=format:%H | %ci | %s | [%an]'
        ]
    data_string = subprocess.check_output(query).decode()
    file = open("log.txt", "w+")
    file.write(data_string)
    for log in data_string.split('\n'):
        logRes = log.split(' | ', 3)
        if len(logRes) < 2:
            continue
        log = logRes[2]
        splitRes = log.split(':')
        if len(splitRes) < 2:
            continue
        logType = splitRes[0]
        logText = splitRes[1]
        logType = logType if not logType.startswith('fix') else 'fix'
        logs = logTypes.get(logType)
        if logs is None:
            logTypes.update({logType: [logText]})
        else:
            logs.append(logText)
    tempList = []
    for (k, v) in logTypes.items():
        tempList.extend([k])
        tempList.extend(v)

    return '(nothing update)' if len(tempList) == 0 else '\n'.join(tempList)


def uploadApp():
    if os.path.exists(destAppPath) and os.path.exists(destApkPath) :
        writeIpaHtml()
        writeIpaPlist()

        # 生成二维码 和 上传图片
        appUrl = f'{httpUrl}/{dateTime}/ipa.html'
        ipaUrl = f'{httpUrl}/{dateTime}/droneId-{dateTime}.ipa'
        apkUrl = f'{httpUrl}/{dateTime}/droneId-{dateTime}.apk'
        img = qrcode.make(data=appUrl)
        img.save('app.jpg')
        img = qrcode.make(data=apkUrl)
        img.save('apk.jpg')
        appUrlKey = uploadImage("app.jpg")
        apkUrlKey = uploadImage("apk.jpg")
        log = getLog()

        content = f"""构建分支: {branch}
版本号: {version}+{build_number}"""
        # 安卓包下载地址: {serverBaseUrl}/{dateTime}/droneId-{dateTime}.apk
        # iOS包下载地址: {serverBaseUrl}/{dateTime}/ipa.html
        sendSuccessMessage('🍺🍺🍺构建成功🍺🍺🍺',content,appUrl,ipaUrl,apkUrl,appUrlKey,apkUrlKey,log)
    else:
        sendMessage('💣💣💣构建失败💣💣💣')




if __name__ == '__main__':
    print('开始构建项目...')
    print(f'版本号: {version}')

    # flutter 版本切换
    os.system(f"fvm use {flutterSdk} --force")
    os.system("fvm flutter --version")
    # 修改版本号
    change_yaml_version()
    # 清除缓存
    clear_cache()
    # 初始化
    init()

    # 构建iOS
    if(platform.system() =="darwin"):
        buildIOS()

    # 构建android
    buildAndroid()

    # 提交App
    uploadApp()

