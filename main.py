import time
import sched
import pyttsx3
from flask import Flask, redirect, request, render_template


alarms = []
notifications = []

s = sched.scheduler(time.time, time.sleep)

app = Flask(__name__)


def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(test)
    engine.runAndWait()
    engine.stop()


def announcement(date_time):
    alarm = get_alarm(date_time)

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


@app.route("/")
@app.route("/index")
def index():
    s.run(blocking=False)

    date_time = request.args.get("alarm")
    label = request.args.get("two")
    news = request.args.get("news")
    weather = request.args.get("weather")
    date_time_to_remove = request.args.get("alarm_item")

    if date_time and label:
        date_time = fix_date_time(date_time)
        add_alarm(date_time, label, news, weather)

        return redirect("/index")

    if date_time_to_remove:
        date_time_to_remove = fix_date_time(date_time_to_remove)
        remove_alarm(date_time_to_remove)

        return redirect("/index")

    return render_template("index.html", alarms=alarms, favicon=False)


if __name__ == "__main__":
    app.run()
