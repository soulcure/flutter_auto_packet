import requests
import json
from threading import Thread
import cv2
import os


class Wechat_Info():
    def __init__(self):
        self.partyID = ''
        self.corpID = ''
        self.secret = ''
        self.agentID = ''
        self.token = None
        self.pic = None

    def __get_token(self, corpid, secret):
        Url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        Data = {
            "corpid": corpid,
            "corpsecret": secret
        }
        r = requests.get(url=Url, params=Data)
        token = r.json()['access_token']
        return token

    def send_message(self, message):
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(
            self.__get_token(self.corpID, self.secret))
        data = {
            "toparty": self.partyID,
            "msgtype": "text",
            "agentid": self.agentID,
            "text": {
                "content": message
            },
            "safe": "0"
        }
        result = requests.post(url=url, data=json.dumps(data))
        return result.text

    def get_media_url(self, path):  ##上传到图片素材  图片url
        Gtoken = self.__get_token(self.corpID, self.secret)
        img_url = "https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg?access_token={}".format(Gtoken)
        files = {'media': open(path, 'rb')}
        r = requests.post(img_url, files=files)
        re = json.loads(r.text)
        # print("media_id: " + re['media_id'])
        return re['url']

    def send_pic(self, pic_path):
        img_url = self.get_media_url(pic_path)
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(
            self.__get_token(self.corpID, self.secret))
        data = {
            "toparty": self.partyID,
            "msgtype": "text",
            "agentid": self.agentID,
            "text": {
                "content": img_url
            },
            "safe": "0"
        }
        result = requests.post(url=url, data=json.dumps(data))
        return result.text

    def send_violence_warning(self, pic_path):
        img_url = self.get_media_url(pic_path)
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}".format(
            self.__get_token(self.corpID, self.secret))
        data = {
            "toparty": self.partyID,
            "msgtype": "text",
            "agentid": self.agentID,
            "text": {
                "content": '【管理员注意】，有校园暴力行为发生，请及时处理！监控图片>>' + img_url
            },
            "safe": "0"
        }
        result = requests.post(url=url, data=json.dumps(data))
        return result.text

    def send_violence_warning_read_path_from_class(self):
        pic_path = 'temp.jpg'
        cv2.imwrite(pic_path, self.pic)
        self.send_violence_warning(pic_path)
        os.remove(pic_path)

    def send_violence_warning_in_new_thread(self, pic):
        self.pic = pic
        thread = Thread(target=self.send_violence_warning_read_path_from_class)
        thread.start()



if __name__ == '__main__':
    wechat_info = Wechat_Info()
    # result = wechat_info.send_message('微信测试_2020')
    # result = wechat_info.send_pic('C:\\Users\\JiaDing\\Desktop\\pic.jpg')
    result = wechat_info.send_violence_warning('C:\\Users\\JiaDing\\Desktop\\pic.jpg')
    print(result)
