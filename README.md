# ca3
CA3 Smart Alarm.

CA3 Smart Alarm is a smart alarm that allows the user to schedule events to
notify them of the weather, top news headlines, and current COVID-19 deaths
and cases in their region. There are 2 types of events:

- Alarms: these are scheduled by the user to go off at specific times. The
user can choose whether they would like a weather or news briefing (or both).
When the alarm reaches its time, a TTS announcement will occur which will
contain the alarm name, the current COVID-19 deaths/rates, and also the news
or weather depending on what the user selected. The user can also view
scheduled alarms in the side bar on the left and can cancel an alarm if they
don't need it any more.

- Notifications: these occur every 15 minutes. The program will get the
latest COVID-19, weather and news data and will display them in the side bar
on the right. The user can also remove notifications they no longer need to
view.

## Installation

To get the CA3 Smart Alarm, download and install Python 3. You will also need
the following modules/libraries:

- `pyttsx3`
- `uk-covid19`
- `flask`

These can be installed by running `pip install [name]`. You can then either
download the CA3 Smart Alarm directly from this page or run `git clone
https://github.com/ah970/ca3`.

## Usage

To use the CA3 Smart Alarm, run: `python main.py`.

Then, open a browser and navigate to: `localhost:5000`, or alternatively,
`127.0.0.1:5000`. You should then see the user interface for the CA3 Smart
Alarm.

## Configuration

To (re)configure the CA3 Smart Alarm to your needs, you can edit the 
`config.json` file. This file contains a variety of different options that
the user can change:

- Title: name of the CA3 Smart Alarm.
- APIs:
	- News:
		- URL: the URL to pull data from.
		- Key: the key to use.

	- Weather:
		- URL: the URL to pull data from.	
        	- Key: the key to use.

- Country code: the 2 letter ISO-3166-1 code of your country.
- Country: the name of your country.
- City: the name of your city.
- Units:
	- Standard: the standard of units to use (metric or imperial).
	- String: temperature string to use.

- Notification update: how of the notifications list should be updated (in
minutes)
- Number of articles: the number of articles that the news API should get.
- Cases threshold: the threshold over which daily and total cases should be
reported.
- Deaths threshold: the threshold over which daily and total deaths should be
reported.
- Log file: the log file to use.

## Log file
The log file (by default a file called `ca3.log` in the same directory as
`main.py` contains a list of events that have happened. This log is relatively
detailed and is intended as a diagnostic tool in the event of a crash.

## Miscellaneous
The license and author for this project can be found in the `LICENSE` file.

This project is hosted on GitHub [here](https://github.com/ah970/ca3).
