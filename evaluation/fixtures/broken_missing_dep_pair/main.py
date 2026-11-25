import requests
from bs4 import BeautifulSoup
from dateutil import parser

print(parser.parse("2024-01-02").year, BeautifulSoup("<p>x</p>", "html.parser").p.text)
