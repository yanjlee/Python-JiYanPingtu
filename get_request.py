#coding=utf-8
from PIL import Image
import os
import json
from io import BytesIO

#  开启命令：mitmdump --mode upstream:http://default-upstream-proxy.local:8080/ -s xxx.py
# def request(flow):
#     # 这里配置二级代理的ip地址和端口
#     if flow.live:
#         proxy = ("110.52.235.54", 9999)
#         flow.live.change_upstream_proxy_server(proxy)

def response(flow):
    # 通过抓包软包软件获取请求的接口

    try:
        os.mkdir('captcha')
    except:
        pass

    #抓取请求的信息，第一次请求图片url信息
    if 'https://api.geetest.com/get.php?is_next=true&type=slide3&' in flow.request.url: #第一次请求
        file = 'request'
        with open('./captcha/%s.txt'%file,'w') as f:
            f.write(flow.response.text)

    # 抓取请求的信息，刷新请求图片url信息
    if 'https://api.geetest.com/refresh.php?gt=' in flow.request.url: #第一次请求
        file = 'request'
        with open('./captcha/%s.txt'%file,'w') as f:
            f.write(flow.response.text)


    if '.webp' in flow.request.url:
        """抓取图片请求url"""
        if '/bg' in flow.request.url: #带缺口的乱码图片
            nf = flow.request.url.split("/")[-1].split('.')[0]
            file = "./captcha/%s/%s" % (flow.request.url.split("/")[-3], nf)
            image = Image.open(BytesIO(flow.response.content))
            image.save('%s.jpg'%file)

            full = flow.request.url.split("/")[-3]
            content = json.dumps(dict({full:nf}), ensure_ascii=False) + "\n"
            with open("./captcha/info.json", 'w') as f:
                f.write(content)

        else:
            try: #
                os.mkdir('./captcha/%s'%flow.request.url.split("/")[-2])
            except:
                pass
            file = "./captcha/%s/%s" % (flow.request.url.split("/")[-2], flow.request.url.split("/")[-2])
            image = Image.open(BytesIO(flow.response.content))
            image.save('%s.jpg' % file)
