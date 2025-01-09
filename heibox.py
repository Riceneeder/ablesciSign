import os
import requests
import time
import base64
try:
    import setting as url
except ImportError:
    log.error("The 'setting' module is missing or does not contain the required attributes.")
    raise
from log import Log
from sendNotify import send
import random

log = Log()

# 小黑盒签到
class XiaoHeiHe():
    def __init__(self,SignToken) -> None:
        self.Xiaoheihe = SignToken['XiaoHeiHe'].get('cookie', '')
        self.imei = SignToken['XiaoHeiHe'].get('imei', '')
        self.heybox_id = SignToken['XiaoHeiHe'].get('heybox_id', '')
        self.version = SignToken['XiaoHeiHe'].get('version', '')
        self.n = self.get_nonce_str()
        self.t = int(time.time())
        #self.u = "/task/sign"

    def get_nonce_str(self,length: int = 32) -> str:
            """
            生成随机字符串
            参数:
                length: 密钥参数
            返回:
                str: 随机字符串
            """
            source = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            result = "".join(random.choice(source) for _ in range(length))
            return(result)

    def hkey(self,key):
        params={"urlpath": key, "nonce": self.n, "timestamp": self.t}
        zz = requests.get(url.XiaoHeiHe_Hkey,params=params).text
        return zz

    def params(self,key):
        p = {
            "_time":self.t,
            "hkey":self.hkey(key),
            "nonce":self.n,
            "imei":self.imei,
            "heybox_id":self.heybox_id,
            "version":self.version,
            "divice_info":"M2012K11AC",
            "x_app":"heybox",
            "channel":"heybox_xiaomi",
            "os_version":"13",
            "os_type":"Android"
        }
        return p

    def head(self):
        head = {
            "User-Agent":"Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36 ApiMaxJia/1.0",
            "cookie":self.Xiaoheihe,
            "Referer":"http://api.maxjia.com/"
        }
        return head

    def b64encode(self,data: str) -> str:
        result = base64.b64encode(data.encode('utf-8')).decode('utf-8')
        return(str(result))

    def getpost(self):
        req = requests.get(
            url=url.XiaoHeiHe_News,
            params=self.params("/bbs/app/feeds/news"),
            headers=self.head()
            ).json()['result']['links'][1]['linkid']
        def click(link_id):
            head = self.params("/bbs/app/link/share/click")
            head['h_src'] = self.b64encode('news_feeds_-1')
            head['link_id'] = link_id
            head['index'] = 1
            req = requests.get(url=url.XiaoHeiHe_Click,params=head,headers=self.head()).json()['status']
            if req == "ok":
                log.info("分享成功")
                msg_req = "分享成功"
            else:
                log.info("分享失败")
                msg_req = "分享失败"
            return msg_req
        def check():
            head =  self.params("/task/shared/")
            head['h_src'] = self.b64encode('news_feeds_-1')
            head['shared_type'] = 'normal'
            req = requests.get(url=url.XiaoHeiHe_Check,params=head,headers=self.head()).json()['status']
            if req == "ok":
                log.info("检查分享成功")
                msg_req = "检查分享成功"
            else:
                log.info("检查分享失败")
                msg_req = "检查分享失败"
            return msg_req
        return click(req)+"\n"+check()

    def Sgin(self):
        if self.Xiaoheihe != "":
            try:
                req = requests.get(
                    url=url.XiaoHeiHe_SginUrl,
                    params=self.params("/task/sign/"),
                    headers=self.head()
                    ).json()
                fx = self.getpost()
                if req['status'] == "ok":
                    if req['msg'] == "":
                        log.info("小黑盒:已经签到过了")
                        return fx+"\n已经签到过了"
                    else:
                        log.info(f"小黑盒:{req['msg']}")
                        return {fx} + "\n" + req['msg']
                else:
                    log.info(f"小黑盒:签到失败 - {req['msg']}")
                    return f"{fx}\n签到失败 - {req['msg']}"   
            except Exception as e:
                log.info(f"小黑盒:出现了错误,错误信息{e}")
                return f"出现了错误,错误信息{e}"
        else:
            log.info("小黑盒:没有配置cookie")
            return "没有配置cookie"

# 从GitHub Workflow环境变量中获取小黑盒签到所需的cookie
def GetXiaoHeiSignToken():
    SignToken = {
        "XiaoHeiHe": {
            "cookie": os.environ.get('XIAOHEICOOKIE'),
            "imei": os.environ.get('XIAOHEIIMEI'),
            "heybox_id": os.environ.get('XIAOHEIHEYBOXID'),
            "version": os.environ.get('XIAOHEIVERSION')
        }
    }
    return SignToken

def main():
    SignToken = GetXiaoHeiSignToken()
    heybox = XiaoHeiHe(SignToken)
    msg = heybox.Sgin()
    log.info(msg)
    send("小黑盒",msg)

if __name__ == "__main__":
    main()
