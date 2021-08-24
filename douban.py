# 爬取网页
import requests
# 解析网页
from bs4 import BeautifulSoup
# 正则匹配
import re
# 操作excel
import xlwt
# 操作sqlite
import sqlite3

# 正则表达式匹配规则
# 电影链接
find_link = re.compile(r'<a href="(.*?)">')
# 图片链接
find_img_src = re.compile(r'<img.*src="(.*?)"',re.S)
# 中文名和外文名
find_title = re.compile(r'<span class="title">(.*)</span>')
# 简介
find_bd = re.compile(r'<p class="">(.*?)</p>',re.S)
# 评分
find_rating = re.compile(r'<span class="rating_num" property="v:average">(.*)</span>')
# 评价人数
find_judge = re.compile(r'<span>(\d*)人评价</span>')
# 短评
find_inq = re.compile(r'<span class="inq">(.*)</span>')

# 爬取特定URL的网页内容
def ask_url(url):
    """爬取特定URL的网页内容"""
    head = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36"}
    response = requests.get(url,headers=head)
    response.encoding = "utf-8"
    html = response.text
    return html

# 根据网址返回数据
def get_data(base_rul):
    """根据网址返回数据"""
    data_list = []
    # 每页25个电影，一共10页，循环10次
    for i in range(0,10):
        # 拼接每次查询的url
        url = base_rul + str(i*25)
        html = ask_url(url)
        # 通过BeautifulSoup进行网页解析
        soup = BeautifulSoup(html,"html.parser")
        # 每个电影对应一个div，先把每个电影的div获取出来再进一步解析
        for item in soup.find_all('div',class_ = "item"):
            data = []
            item = str(item)
            # 电影详情链接
            # 可能匹配到多个数据，只获取第一个
            link = re.findall(find_link,item)[0]
            data.append(link)
            # 图片地址
            img_src = re.findall(find_img_src,item)[0]
            data.append(img_src)
            # 电影名称，中文和外文
            titles = re.findall(find_title,item)
            # 如果外文名不存在，赋值为空格
            if(len(titles) == 2):
                c_title = titles[0]
                data.append(c_title )
                o_title = titles[1].replace('/','').strip()
                data.append(o_title)
            else:
                data.append(titles[0])
                data.append(' ')
            # 评分
            rating = re.findall(find_rating,item)[0]
            data.append(rating)
            # 评论人数
            judge_num = re.findall(find_judge,item)[0]
            data.append(judge_num)
            # 短评
            inq = re.findall(find_inq,item)
            if len(inq) != 0:
                inq = inq[0].replace("。","")
                data.append(inq)
            else:
                data.append(" ") #防止为空
            # 简介
            bd = re.findall(find_bd,item)[0]
            bd = re.sub('<br(\s+)?/>(\s+)?',"",bd) # 去掉<br/>
            bd = re.sub("/"," ",bd)# 斜杠替换
            bd = bd.replace('\xa0','') # \xa0替换
            data.append(bd.strip()) # 去掉前后空格

            data_list.append(data)
    return data_list

# 保存数据到excel文件
def save_data(data_list,save_path):
    """保存数据到excel文件"""
    work_book = xlwt.Workbook(encoding="utf-8",style_compression=0)
    # 创建sheet页
    work_sheet = work_book.add_sheet("豆瓣电影Top250",cell_overwrite_ok=True)
    # 标题行
    col = ('电影详情链接','图片链接','中文名','外国名','评分','评分人数','概况','相关信息')
    # 写入数据
    for i in range(0,8):
        work_sheet.write(0,i,col[i])
    for i in range(0,250):
        data = data_list[i]
        for j in range(0,8):
            work_sheet.write(i+1,j,data[j])
    # 保存
    work_book.save(save_path)

# 创建数据库
def init_db(db_path):
    """创建数据库，如果存在则跳过"""
    sql = """
    create table if not exists movie_250(
        id integer primary key autoincrement,
        info_link text,
        pic_link text,
        c_name text,
        e_name text,
        score numeric,
        rating numeric,
        instruction text,
        info text
    )
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    conn.close()

# 保存数据到数据库中，如果数据库和表不存在则新创建
def save_data_to_db(data_list,db_path):
    """保存数据到数据库中，如果数据库和表不存在则新创建"""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for data in data_list:
        # sql语句拼接是需要带双引号，先进行拼接处理
        for index in range(len(data)):
            data[index] = '"' + data[index] + '"'
        # 将数据拼接到sql语句中
        sql = """
        insert into movie_250(info_link, pic_link, c_name, e_name, score, rating, instruction, info) 
        values(%s)
        """%",".join(data)
        # 将数据写入数据库
        cursor.execute(sql)
        conn.commit()
    cursor.close()
    conn.close()

def main():
    """主函数"""
    base_url = "https://movie.douban.com/top250?start="
    db_path = "movie.db"
    save_path = "豆瓣电影Top250.xls"
    data_list = get_data(base_url)
    save_data(data_list,save_path)
    save_data_to_db(data_list,db_path)

if __name__ == '__main__':
    main()