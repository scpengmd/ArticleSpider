# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
#eeee
import datetime
import re
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

from .utils.common import extract_num
from .settings import SQL_DATE_FORMAT,SQL_DATETIME_FORMAT

class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

def add_jobbole(value):
    return value+"-bobby"


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()
    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d+).*?", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0
    return nums

def remove_commetn_tags(value):
    #去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value

class ArticleItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()


def return_value(value):
    return value


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_commetn_tags),
        output_processor=Join(",")
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    INSERT INTO jobbole_article(title, url, create_date, fav_nums)
                    VALUES(%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums)
                """

        params = (self["title"], self["url"], self["create_date"], self["fav_nums"])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    #知乎的问题item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    INSERT INTO zhihu_question(zhihu_id,topics,url,title,content,answer_num,comments_num,watch_user_num,
                    click_num,crawl_time)
                    VALUES(%s,%s,%s,%s,(%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE fav_nums=VALUES(fav_nums), answer_num=VALUES(answer_num), 
                        comments_num=VALUES(comments_num), watch_user_num=VALUES(watch_user_num),
                        click_num=VALUES(click_num)                
                """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = extract_num("".join(self["answer_num"]))
        comments_num = extract_num("".join(self["comments_num"]))
        watch_user_num = extract_num("".join(self["watch_user_num"]))
        click_num = extract_num("".join(self["click_num"]))
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id,topics,url,title,content,answer_num,comments_num,watch_user_num,click_num,crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    #知科的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    INSERT INTO zhihu_answer(zhihu_id,url,question_id,author_id,content,praise_num,comments_num,
                        create_time,update_time,crawl_time,crawl_update_time)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),
                        praise_num=VALUES(praise_num), update_time=VALUES(update_time)
                """

        create_time =  datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time =  datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["praise_num"],
            self["comments_num"],create_time,update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql,params