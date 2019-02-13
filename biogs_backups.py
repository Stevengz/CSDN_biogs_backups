# coding: utf-8

import re
import os
import sys
import chilkat

head_string = """
<html>
<head>
  <title>索引</title>
  <basefont face="微软雅黑" size="2" />
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
  <meta name="exporter-version" content="Evernote Windows/276127; Windows/6.3.9600;"/>
  <style>
    body, td {
      font-family: 微软雅黑;
      font-size: 10pt;
    }
  </style>
</head>
<body>
"""
tail_string = """
</body>
</html>
"""

iter_count = 0


# 提取博客列表
def extract(account_id):
    url = "https://me.csdn.net/" + account_id + '/'
    spider = chilkat.CkSpider()
    # 初始化组件
    spider.Initialize(url)
    spider.AddUnspidered(url)
    pattern = account_id + '/article/details'
    file_path = 'URList-' + account_id + '.txt'
    f = open(file_path, 'w')
    # 是否加载完成
    success = spider.CrawlNext()
    if (success == True):
        url_list = []

        # 提取所有博客链接
        for i in range(0, spider.get_NumOutboundLinks()):
            article_url = spider.getOutboundLink(i)
            # 把链接都存放在列表里面
            url_list.append(article_url)

        # 把每个链接的标题提取出来并和链接一起保存
        article_spider = chilkat.CkSpider()
        print("正在保存...")
        for one_url in url_list:
            # 判断是否为所需链接
            judge = re.search(pattern, one_url)
            if not judge:
                continue
            print(one_url)
            article_spider.Initialize(one_url)
            article_success = article_spider.CrawlNext()
            # 提取标题
            title = article_spider.lastHtmlTitle().split(' -')[0]
            # 对标题中特殊符号进行处理
            title = title.replace('/', ' ')
            title = title.replace('_', ' ')
            title = title.replace(':', ' ')
            title = title.replace('*', ' ')
            title = title.replace('?', ' ')
            title = title.replace('|', ' ')
            title = title.replace('#', 'sharp')
            f.write(one_url + "," + title + '\n')

    else:
        # 当出现错误或者没有需要抓取的网址
        if (spider.get_NumUnspidered() == 0):
            print("No more URLs to spider")
        else:
            print(spider.lastErrorText())
    f.close()
    # 对生产的文件进行备份
    open('URList-' + account_id + '-backup.txt', "w").write(
        open(file_path, "r").read())
    print("提取完成")


# 下载博客
def download(account_id):
    global iter_count
    mht = chilkat.CkMht()
    # 解锁组件，使用完整功能
    success = mht.UnlockComponent("Anything for 30-day trial")
    if (success != True):
        print(mht.lastErrorText())
        sys.exit()

    # 拿出链接
    file_path = 'URList-' + account_id + '.txt'
    f = open(file_path, 'r')
    fout = open('Error.txt', 'w')
    for line in f.readlines():
        m = re.search('(http.+[0-9]{7,}),(.+)', line)
        url = m.group(1)
        print(url)
        title = m.group(2)
        # 确认MHT信息
        mht_doc = mht.getMHT(url)
        if (mht_doc == None):
            print(mht.lastErrorText())
            sys.exit()
        if not os.path.exists('CSDN-' + account_id):
            os.mkdir('CSDN-' + account_id)
        # 提取HTML并嵌入对象
        unpack_dir = "./CSDN-" + account_id + '/'
        html_filename = title + ".html"
        parts_subdir = title
        # 解压缩MHT文件的内容，把需要的css、js等资源都进行下载
        success = mht.UnpackMHTString(mht_doc, unpack_dir, html_filename,
                                      parts_subdir)
        if (success != True):
            fout.write(line)
        else:
            print("成功下载：" + title)
    f.close()
    fout.close()
    # 出现错误就尝试迭代
    if iter_count >= 5:
        print("一些博客没有下载成功, 请确认错误信息")
        os.remove(file_path)
        os.rename('URList-' + account_id + '-backup.txt', file_path)
    if iter_count < 10 and os.path.getsize('Error.txt') > 0:
        iter_count += 1
        print("进行第 " + str(iter_count) + " 次迭代下载")
        os.remove(file_path)
        os.rename('Error.txt', file_path)
        download(account_id)


# 建立索引
def generate_index(account_id):
    file_path = 'URList-' + account_id + '.txt'
    f = open(file_path, 'r')
    fout = open('./CSDN-' + account_id + '/Index.html', 'w', encoding='utf-8')
    fout.write(head_string)
    fout.write("""<h2>""" + account_id + "的博客" + """</h2>\n""")
    fout.write("""<ol>\n""")
    for line in f.readlines():
        m = re.search('(http.+[0-9]{7,}),(.+)', line)
        title = m.group(2)
        print(title)
        fout.write("""<li><a href=\"""" + title + ".html" + """\">""" + title +
                   """</a></li>\n""")
    fout.write("""</ol>""")
    fout.write(tail_string)
    f.close()
    fout.close()


if __name__ == '__main__':
    print("请输入被提取CSDN博客的账号ID")
    account_id = input("ID：")
    if not account_id:
        print("ID为空，无法提取")
    else:
        print("开始提取博客列表...")
        extract(account_id)
        print("开始下载博客...")
        download(account_id)
        print("开始生成索引...")
        generate_index(account_id)
        print("备份完成")