# This function is just used for person who wants to apply for themselves.
# DO NOT use this function unless you can not apply manually.
import configparser
import json
import os
import time
from datetime import datetime

import requests


class User:
    def __init__(self):
        self.wecom_on, self.wecom_cid, self.wecom_aid, self.wecom_secret, self.wecom_touid= \
        list(zip(*self.get_config()[0]))[1]
        self.officeID, self.date_start, self.date_end = list(zip(*self.get_config()[1]))[1]

    @staticmethod
    def get_config():
        pre_dir = os.path.split(os.path.realpath(__file__))[0]
        config_path = os.path.join(pre_dir, 'config.ini')
        # print(config_path)
        conf = configparser.RawConfigParser()
        conf.read(config_path)
        user_wecom = conf.items('UserWecom')
        user_info = conf.items('UserInfo')
        return user_wecom, user_info

    def send_to_wecom(self, text):
        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.wecom_cid}&corpsecret=" \
                        f"{self.wecom_secret}"
        response = requests.get(get_token_url).content
        access_token = json.loads(response).get('access_token')
        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": self.wecom_touid,
                "agentid": self.wecom_aid,
                "msgtype": "text",
                "text": {
                    "content": text
                },
                "duplicate_check_interval": 600
            }
            response = requests.post(send_msg_url, data=json.dumps(data)).content
            return response
        else:
            return False


class Status:
    def __init__(self):
        self.available_item = ''
        self.data_collated = []
        self.retry = 0

    def send_request(self):
        try:
            response = requests.get(
                url="https://eservices.es2.immd.gov.hk/surgecontrolgate/ticket/getSituation",
                headers={
                    "Host": "eservices.es2.immd.gov.hk",
                    "Connection": "keep-alive",
                    "sec-ch-ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"114\", \"Microsoft Edge\";v=\"114\"",
                    "Accept": "*/*",
                    "X-Requested-With": "XMLHttpRequest",
                    "sec-ch-ua-mobile": "?0",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.41",
                    "sec-ch-ua-platform": "\"macOS\"",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty",
                    "Referer": "https://eservices.es2.immd.gov.hk/es/quota-enquiry-client/?l=zh-CN&appId=579",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                    "x-forwarded-for": "1.1.1.1",
                },
            )
            content = response.json()
        except requests.exceptions.RequestException:
            print(str(datetime.now())[0:19] + "\n-----------\n网络错误！请检查网络")
            self.retry += 1
            return False
        self.collate_data(content)

    def collate_data(self, content):
        if content is None:
            print(str(datetime.now())[0:19] + "\n-----------\n未从服务器获取有效信息")
            self.retry += 1
            return False
        for item in content["data"]:
            if any(item[key] in ('quota-y', 'quota-g') for key in ('quotaR', 'quotaK')):
                self.data_collated.append(item)
        if self.data_collated:
            print(str(datetime.now())[0:19] + '\n-----------\n部分地区有空位，正在检测是否符合...')
            print(self.data_collated)
        else:
            print(str(datetime.now())[0:19] + '\n-----------\n仍无有效名额，持续监测中' + '\n-----------\n')

    def collation_details(self, user):
        region_info = {"RHK": '港岛办事处', "RKO": '九龙办事处', "RKT": '观塘办事处', "FTO": '火炭办事处', "TMO": '屯门办事处', "YLO": '元朗办事处'}
        status_info = {"quota-r": '🔺已满', "quota-y": '🟨少量名额', "quota-g": '🟢尚有名额'}
        for data in self.data_collated:
            # print(data)
            if int(time.mktime(time.strptime(user.date_start, '%d/%m/%Y'))) <= int(time.mktime(time.strptime(data["date"], '%m/%d/%Y'))) <= int(time.mktime(time.strptime(user.date_end, '%d/%m/%Y'))):
                if data["officeId"] in user.officeID:
                    time_format = time.strftime('%Y-%m-%d', time.strptime(data["date"], '%m/%d/%Y'))
                    self.available_item = self.available_item + f'\n-----------\n日期：{time_format}\n位置： {region_info[data["officeId"]]}\n一般时段：{status_info[data["quotaR"]]}\n延长时段：{status_info[data["quotaK"]]}'


def main():
    user = User()
    status = Status()
    print(str(datetime.now())[0:19] + '\n-----------\n初始化完成...')
    user.send_to_wecom(str(datetime.now())[0:19] + '\n-----------\nHK_Apply初始化完成...') if user.wecom_on else print(str(datetime.now())[0:19] + " 用户关闭了企业微信通知...")
    while not status.available_item:
        status.send_request()
        status.collation_details(user)
        if status.available_item:
            print(str(datetime.now())[0:19] + '\n暂无符合的位置信息，继续监控\n')
            time.sleep(5)
        # print(str(datetime.now())[0:19] + str(status.available_item))
    print(str(datetime.now())[0:19] + str(status.available_item))
    user.send_to_wecom(str(datetime.now())[0:19] + status.available_item +
                       '\n一键直达：https://www.gov.hk/sc/apps/immdicbooking2.htm') if user.wecom_on \
        else print(str(datetime.now())[0:19] + " 用户关闭了企业微信通知...")


if __name__ == '__main__':
    main()
