"""main - This module provides the main app."""


import time
import sched
import pyttsx3
import json
import requests
import logging
from uk_covid19 import Cov19API
from flask import Flask, Markup, redirect, request, render_template


with open("config.json", "r") as file:
    settings = json.loads(file.read())

alarms = []
notifications = []

logging.basicConfig(filename=settings["log_file"], level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")

logging.info("Setting up scheduler")
s = sched.scheduler(time.time, time.sleep)

logging.info("Setting up Flask app")
app = Flask(__name__)


def text_to_speech(text: str):
    """Run a TTS with the given text.

    Arguments:
    text (str): text to TTS.

    Returns:
    None
    """
    logging.info("Running text-to-speech function with text: {}".format(text))
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def announcement(date_time: str):
    """Perform an announcement for an alarm.

    Arguments:
    date_time (str): datetime of the alarm to perform announcement for.

    Returns:
    None
    """
    logging.info("Performing announcement for alarm with datetime: {}".format(date_time))
    alarm = get_alarm(date_time)

    label = alarm["content"]
    text_to_speech("Alarm " + label + " has gone off")

    logging.info("Performing announcement for COVID data")
    covid_data = get_covid_data()
    text = covid_data["raw_content"]
    text_to_speech(text)

    if alarm["news"]:
        logging.info("Performing announcement for news")
        news = get_news()
        text = news["raw_content"]
        text_to_speech("Top headlines")
        text_to_speech(text)

    if alarm["weather"]:
        logging.info("Performing announcement for weather")
        weather = get_weather()
        text = weather["content"]
        text_to_speech("Current weather")
        text_to_speech(text)

    remove_alarm(date_time)


def fix_date_time(date_time: str) -> str:
    """Fix a datetime string for consistency.

    Arguments:
    date_time (str): datetime string to fix.

    Returns:
    date_time (str): fixed datetime string.
    """
    logging.info("Fixing datetime string: {}".format(date_time))
    date_time = date_time.replace("T", " ")
    date_time = date_time.replace("+", " ")

    return date_time


def add_alarm(date_time: str, label: str, news: str, weather: str):
    """Add an alarm to the list of alarms.

    Arguments:
    date_time (str): datetime when alarm is supposed to go off.
    label (str): label of alarm.
    news (str): should the alarm say news?
    weather (str): should the alarm say weather?

    Returns:
    None
    """
    pattern = "%Y-%m-%d %H:%M"
    epoch = time.mktime(time.strptime(date_time, pattern))

    if time.time() > epoch:
        logging.error("Alarm is set in the past, not adding alarm.")
        return

    logging.info("Adding alarm to scheduler with datetime: {}".format(date_time))
    event = s.enterabs(epoch, 1, announcement, argument=(date_time,))

    alarm_dict = {
            "title": date_time,
            "content": label,
            "event": event,
            "news": news,
            "weather": weather
            }

    logging.info("Adding alarm with datetime {}, label {}, news {}, weather {} to list of alarms".format(date_time, label, weather, news))

    alarms.append(alarm_dict)


def get_alarm(date_time: str) -> dict:
    """Get an alarm by it's datetime from the list of alarms.

    Arguments:
    date_time (str): datetime of alarm to get.

    Returns:
    alarm (dict): the relevant alarm dictionary.
    """
    logging.info("Getting alarm with datetime: {}".format(date_time))
    for alarm in alarms:
        if alarm["title"] == date_time:
            return alarm
    logging.error("Alarm with datetime {} could not be found".format(date_time))
    return None


def remove_alarm(date_time: str):
    """Remove an alarm from the list of alarms.

    Arguments:
    date_time (str): datetime of alarm to remove.

    Returns:
    None
    """
    alarm = get_alarm(date_time)

    logging.info("Removing alarm wtih datetime {} from list of alarms".format(date_time))
    alarms.remove(alarm)
    try:
        logging.info("Cancelling alarm in scheduler")
        s.cancel(alarm["event"])
    except ValueError:
        logging.warning("Alarm could not be cancelled, perhaps it already went off?")
        pass


def get_weather() -> dict:
    """Gets the current weather.

    Arguments:
    None

    Returns:
    weather_dict (dict): a dictionary containing current weather data.
    """
    logging.info("Getting latest weather data")
    url = settings["apis"]["weather"]["url"]
    key = settings["apis"]["weather"]["key"]

    city = settings["city"]
    units = settings["units"]["standard"]

    url = url.format(key=key, city=city, units=units)

    logging.info("Attempting a GET request with URL: {}".format(url))
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

    logging.info("Returning latest weather data")

    return weather_dict


def get_news() -> dict:
    """Gets the current news.

    Arguments:
    None

    Returns:
    news_dict (dict): a dictionary with the current news data.
    """
    logging.info("Getting latest news data")
    url = settings["apis"]["news"]["url"]
    key = settings["apis"]["news"]["key"]

    country_code = settings["country_code"]
    number_of_articles = settings["number_of_articles"]

    url = url.format(key=key, country_code=country_code,
            number_of_articles=number_of_articles)

    logging.info("Attempting a GET request with URL: {}".format(url))
    r = requests.get(url)

    data = r.json()
    html_link_structure = "<a href=\"{url}\">{text}</a><br><br>"
    content = ""
    raw_content = ""
    articles = data["articles"]
    for article in articles:
        title = article["title"]
        url = article["url"]
        content += html_link_structure.format(text=title, url=url)
        raw_content += title + "\n"
    content = Markup(content)

    news_dict = {
            "title": "News",
            "content": content,
            "raw_content": raw_content
            }
    
    logging.info("Returning latest news data")

    return news_dict


def get_covid_data() -> dict:
    """Gets the current COVID data.

    Arguments:
    None

    Returns:
    covid_data_dict (dict): a dictionary containing current COVID data.
    """
    yesterdays_date = time.strftime("%Y-%m-%d",
            time.gmtime(time.time() - (60 * 60 * 24)))
    country = settings["country"]

    logging.info("Getting COVID data for date: {}".format(yesterdays_date))

    filters = [
            "areaType=nation",
            "areaName={}".format(country),
            "date={}".format(yesterdays_date)
            ]

    structure = {
            "newCasesByPublishDate": "newCasesByPublishDate",
            "cumCasesByPublishDate": "cumCasesByPublishDate",
            "newDeathsByDeathDate": "newDeathsByDeathDate",
            "cumDeathsByDeathDate": "cumDeathsByDeathDate"
            }
    
    logging.info("Attempting to get data from COVID API")
    api = Cov19API(filters=filters, structure=structure)
    data = api.get_json()["data"].pop()

    new_cases = data["newCasesByPublishDate"] or 0
    total_cases = data["cumCasesByPublishDate"]
    new_deaths = data["newDeathsByDeathDate"] or 0
    total_deaths = data["cumDeathsByDeathDate"]

    content = "COVID data as of {}:<br><br>".format(yesterdays_date)
    if new_cases >= settings["cases_threshold"]:
        logging.info("New cases have broken threshold")
        content += "New cases: {}<br>".format(new_cases)
        content += "Total cases: {}<br>".format(total_cases)
    else:
        logging.info("New cases have not broken threshold")
        content += "New cases have not broken thresholds<br>"

    if new_deaths >= settings["deaths_threshold"]:
        logging.info("New deaths have broken threshold")
        content += "New deaths: {}<br>".format(new_deaths)
        content += "Total deaths: {}<br>".format(total_deaths)
    else:
        logging.info("New deaths have not broken threshold")
        content += "New deaths have not broken thresholds<br>"
    
    raw_content = content.replace("<br>", "")
    content = Markup(content)

    covid_data_dict = {
            "title": "COVID",
            "content": content,
            "raw_content": raw_content,
            "data": data
            }

    logging.info("Returning latest COVID data")
    
    return covid_data_dict


def get_notification(title: str) -> dict:
    """Get a notification by it's title.

    Arguments:
    title (str): title of notification to get.

    Returns:
    notification (dict): relevant notification dictionary.
    """
    logging.info("Getting notification with title: {}".format(title))
    for notification in notifications:
        if notification["title"] == title:
            return notification
    logging.error("Notification with title {} could not be found".format(title))
    return None


def remove_notification(title: str):
    """Remove a notification from the list of notifications.

    Arguments:
    title (str): title of notification to remove.

    Returns:
    None
    """
    notification = get_notification(title)

    logging.info("Removing notification with title {} from list of notifications".format(title))
    notifications.remove(notification)


def update_notifications():
    """Update all notifications.

    Arguments:
    None

    Returns:
    None
    """
    logging.info("Updating notifications")

    old_covid_data = get_notification("COVID")

    logging.info("Checking COVID data")
    if old_covid_data:
        current_covid_data = get_covid_data()
        if old_covid_data["data"] != current_covid_data["data"]:
            logging.info("COVID data is outdated, updating with new data")
            remove_notification("COVID")
            notifications.append(current_covid_data)
    else:
        logging.warning("COVID data nonexistent, getting new COVID data (first time run?)")
        covid_data = get_covid_data()
        notifications.append(covid_data)

    old_weather = get_notification("Weather")

    logging.info("Checking weather data")
    if old_weather:
        current_weather = get_weather()
        if old_weather["description"] != current_weather["description"] \
        or old_weather["temperature"] != current_weather["description"]:
            logging.info("Weather data is outdated, updating with new data")
            remove_notification("Weather")
            notifications.append(current_weather)
    else:
        logging.warning("Weather data nonexistent, getting new weather data (first time run?)")
        weather = get_weather()
        notifications.append(weather)

    old_news = get_notification("News")

    logging.info("Checking news data")
    if old_news:
        current_news = get_news()
        if old_news["content"] != current_news["content"]:
            logging.info("News data is outdated, updating with new data")
            remove_notification("News")
            notifications.append(current_news)
    else:
        logging.warning("News data nonexistent, getting new news data (first time run?)")
        news = get_news()
        notifications.append(news)

    logging.info("Adding event to scheduler to update notifications in {} minutes".format(settings["notification_update"]))
    s.enter(settings["notification_update"] * 60, 2, update_notifications)


@app.route("/")
@app.route("/index")
def index():
    """Serve the user the index page of the site.

    Arguments:
    None

    Returns:
    redirect("/index) (redirect): redirect the user back to this page.
    OR
    render_template("index.html, alarms=alarms, notifications=notifications)
    (render_template): render the page with the alarms and notifications.
    """
    logging.info("User has navigated to / or /index")

    logging.info("Running any scheduled events")
    s.run(blocking=False)


    logging.info("Getting any arguments")
    date_time = request.args.get("alarm")
    label = request.args.get("two")
    news = request.args.get("news")
    weather = request.args.get("weather")
    date_time_to_remove = request.args.get("alarm_item")
    notification_to_remove = request.args.get("notif")

    if date_time and label:
        logging.info("User supplied datetime {} and label {}, going to make alarm".format(date_time, label))
        date_time = fix_date_time(date_time)
        add_alarm(date_time, label, news, weather)

        logging.info("Redirecting user back to /index")
        return redirect("/index")

    if date_time_to_remove:
        logging.info("User wants to remove alarm with datetime {}".format(date_time_to_remove))
        date_time_to_remove = fix_date_time(date_time_to_remove)
        remove_alarm(date_time_to_remove)

        logging.info("Redirecting user back to /index")
        return redirect("/index")

    if notification_to_remove:
        logging.info("User wants to remove notification with title {}".format(notification_to_remove))
        remove_notification(notification_to_remove)

        logging.info("Redirecting user back to /index")
        return redirect("/index")

    logging.info("Rendering template with alarms and notifications")
    return render_template("index.html", alarms=alarms,
            notifications=notifications)


if __name__ == "__main__":
    logging.info("Starting main app")
    update_notifications()
    app.run()
