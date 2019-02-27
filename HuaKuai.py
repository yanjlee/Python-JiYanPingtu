#coding=utf-8

"""破解极验验证码，采用selenium+chrome"""
from time import sleep
from PIL import Image
import re
import json
import cPickle
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options() #浏览器配置
from selenium.webdriver.support.ui import WebDriverWait #隐式等待
from selenium.webdriver.common.by import By #找到元素
from selenium.webdriver.support import expected_conditions as EC #等待的条件
from selenium.webdriver.common.action_chains import  ActionChains #鼠标动作

class JiYan():
    def __init__(self,url):
        self.url = url
        # options = webdriver.ChromeOptions()
        # proxy = "http://119.101.116.111:9999"
        # options.add_argument('--proxy-server='+proxy)  # 代理
        options.add_argument('--user-data-dir=/home/ubuntu/.config/google-chrome/') #加载浏览器配置文件
        # options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver,3)

    def login(self):
        """登录"""
        self.driver.get(self.url) #请求url
        email = self.wait.until(EC.presence_of_element_located((By.ID,'email')))
        password = self.wait.until(EC.presence_of_element_located((By.ID,'password')))
        email.send_keys('1234')
        email.send_keys('5678')
        sleep(1)
        password.send_keys('1234')
        password.send_keys('5678')
        sleep(1) #等待验证按钮的出现
        check = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME,'geetest_radar_tip_content')))
        try:
            if check: #如果验证按钮存在
                check.click()  # 点击验证按钮
                sleep(1) #等待验证码出现
                self.repetition_auto(check) #如果验证码出现则处理验证码
        except Exception as e:
            print(e)
        finally:
            self.driver.quit()

    def check_login(self,check):
        """处理用户账号和密码错误"""
        print('验证成功')
        submit = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'login-btn')))
        submit.click() #点击登录按钮
        sleep(1) #等待结果出现
        try:  # 用户名格式错误
            error = self.wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="backend-message"]'))).text
            if '用户名格式错误' in error.encode('utf-8'):
                check.click()  # 用户格式错误，则点击验证按钮继续验证
        except:
            print('登录成功')

    def repetition_auto(self,check):
        """验证失败继续验证"""
        while True:  # 如果验证失败继续验证
            #获取点击验证按钮后的结果
            result = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'geetest_radar_tip_content'))).text
            if result.encode('utf-8') == '点击按钮进行验证':  # 验证成功:
                self.check_login(check) #处理点击登录按钮后的的过程
                # break
            else:
                pullbg, bg1 = self.get_url()  # 从文件中读取请求乱码图片url
                d,track = self.check() #验证验证码
                sleep(1) #等待结果出现
                try:
                    result = self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'geetest_radar_tip_content'))).text

                    if result.encode('utf-8') == '请完成验证':  # 验证不成功
                        print('验证不成功')
                        pullbg, bg2 = self.get_url()  # 从文件中读取请求乱码图片url
                        print(bg1, bg2)
                        if bg1 != bg2: #读取两次记录判断验证码是否一样，如果不一样则代表验证被识别，验证码自动刷新
                            # print(d,track)
                            raw_input(':')
                            pass
                        else:
                            refresh = self.wait.until(
                                EC.presence_of_element_located((By.XPATH, '//a[@class="geetest_refresh_1"]')))
                            refresh.click()  # 手动刷新验证码

                    if result.encode('utf-8') == '点击按钮进行验证': # 验证成功
                        pullbg, bg = self.get_url()  # 从文件中读取请求乱码图片url
                        content = json.dumps(dict({
                            'pullbg':pullbg.split('/')[-1],
                            'bg': bg.split('/')[-1],
                            'distance':d,
                            'track':track
                        }), ensure_ascii=False) + "\n"
                        #保存相应验证码的轨迹记录
                        with open("./captcha/track.json", 'ab+') as f:
                            f.write(content)
                        self.check_login(check)#处理点击登录按钮后的的过程
                        # break

                    if result.encode('utf-8') == '尝试过多':
                        print('尝试过多')
                        result = self.wait.until(
                            EC.presence_of_element_located(
                                (By.XPATH, '//div/span[@class="geetest_reset_tip_content"]')))
                        result.click() #尝试过多重新点击验证按键
                except:  # 验证失败
                    pass

    def check(self):
        """处理出现的验证码"""
        sleep(2) #等待验证码出现和代理脚本把请求信息保存
        sliding = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_slider_button'))) #获取滑块
        d = self.get_d() #获取滑块移动距离
        track = self.get_track(d) #根据移动距离获取滑块轨迹
        self.move_to_gap(sliding, track) # 拖动滑块
        return d,track

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 初速度
        v = 0
        a = 0
        t = 0
        while current < distance:
            if distance < 100: #缺口位置小于100，则速度放慢
                # 计算间隔
                t = 0.1 #在0.1秒内的滑块速度的变化
                if current <= distance*(6.0/10.0): #当滑块移动的距离小于等于总距离的十分之六，则以加速度4加速滑行
                    # 加速度为正4
                    a = 4
                if current > distance * (6.0 / 10.0):#当滑块移动的距离大于总距离的十分之六，则以加速度-8减速滑行
                    a = -8
            if distance >= 100:
                t = 0.2
                if current <= distance*(7.0/10.0):
                    # 加速度为正2
                    a = 2
                if current > distance * (7.0 / 10.0):
                    a = -7
            # 初速度v0，把当前的瞬时速度作为初速度
            v0 = v
            # 当前瞬时速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2，在一定时间间隔内以初速度为v0加速度为a移动的距离
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # print('d:%s'%distance, 'current:%s' %current, 'move:%s'%move,'v0:%s'%v0)
            # 加入轨迹
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.driver).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform() #拖动滑块
        sleep(0.5)
        ActionChains(self.driver).release().perform() #释放滑块

    def get_gap(self,image1, image2):
        """
        获取像素点不一样的位置
        :param image1:
        :param image2:
        :return:
        """
        block_location = []
        left = 0  #图片最左侧的位置
        #对比规则：从上往下，从左往右依次扫描对比
        for i in range(left, image1.size[0]): #size[0] x轴位置
            for j in range(image1.size[1]): #size[1] x轴位置
                if not self.is_pixel_equal(image1, image2, i, j): #如果像素点不一致，则把该x,y轴位置记录下来
                    block_location.append((i, j))
        return block_location

    def is_pixel_equal(self,image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 70  # 像素点的阀值，小于这个值则代表两两张图片的像素点一样，则继续比较
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold: #两个像素点中任意一个RGB值的R,G,B小于阀值，则代表像素点一致
            return True
        else:
            return False

    def get_dist(self,full, notfull):
        # 合并图片使用
        location_list = cPickle.load(open('location_list.pkl')) #合成规则
        new_image1 = self.get_merge_image(location_list, full) #合成第一张图片
        new_image2 = self.get_merge_image(location_list, notfull) #合成第二张图片
        return new_image1, new_image2

    def get_merge_image(self,location_list, image):
        """根据合成规则和参数，把乱码图片合成正确的图片"""
        im_list_upper = []
        im_list_down = []
        for location in location_list:
            if location['y'] == -58: #上半部分，从乱码图片中依次取出每一部分的图片放入列表中
                aa = image.crop((
                    abs(location['x']), 80,
                    abs(location['x']) + 10, 138)) #切出范围大小的小图片
                im_list_upper.append(aa)

            if location['y'] == 0: #下半部分，从乱码图片中依次取出每一部分的图片放入列表中
                im_list_down.append(image.crop((
                    abs(location['x']), -21,
                    abs(location['x']) + 10, 80)))#切出范围大小的小图片

        # 新建一张图片，通过小图片合成新的图片
        new_im = Image.new('RGBA', (258, 159))
        # 从图片左上角(0,0)开始拼接
        # 上部分拼接
        x_offset = 0 #x轴方向
        for im in im_list_upper: #y轴不变，x轴增加
            new_im.paste(im, (x_offset, 0))  # 将im 粘贴到new_im 位置(x_offset,0)
            x_offset += im.size[0]

        # 下部分拼接
        x_offset = 0 #x轴方向
        for im in im_list_down: #y轴不变，x轴增加
            new_im.paste(im, (x_offset, 58))  # 将im 粘贴到new_im 位置(x_offset,58)
            x_offset += im.size[0]
        return new_im

    def get_url(self):
        """从文件中读取请求乱码图片url"""
        with open('./captcha/request.txt', 'r') as f: #包含了请求所有验证码的信息
            content = f.read()
        pullbgrule = 'pictures/gt/\w+/\w+.jpg'
        pullbg = re.search(pullbgrule,content).group() #没有缺口乱码图片的url
        bgrule = 'pictures/gt/\w+/bg/\w+.jpg'
        bg = re.search(bgrule, content).group() #有缺口乱码图片的url
        return pullbg,bg

    def get_d(self):

        pullbg, bg = self.get_url() #从文件中读取请求乱码图片url
        for pullnum, notpullnum in json.load(open('./captcha/info.json')).items(): #本地乱码图片的路径
            if pullbg.split('/')[-1] == pullnum+'.jpg' and bg.split('/')[-1] == notpullnum+'.jpg':
                #判断请求url乱码图片的名字是否和本地保存乱码图片的名字一致，
                #如果一致则从本地上获取乱码图片对比像素点获取滑块移动距离
                path = './captcha/%s/' % (pullnum)
                fulpath = path + pullnum + '.jpg'
                notfulpath = path + notpullnum + '.jpg'
                pull = Image.open(fulpath)
                notfull = Image.open(notfulpath)
                return self.get_d2(pull,notfull) #从本地上获取乱码图片对比像素点获取滑块移动距离

            else:
                #如果不一致则发出url请求获取乱码图片对比像素点获取滑块移动距离
                pullbgurl = 'https://static.geetest.com/'+pullbg
                bgurl = 'https://static.geetest.com/' + bg
                headers = {
                    'Origin':'ttps: // account.geetest.com',
                    'Referer':'https://account.geetest.com/login',
                    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)',
                }
                response = requests.get(pullbgurl,headers=headers) #重新发出请求
                fullimae = Image.open(BytesIO(response.content))
                response = requests.get(bgurl, headers=headers)
                bgimae = Image.open(BytesIO(response.content))
                return self.get_d2(fullimae,bgimae)

    def get_d2(self,pull,notpull):
        """传入两张乱码图片，合成新的两张图片用来对比每个像素，确定缺口左侧的x轴位置"""
        image1, image2 = self.get_dist(pull, notpull) #传入乱码图片，返回正确的合成图片
        block_location = self.get_gap(image1, image2)  # 对比两张合成图片的每个像素,返回不一样的x,y位置列表(x,y)
        # y = []
        # for i in block_location: #目的是把y轴方向最大的值取出来
        #     y.append(i[1])
        left = block_location[0][0]
        # top = min(y)
        # right = block_location[-1][0]
        # bottom = max(y)
        # block_image = image2.crop((left, top, right, bottom))  # 把缺口形状切割出来
        # block_image.show()
        # x, y = right - left, bottom - top
        return int(left - 7) #由于合成图片变形和滑块位置不在最左侧，所以需补偿滑动距离的误差

def test_ip():
    proxy = "http://119.101.116.111:9999"
    # options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=' + proxy)  # 代理
    chrome_options.add_argument('--user-data-dir=/home/ubuntu/.config/google-chrome/')  # 加载浏览器配置文件
    chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get('http://httpbin.org/get')
    print(driver.page_source)
    raw_input(':')
    driver.quit()

if __name__ == '__main__':
    url = 'https://account.geetest.com/login'
    jiyan  = JiYan(url)
    jiyan.login()
    # test_ip()