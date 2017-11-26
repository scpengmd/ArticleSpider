# -*- coding: utf-8 -*-
import scrapy
import re
import json
import datetime

try:
    from urlparse import parse
except:
    from urllib import parse

from scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    #question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset={1}&limit={2}&sort_by=default"

    header = {
        "Host": "www.zhihu.com",
        "Referer": "https://www.zhihu.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"
    }

    def parse(self, response):
        """
        提取出html页面中的所有url，并跟踪这些url进一步爬取
        如果提取的url中格式为/question/xxx，就下载之后直接进入解析函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            print(url)
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                #如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=self.header, callback=self.parse_question)
                break
            else:
                #如果不是qustion页面则直接进一步跟踪
                # yield scrapy.Request(url, headers=self.header, callback=self.parse)
                pass


    def parse_question(self, response):
        #处理quetion页面，从页面中提取出具体的question item

        if "QuestionHeader-title" in response.text:
            #处理新版本(这里跟视频不一样了，没有QuestionHeader-title)
            #新版本样式：https://www.zhihu.com/question/55939030
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = match_obj.group(2)

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css("title", "h1.QuestionHeader-title::text") #['你见过最上进的人是怎样的？']
            item_loader.add_css("content", ".QuestionHeader-detail span::text") #['镜像问题:', '看别人的短处固然能...']
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".List-headerText span::text") #['713', ' 个回答']
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text") #['13 条评论']
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text") #['36820', '9094813']
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text") #['职业发展', '生活经历', '职业规划', '社会', '个人成长']
            question_item = item_loader.load_item()
            pass# 2017/11/25 15.:06

        else:
            #处理旧版本
            #旧版本样式：https://www.zhihu.com/question/55939030/answer/147357004
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css("title", "h1.QuetionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".QuestionMainAction::text") #['查看全部 719 个回答', '查看全部 719 个回答']其它跟新版一样
            item_loader.add_css("comments_num", ".QuestionHeader-actions button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover::text")

            question_item = item_loader.load_item()
            pass

        yield scrapy.Request(self.start_answer_url.format(question_id, 3, 20), headers=self.header, callback=self.parse_answer)
        yield question_item


    def parse_answer(self, response):
        #处理question的answerself
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        #提取answer的具体字段
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id " in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else  None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["crawl_time"] = datetime.datetime.now()
            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.header, callback=self.parse_answer)


    #scrapy的入口是这个函数，想要做模拟登陆就要重写这个函数,意思是请求前，先去登陆页面解决登陆问题
    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.header, callback=self.login)]  #这是scrapy自带的异步调用请求，记得定义callback，不然默认是callback=self.parse()

    def login(self, response):
        response_text = response.text
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response_text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = (match_obj.group(1))

        if xsrf:
            post_url = "https://www.zhihu.com/login/phone_num"
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "18064630503",
                "password": "missmiss",
                "captcha":""
            }
            import time
            t = str(int(time.time() * 1000))
            # captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login&lang=en".format(t)

            yield scrapy.Request(captcha_url, headers=self.header, meta={"post_data": post_data}, callback=self.login_after_capthcha)



    def login_after_capthcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()

        from PIL import Image
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            pass

        captcha = input("输入验证码\n>")

        post_data = response.meta.get("post_data", {})
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data["captcha"] = captcha
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.header,
            callback=self.check_login
        )]


    def check_login(self, response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)  #这里没有指定callback,回到最上面的self.parse
        else:
            print("error")
            pass
