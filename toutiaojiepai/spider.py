import requests
from urllib.parse import urlencode
from requests import codes
import os
from hashlib import md5
from multiprocessing.pool import Pool
import re


def get_page(offset):
    headers = {
        'cookie': 'tt_webid=6727175009917994509; WEATHER_CITY=%E5%8C%97%E4%BA%AC; tt_webid=6727175009917994509; csrftoken=5109486c3f4cf5d73eb3d185044774e9; __tasessionId=vodb6ghh11566386218716; RT="z=1&dm=toutiao.com&si=slmz8xt12bi&ss=jzl37cx7&sl=5&tt=0&nu=854c79f64def5cc87bdb66c39d3976ec&cl=34nw&obo=5&ld=2pgpd&r=4d707aab8209c38c1dfc5a11a3ddf8e5&ul=2pgpg&hd=2pgsn"; s_v_web_id=62c1ceee11848508975b08334a0403cd',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'referer': 'https://www.toutiao.com/search/?keyword=%E8%A1%97%E6%8B%8D',
    }
    params = {
        'aid': 24,
        'app_name': 'web_search',
        'offset': offset,
        'format': 'json',
        'keyword': '街拍',
        'autoload': 'true',
        'count': 20,
        'en_qc': 1,
        'cur_tab': 1,
        'from': 'search_tab',
        'pd': 'synthesis',
    }
    base_url = 'https://www.toutiao.com/api/search/content/?'
    url = base_url + urlencode(params)
    try:
        resp = requests.get(url, headers=headers)
        if codes.ok == resp.status_code:
            return resp.json()
    except requests.ConnectionError:
        return None


def get_images(json):
    if json.get('data'):
        data = json.get('data')
            if item.get('title') is None:
                continue
            title = re.sub('[\t|]', '', item.get('title'))
            images = item.get('image_list')
            if images:
                for image in images:
                    origin_image = re.sub("list.*?pgc-image", "large/pgc-image", image.get('url'))  #把缩略图url替换成大图
                    yield {
                        'image': origin_image,
                        'title': title
                    }


def save_image(item):
    img_path = 'img' + os.path.sep + item.get('title')  #os.path.sep 路径分隔符
    if not os.path.exists(img_path):    #os.path.exists()判断括号里的文件是否存在，存在返回True
        os.makedirs(img_path)           #os.makedirs（）用递归创建文件目录，文件夹需要包含子目录
    try:
        resp = requests.get(item.get('image'))  #访问图片
        if resp.status_code == 200:
            file_path = img_path + os.path.sep + '{file_name}.{file_suffix}'.format(
                file_name=md5(resp.content).hexdigest(),    #表示文件名字，根据文件内容以其md5值作为文件名
                file_suffix='jpg')
            if not os.path.exists(file_path):   #同一份内容的md5值相同，避免重复下载
                with open(file_path, 'wb') as f:    #打开文件，wb形式，二进制数据
                    f.write(resp.content)
                    f.close()
                print('Downloaded image path is %s' % file_path)
            else:
                print('Already image, %s', file_path)
    except Exception as e:
        print(e)


def main(offset):
    json = get_page(offset)
    for item in get_images(json):
        save_image(item)

GROUP_START = 0
GROUP_END = 9

if __name__ == '__main__':
    pool = Pool()
    groups = ([x * 20 for x in range(GROUP_START, GROUP_END + 1)])
    pool.map(main, groups)  #mao函数会根据提供的main函数对指定的groups序列做映射
    pool.close()
    pool.join()     #对pool对象调用join()会等待所有子进程执行完毕，调用join()之前需要调用close()
