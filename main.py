# -*- coding:utf-8 -*-
__author__ = 'bobby'

from scrapy.cmdline import execute

import sys
import os
from urllib import parse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# execute(["scrapy","crawl","jobbole"])
execute(["scrapy","crawl","zhihu"])


# a = parse.urljoin('http://blog.jobbole.com/all-posts/','./112589/')
# print(a)