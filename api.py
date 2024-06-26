import spacy,datetime, re, requests
from dateutil.parser import parse
from flask import Flask, request
from dateutil.relativedelta import relativedelta
nlp = spacy.load("en_core_web_sm")

def extract_time(example):
    doc = nlp(example)
    meeting_time = None
    for ent in doc.ents:
        if ent.label_ in ["DATE", "TIME"]:
            if meeting_time is None:
                meeting_time = ent.text
            else:
                meeting_time += " " + ent.text
    return(meeting_time)

pattern = r'^[\d:]+$'
def scheduling_time(e):
    e = e.lower().replace(".", "").replace(" o'clock","o'clock")#.split()
    e = re.sub(r'(\d+)\s*([ap]m)', r'\1\2',e).split()
    tim = []
    for element in e:
        if bool(re.match(r"^\d{4}",element)):
            continue
        if "o'clock" in element:
            element = element.replace("o'clock","")
            if int(element)<8:
                element = element + "pm"
        element = element.replace("12:","0:")
        if ("pm" in element):
            element = element.replace("pm","")
            for a in range(len(element.split(":"))):
                if a == 0:
                    alpha = ""
                    alpha+= str(int(element.split(":")[0])+12)
                else:
                    alpha+= ":"+element.split(":")[a]
            element = alpha
        element = element.replace("am","").replace("pm","").replace(" ","")
        if bool(re.match(pattern, element)):
            element = element+(":00"*(2 - element.count(":")))
            element = "0"*(2-len(element.split(":")[0])) +element
            tim.append(element)
    return tim

def extract_and_format_dates(text):
    text = text.lower()
    doc = nlp(text)
    dates = []
    today = datetime.date.today()
    
    day_name_mapping = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    
    for token in doc:
        if token.text == "2023":
            continue
        if (token.ent_type_ == "DATE") and (token.text != "next"):
            if token.text == "thursday":
                dates.append(token.text)
            else:
                dates.append(token.text.replace("th",""))
        if token.text.lower() == "next" and token.nbor(1).text.lower() in day_name_mapping:
            day_name = token.nbor(1).text.lower()
            target_day = day_name_mapping[day_name]
            days_until_target = (target_day - today.weekday() + 7) % 7
            date = today + relativedelta(days=days_until_target, weeks=1)
            given = date.strftime("%B %d, %Y")
            dates.append(given.replace("th,",""))
    formatted_dates = []
    for date_str in dates:
        try:
            parsed_date = parse(date_str)
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            formatted_dates.append(formatted_date)
        except ValueError:
            pass  # Skip invalid date strings
    return formatted_dates

# Process and extract dates from the sample sentences
def get_date(sentence):
# for sentence in sentences:
    current_time = str(datetime.datetime.now())
    c_year = current_time.split("-")[0]
    c_month = current_time.split("-")[1]
    c_day = current_time.split("-")[2].split()[0]
    year = c_year
    month = c_month
    day = c_day
    formatted_dates = extract_and_format_dates(sentence)
    if formatted_dates:
        if len(formatted_dates)>1:
            for date in formatted_dates:
                if date.split("-")[0] != c_year:
                    year = date.split("-")[0]
                if date.split("-")[1] != c_month:
                    month = date.split("-")[1]
                if date.split("-")[2] != c_day:
                    day = date.split("-")[2]
            formatted_dates = [str(year) +"-"+ str(month)+"-"+str(day)]
    else:
        formatted_dates = [str(year) +"-"+ str(month)+"-"+str(day)]
    return formatted_dates[0]

def main_fun(sentence,phone, timezone):
    e = extract_time(sentence)
    time_lis = scheduling_time(e)
    date_str = get_date(sentence)
    i = 0
    sc_dt = []
    for time_e in time_lis:
        sc_dt.append(date_str+"T"+time_e)
        i = i+1
        if i>1:
            break
    if len(sc_dt) ==1:
        try:
            input_datetime = datetime.datetime.fromisoformat(sc_dt[0])
            new_datetime = input_datetime + datetime.timedelta(hours=1)
            sc_dt.append(str(new_datetime.isoformat()))
        except ValueError:
            print("Invalid datetime format. Please use ISO format (e.g., '2023-10-17T12:30:00Z').")
    payload = {"receivedEvent":{
        "summary": "Test Event",
        "start":{
            "dateTime": sc_dt[0]+timezone
        },
        "end":{
            "dateTime": sc_dt[1]+timezone
        },
        "fromNumber" : phone
    }
    }
    return payload

url = "https://letava.ai.paklogics.com/app/createGoogleCalenderEvent"
app = Flask(__name__)
@app.route("/api/calander_python",methods=["Post"])
def calander_schedule():
    data = request.get_json()
    sentence = data["sentence"]
    phone = data["phone"]
    timezone = data["timezone"]
    payload = main_fun(sentence, phone, timezone)
    response = requests.post(url, json = payload)
    return(response.text)

if __name__ == "__main__":
    app.run(debug = True, port=5000)
