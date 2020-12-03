import time
import sched
import pyttsx3
import json
import requests
from flask import Flask, Markup, redirect, request, render_template


alarms = []
notifications = []

s = sched.scheduler(time.time, time.sleep)

app = Flask(__name__)

with open("config.json", "r") as file:
    settings = json.loads(file.read())


def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def announcement(date_time):
    alarm = get_alarm(date_time)

    if alarm["news"]:
        news = get_news()
        articles = news["raw_articles"]
        text_to_speech("Top headlines")
        text_to_speech(articles)
    if alarm["weather"]:
        weather = get_weather()
        description = weather["content"]
        text_to_speech("Current weather")
        text_to_speech(description)

    remove_alarm(date_time)


def fix_date_time(date_time):
    date_time = date_time.replace("T", " ")
    date_time = date_time.replace("+", " ")
    return date_time


def add_alarm(date_time, label, news, weather):
    pattern = "%Y-%m-%d %H:%M"
    epoch = time.mktime(time.strptime(date_time, pattern))
    event = s.enterabs(epoch, 1, announcement, argument=(date_time,))

    print("Adding alarm", label, "set to go off at", date_time)

    alarm_dict = {
            "title": date_time,
            "content": label,
            "event": event,
            "news": news,
            "weather": weather
            }

    alarms.append(alarm_dict)


def get_item_from_list(title, list_name):
    for item in list_name:
        if item["title"] == title:
            return item

def remove_item_from_list(title, list_name):
    item = get_item_from_list(title, list_name)
    list_name.remove(item)

    try:
        s.cancel(item["alarm"])
    except ValueError:
        pass

def get_alarm(date_time):
    for alarm in alarms:
        if alarm["title"] == date_time:
            return alarm


def remove_alarm(date_time):
    alarm = get_alarm(date_time)

    print("Removed alarm", alarm["content"], "set to go off at", alarm["title"])

    alarms.remove(alarm)
    try:
        s.cancel(alarm["event"])
    except ValueError:
        pass


def get_weather():
    print("Getting weather data")
    url = settings["apis"]["weather"]["url"]
    key = settings["apis"]["weather"]["key"]

    city = settings["city"]
    units = settings["units"]["standard"]

    url = url.format(key=key, city=city, units=units)

    r = requests.get(url)
    
    data = r.json()
    weather_data = data["weather"].pop()
    weather_description = weather_data["description"].title()
    temperature = round(data["main"]["temp"])

    weather_dict = {
            "title": "Weather",
            "content": weather_description + ", Temperature: " +
            str(temperature) + settings["units"]["string"],
            "description": weather_description,
            "temperature": temperature
            }
    return weather_dict


def get_news():
    print("Getting news data")
    url = settings["apis"]["news"]["url"]
    key = settings["apis"]["news"]["key"]

    country_code = settings["country_code"]
    number_of_articles = settings["number_of_articles"]

    url = url.format(key=key, country_code=country_code, number_of_articles=number_of_articles)

    r = requests.get(url)

    data = r.json()
    html_link_structure = "<a href=\"{url}\">{text}</a><br><br>"
    content = ""
    raw_articles = ""
    articles = data["articles"]
    for article in articles:
        title = article["title"]
        url = article["url"]
        content += html_link_structure.format(text=title, url=url)
        raw_articles += title
    content = Markup(content)

    news_dict = {
            "title": "News",
            "content": content,
            "raw_articles": raw_articles
            }
    
    return news_dict


def get_notification(title):
    for notification in notifications:
        if notification["title"] == title:
            return notification


def remove_notification(title):
    notification = get_notification(title)

    notifications.remove(notification)


def update_notifications():
    print("Updating notificaitons")
    old_weather = get_notification("Weather")

    if old_weather:
        current_weather = get_weather()
        print("Comparing old and new weather data")
        if old_weather["description"] != current_weather["description"] \
        or old_weather["temperature"] != current_weather["description"]:
            print("Old weather outdated, removing/replacing")
            remove_notification("Weather")
            notifications.append(current_weather)
    else:
        weather = get_weather()
        notifications.append(weather)

    old_news = get_notification("News")

    if old_news:
        current_news = get_news()
        print("Comparing old and new news data")
        if old_news["content"] == current_news["content"]:
            print("old news outdatted, remoin repla")
            remove_notification("News")
            notifications.append(current_news)
    else:
        news = get_news()
        notifications.append(news)

    s.enter(settings["notification_update"] * 60, 2, update_notifications)


update_notifications()

@app.route("/")
@app.route("/index")
def index():
    s.run(blocking=False)

    date_time = request.args.get("alarm")
    label = request.args.get("two")
    news = request.args.get("news")
    weather = request.args.get("weather")
    date_time_to_remove = request.args.get("alarm_item")
    notification_to_remove = request.args.get("notif")

    if date_time and label:
        date_time = fix_date_time(date_time)
        add_alarm(date_time, label, news, weather)

        return redirect("/index")

    if date_time_to_remove:
        date_time_to_remove = fix_date_time(date_time_to_remove)
        remove_alarm(date_time_to_remove)

        return redirect("/index")

    if notification_to_remove:
        remove_notification(notification_to_remove)

        return redirect("/index")

    return render_template("index.html", alarms=alarms, notifications=notifications)


if __name__ == "__main__":
    app.run()
