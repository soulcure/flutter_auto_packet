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

#argv: build.py 1.0.1 1 main false 3.7.3
print(sys.argv)
version = sys.argv[1]
build_number = sys.argv[2]
branch = sys.argv[3]
isBuildChannel = sys.argv[4]
flutterSdk = sys.argv[5]

# flutter build path
appPath = "build/ios/iphoneos/Runner.app"
apkPath = "build/app/outputs/flutter-apk/app-android-release.apk"

dateTime = time.strftime("%Y-%m-%d_%H:%M:%S")
outPutPath = "build/all/" + dateTime
destAppPath = f"{outPutPath}/droneId-{dateTime}.ipa"
destApkPath = f"{outPutPath}/droneId-{dateTime}.apk"

webPath = "/Users/ci/Desktop/package"
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
    os.system('rm ios/Flutter/Flutter.podspec')
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
    destWebPath = f"{webPath}/{dateTime}"
    if not os.path.exists(destWebPath):
        os.mkdir(destWebPath)

# build iOS
def buildIOS():
    print('🍺🍺🍺🍺===iOS开始打包===🍺🍺🍺🍺')

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
    print('🍺🍺🍺🍺===android开始打包===🍺🍺🍺🍺')

    os.system('fvm flutter build apk -t lib/main.dart --flavor android --target-platform=android-arm64 --release')

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
    tokenRes = requests.post("https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=ID&corpsecret=SECRET",
                             data=json.dumps({'app_id': "cli_9e62c8e53639100d", "app_secret": "xPM1CNYeqoDsXfDLFNvXygWZ58UYaiqL"}),
                             headers={"Content-Type": "application/json"})
    if tokenRes.status_code != 200 or tokenRes.json()['code'] != 0:
        qywechat_token = ''
        return qywechat_token
    qywechat_token = tokenRes.json()['access_token']
    return qywechat_token


# 上传图片到企业微信
def uploadImage(image_path):
    # 获取 token
    token = getToken()
    if len(token) == 0:
        return ''
    token = f'Bearer {token}'
    with open(image_path, 'rb') as f:
        image = f.read()
    resp = requests.post(
        url='https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN',
        headers={'Authorization': token},
        files={
            "image": image
        },
        data={
            "image_type": "message"
        },
        stream=True)
    resp.raise_for_status()
    content = resp.json()
    print(content)
    if content.get("code") == 0:
        data = content['data']
        image_key = data['image_key']
        return image_key
    else:
        raise Exception("Call Api Error, errorCode is %s" % content["code"])

# 发生文本信息
def sendMessage(content) :
    # 发送消息
    sendRes = requests.post(webhook,
                            data=json.dumps({"msg_type": "text", "content": {"text": content}}),
                            headers={"Content-Type": "application/json"})
    if sendRes.status_code != 200 or sendRes.json()['code'] != 0:
        print('企业微信消息发送失败')

# 发生富文本信息
def sendSuccessMessage(title,content,appUrl,appDevelopmentUrl,apkUrl,appImageKey,apkImageKey,log) :
    sendRes = requests.post(webhook,
                            data=json.dumps(
                                {
                                    "msgtype": "text",
                                    "content": {
                                        "post": {
                                            "zh_cn": {
                                                "title": title,
                                                "content": [
                                                    [{"tag": "text", "text":content}],
                                                    [{"tag": "text", "text":'iOS:'},{"tag": "a","text": "安装地址","href": appUrl},],
                                                    [{"tag": "text", "text":'iOS包:'},{"tag": "a","text": "下载地址","href": appDevelopmentUrl}],
                                                    [{"tag":"img","image_key":appImageKey}],
                                                    [{"tag": "text", "text":'android:'},{"tag": "a","text": "下载地址","href": apkUrl}],
                                                    [{"tag":"img","image_key":apkImageKey}],
                                                    [{"tag": "text", "text": "日志:\n" + log }]
                                                ]
                                            }
                                        }
                                    }
                                }),
                            headers={"Content-Type": "application/json"})
    if sendRes.status_code != 200 or sendRes.json()['code'] != 0:
        print('飞书消息发送失败')
    print(sendRes.json())


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
    file = open(f"{webPath}/{dateTime}/ipa.html", "w")
    file.write(content)
    file.close()

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
    file = open(f"{webPath}/{dateTime}/ipa.plist", "w")
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
        destWebPath = f"{webPath}/{dateTime}"
        shutil.move(destAppPath,destWebPath)
        shutil.move(destApkPath,destWebPath)
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


def buildChannelApk():
    # 构建32位包
    os.system('fvm flutter build apk --flavor android --release')
    path = 'build/app/outputs/flutter-apk/app-android-release.apk'
    destWebPath = f"{webPath}/{dateTime}/droneId-android-32.apk"
    if os.path.exists(path):
        shutil.move(path,destWebPath)
    else:
        print('apk 打包失败')
    # 构建渠道包
    channels = ['android','OP0S0N00666', 'BG0S0N00666', 'HW0S0N00666', 'MZ0S0N00666' ,'XM0S0N00662', 'TX0S0N70666']
    for channel in channels:
        os.system(f'fvm flutter build apk --flavor {channel} --release')
        path = f'build/app/outputs/flutter-apk/app-{channel}-release.apk'
        destWebPath = f"{webPath}/{dateTime}/droneId-{channel}.apk"
        if os.path.exists(path):
            shutil.move(path,destWebPath)
        else:
            print('apk 打包失败')


# 发渠道包消息
def sendChannelApkMessage() :
    content = f"""构建分支: {branch}
版本号: {version}+{build_number}"""
    # 发送消息
    sendRes = requests.post(webhook,
                            data=json.dumps(
                                {
                                    "msg_type": "post",
                                    "content": {
                                                "post": {
                                                    "zh_cn": {
                                                        "title": "渠道包",
                                                        "content": [
                                                            [{"tag": "text", "text":content}],
                                                            [{"tag": "text", "text":'模拟器+32位包:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-android-32.apk'},],
                                                            [{"tag": "text", "text":'官网:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-android.apk'},],
                                                            [{"tag": "text", "text":'oppo:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-OP0S0N00666.apk'},],
                                                            [{"tag": "text", "text":'步步高:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-BG0S0N00666.apk'},],
                                                            [{"tag": "text", "text":'华为:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-HW0S0N00666.apk'},],
                                                            [{"tag": "text", "text":'魅族:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-MZ0S0N00666.apk'},],
                                                            [{"tag": "text", "text":'小米:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-XM0S0N00662.apk'},],
                                                            [{"tag": "text", "text":'腾讯:'},{"tag": "a","text": "下载地址","href": f'{httpUrl}/{dateTime}/droneId-TX0S0N70666.apk'},],
                                                        ]
                                                    }
                                                }
                                            }
                                 }),
                            headers={"Content-Type": "application/json"})
    if sendRes.status_code != 200 or sendRes.json()['code'] != 0:
        print('企业微信消息发送失败')
    print(sendRes.json())










if __name__ == '__main__':
    print('开始构建项目...')
    print(f'版本号: {version}')

    # flutter 版本切换
    #os.system(f"fvm use {flutterSdk} --force")
    os.system("flutter --version")
    # 修改版本号
    change_yaml_version()
    # 清除缓存
    clear_cache()
    # 初始化
    init()

    if isBuildChannel == 'false' :
        # 构建iOS
        buildIOS()

        # 构建android
        buildAndroid()

        # 提交App
        uploadApp()

    else :
        # 构建渠道包
        buildChannelApk()
        sendChannelApkMessage()