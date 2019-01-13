
# coding: utf-8

# In[ ]:


##importing info for gmail API
from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
##regex for dates
import re
##for days of week
import datetime
##for limiting api extraction
import time
##for interacting with sql tables
import sqlite3


# In[ ]:


##takes an email id as an input and outputs the day of the week the email was sent and the email id in a list
def get_day_of_week_with_semicolon(data):
    message_id = data['id']
    message = service.users().messages().get(userId='me', id=message_id).execute()
    text = message['snippet']
    ex = message['payload']['headers'][1]['value'].split(';')[1].strip()
    date = re.findall('[a-zA-Z]{3}', ex)[0]
    return [message_id,date]


# In[ ]:


##takes an email id as an input and outputs the day of the week the email was sent and the email id in a list
def get_date_from_edge_case_1(data):
    message_id = data['id']
    message_edge_case = service.users().messages().get(userId='me', id=message_id).execute()
    text = message_edge_case['snippet']
    regex_value = re.findall('\d{2}/\d+/\d{4}', text)[0].split('/')
    d = datetime.date(int(regex_value[2]),int(regex_value[0]),int(regex_value[1]))
    lst_of_week = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    date = lst_of_week[d.weekday()]
    return [message_id,date]


# In[ ]:


##takes an email id as an input and outputs the day of the week the email was sent and the email id in a list
def get_date_from_edge_case_2(data):
    message_id = data['id']
    message_edge_case = service.users().messages().get(userId='me', id=message_id).execute()
    text = message_edge_case['snippet']
    for day in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
        if day in text:
            date = day
    return [message_id,date]


# In[ ]:


##takes an email id as an input and outputs the day of the week the email was sent and the email id in a list
def get_date_from_edge_case_3(data):
    message_id = data['id']
    message_edge_case = service.users().messages().get(userId='me', id=message_id).execute()
    for day in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
        if day in message_edge_case['payload']['headers'][1]['value']:
            date = day
            return [message_id,date]


# In[ ]:


##takes an email id as an input and outputs the day of the week the email was sent and the email id in a list
def get_date_from_edge_case_4(data):
    message_id = dictionary['id']
    message = service.users().messages().get(userId='me', id=message_id).execute()
    for d in message['payload']['headers']:
        if d['name'] == 'Date':
            for day in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
                if day in d['value']:
                    date = day
                    return [message_id,date]


# In[ ]:


##takes a dictionary that has a list of message id’s within it. It goes through each id and makes a request to the gmail API for said id via the above functions. It outputs a list of lists. It also pauses briefly every 50 retrievals as to not overload the api
def process_api_results(results):
    count = 0
    lst = []
    for item in results['messages']:
        try:
            ##tries to get date using primary gmail api information structure, if successful, adds date and id to list and increases count
            value = get_day_of_week_with_semicolon(item)
            if type(value) != type([]):
                print('level1')
                break
            lst.append(value)
            count += 1
        except:
            try:
                ##tries to get date using 1 alternative gmail api information structure, if successful, adds date and id to list and increases count
                value = get_date_from_edge_case_1(item)
                lst.append(value)
                count += 1
            except:
                try:
                    ##tries to get date using 1 alternative gmail api information structure, if successful, adds date and id to list and increases count
                    value = get_date_from_edge_case_2(item)
                    lst.append(value)
                    count += 1
                except:
                    try:
                        ##tries to get date using 1 alternative gmail api information structure, if successful, adds date and id to list and increases count
                        value = get_date_from_edge_case_3(item)
                        ##get_date_from_edge_case_3 won't cause an error if the structure doesn't match, so it checks the return value
                        if type(value) != type([]):
                            value = get_date_from_edge_case_4(item)
                        if type(value) == type([]):
                            lst.append(value)
                            count += 1
                        else:
                            print("this id didn't work:" + item['id'])
                    except:
                        ##if a returned email structure isn't like any that i have seen, then it won't be added to the database
                        print("this id didn't work: " + item['id'])
        ##this slows the retrieval of data
        if count % 50 == 0 : time.sleep(1)
    return lst


