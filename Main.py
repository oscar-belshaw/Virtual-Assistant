from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import speech_recognition as sr
import pyttsx3 as ps
import pytz
import subprocess

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAY_EXTENSIONS = ['rd', 'th', 'st', 'nd']

#This allows the computer to reply audibly rather than just on the command line
def speak(text):
	engine = ps.init()
	engine.say(text)
	engine.runAndWait()

#This function uses the microphone to monitor for audio
#and convert the speech in to text	
def get_audio():
	r =sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""
		
		try:
			said = r.recognize_google(audio)
			print(said)
		except Exception as e:
			print("Exception: " + str(e))
	return said.lower()

#Boring API stuff
def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    
    return service

#This parses through google calendar to reply with events for a given date  
def get_events(day, service):
	
	date = datetime.datetime.combine(day, datetime.datetime.min.time())
	end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
	utc = pytz.UTC
	date = date.astimezone(utc)
	end_date = end_date.astimezone(utc)
	events_result = service.events().list(calendarId='primary', timeMin=date.isoformat() , timeMax=end_date.isoformat(), singleEvents=True, orderBy='startTime').execute()
	events = events_result.get('items', [])
	
	if not events:
		speak('No upcoming events found.')
	else:
		for event in events:
			speak(f"You have {len(events)} events on this day")
			start = event['start'].get('dateTime', event['start'].get('date'))
			print(start, event['summary'])
			start_time = str(start.split("T")[1].split("-")[0]) 
			if int(start_time.split(":")[0]) < 12:
				start_time = start_time + "am"
			else:
				start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
				start_time = start_time + "pm"
			speak(event["summary"] + "at" + start_time) 

#This replies with the current date
def get_date(text):
	text = text.lower()
	today = datetime.date.today()
	
	if text.count("today") > 0:
		return today 
	
	day = -1
	day_of_week = -1
	month = -1
	year = today.year
	
	for word in text.split():
		if word in MONTHS:
			month = MONTHS.index(word) +1
		elif word in DAYS:
			day_of_week = DAYS.index(word)
		elif word.isdigit():
			day = int(word)
		else:
			for ext in DAY_EXTENSIONS:
				found = word.find(ext)
				if found > 0:
					try:
						day = int(word[:found])
						
					except:
						pass
	if month < today.month and month != -1:
		year = year + 1
			
	if day < today.day and month ==-1 and day != -1:
		month = month + 1
			
	if month == -1  and day == -1 and day_of_week != -1:
		current_day_of_week = today.weekday() #0 - 6 with 0 being Monday
		dif = day_of_week - current_day_of_week
		if dif < 0:
			dif += 7
			if text.count("next") >= 1:
				dif += 7
		return today + datetime.timedelta(dif)
	if month == -1 or day == -1:
		return None
	return datetime.date(month = month, day = day, year = year)

#This function creates a text file (.txt) and appends any speech detected to the
#file as text
def note(text):
	date = datetime.datetime.now()
	file_name = str(date).replace( ":", "-") + "-note.txt"
	with open(file_name, "w") as f:
		f.write(text)
	subprocess.call(["open", "-a", "TextEdit", file_name])

#The basic calls to implement the above two functions
WAKE = "hey computer"
calendar_calls = ["what do I have", "do I have plans", "am I busy", "what am I doing"]
note_calls = ["make a note", "write this", "remember to"]
service = authenticate_google()
print("START")

#This loops constantly runs and is always checking for calls from the user,
#with the outline all set out it is very easy to add more calls or API's
#to the voice assistant such as the Apple Music API
while True:
	print("Listening")
	
	text = get_audio()
	
	if text.count(WAKE) > 0:
		speak("Hello, how can I help you?")
		
		text = get_audio()

		for call in calendar_calls:
			if call in text:
				date = get_date(text)
				if date:
					get_events(get_date(text), service)
				else:
					speak("Please repeat that, I didn't understand")

		for call in note_calls:
			if call in text:
				speak("What would you like me to write down?")
				note_text = get_audio()
				note(note_text)
				speak("I wrote that down for you.")
