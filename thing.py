import json
import requests

notifications = []

with open("config.json", "r") as file:
    settings = json.loads(file.read())

def get_news():
    url = settings["apis"]["news"]["url"]
    key = settings["apis"]["news"]["key"]

    country_code = settings["country_code"]
    number_of_articles = settings["number_of_articles"]

    url = url.format(key=key, country_code=country_code, number_of_articles=number_of_articles)

    r = requests.get(url)

    data = r.json()
    html_link_structure = "<a href={url}>{text}</a><br>\n"
    content = ""
    articles = data["articles"]
    for article in articles:
        title = article["title"]
        url = article["url"]
        content += html_link_structure.format(text=title, url=url)

    news_dict = {
            "title": "News",
            "content": content
            }
    
    return news_dict

print(get_news())