# In[ ]:


##This takes a list of lists and writes to a database called ‘emails.sqlite’. If the database doesn’t exist, it creates a table with a column for the day of the week and a column for the email id. If the database does exist, the function retrieves all the email ids currently in the database and only adds new ones. There are no set inputs/outputs, just the database creation/change
def write_to_database(lst):
    conn = sqlite3.connect('emails.sqlite')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS emails (email_id TEXT, day TEXT)')
    count = 0
    cur.execute('SELECT email_id FROM emails')
    lst_of_tups = cur.fetchall()
    lst_of_ids = []
    for tup in lst_of_tups:
        lst_of_ids.append(tup[0])
    for l in lst:
        email_id = l[0]
        day_of_week = l[1]
        if email_id not in lst_of_ids:
            cur.execute('INSERT INTO emails (email_id, day) VALUES (?, ?)', (email_id, day_of_week))
            count += 1
            if count % 10 == 0:
                conn.commit()
    conn.commit()


# In[ ]:


##doesn’t have any set inputs or outputs. It instead takes information from the emails.sqlite file and prints the day that has the most emails. It also prints each day and how many emails they have
def process_data():
    conn = sqlite3.connect('emails.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT day FROM emails')
    lst_of_days = []
    d ={}
    lst_of_tups = cur.fetchall()
    for tup in lst_of_tups:
        lst_of_days.append(tup[0])
    for ky in ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']:
        d[ky] = 0
    for day in lst_of_days:
        d[day] += 1
    sorted_days = sorted(d.keys(), key = lambda x : d[x], reverse = True)
    print('The day with the most emails is ' + sorted_days[0] + ' which has ' + str(d[sorted_days[0]]) + ' emails.')
    for ky in sorted_days:
        print(ky + ' had ' + str(d[ky]) + ' emails.')
    cur.close()


# In[ ]:


##doesn’t have any set inputs. It instead takes information from the emails.sqlite database and creates a bar chart with the days of the week on the x axis and the number of emails on the y axis.
def show_data():
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    conn = sqlite3.connect('emails.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT day FROM emails')
    lst_of_days = []
    d ={}
    lst_of_tups = cur.fetchall()
    for tup in lst_of_tups:
        lst_of_days.append(tup[0])
    days = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    for ky in days:
        d[ky] = 0
    for day in lst_of_days:
        d[day] += 1
    x = []
    y = []
    colors = ['red', 'green', 'black', 'yellow', 'purple', 'pink', '#3377ff']
    for tup in d.items():
        x.append(tup[0])
        y.append(tup[1])
    graph = plt.bar(x,y)
    for i in range(len(colors)-1):
        graph[i].set_color(colors[i])
    plt.xlabel('Day')
    plt.ylabel('Number of Emails')
    plt.title('Number of Emails by Day')
    red_patch = mpatches.Patch(color='red', label='Monday')
    green_patch = mpatches.Patch(color='green', label='Tuesday')
    black_patch = mpatches.Patch(color='black', label='Wednesday')
    yellow_patch = mpatches.Patch(color='yellow', label='Thursday')
    purple_patch = mpatches.Patch(color='purple', label='Friday')
    pink_patch = mpatches.Patch(color='pink', label='Saturday')
    blue_patch = mpatches.Patch(color='#3377ff', label='Sunday')
    plt.legend(handles=[red_patch,green_patch,black_patch,yellow_patch,purple_patch,pink_patch,blue_patch])
    plt.show()


# In[ ]:


##The file token.json stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
##MAKE SURE YOU HAVE THE CREDENTIALS FILE AND THAT YOU DID THE PIP INSTALL THING
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('gmail', 'v1', http=creds.authorize(Http()))

# Call the Gmail API
results = service.users().messages().list(userId='me').execute()
##process the api results and put them into a list with [message id, day of week sent]
lst = process_api_results(results)
##write list to database
write_to_database(lst)
##process the data
process_data()
##show the data
show_data()
