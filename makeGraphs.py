import sys
import plotly
import datetime
import json
import statistics
import plotly.plotly as py
import plotly.graph_objs as go

plotlyUsername = "" #Your plotly username
plotlyAPIKey = "" #Your plotly API Key
fileName = "" #The JSON file with the FB messenger data
personName = fileName.split(".")[0]

if plotlyUsername == "" or plotlyAPIKey == "" or fileName == "":
	print "Fill in your information"
	sys.exit(1)

plotly.tools.set_credentials_file(username=plotlyUsername, api_key=plotlyAPIKey)

with open(fileName) as data_file:
	data = json.load(data_file)

allDates, dateCounts, allWeeks, weekCounts, myResponseTime, theirResponseTime = [], [], [], [], [], []
messageCount, charCount = [0, 0], [0, 0]
dayOfWeekCount = [0, 0, 0, 0, 0, 0, 0]
prevPerson = ""
prevMili = 0

#Go through all messages
for message in data["messages"]:
    date = datetime.datetime.fromtimestamp(int(message["sent"])/1000.0)

    #Maintain count for messagers per day
    datestring = str(date.date())
    try:
		index = allDates.index(datestring)
    except:
		index = -1
    if index == -1:
		allDates.append(datestring)
		dateCounts.append(1)
    else:
		dateCounts[index] = dateCounts[index] + 1


    #Maintain count for messages per week
    iso = list(date.isocalendar())
    d = str(iso[0]) + "-W" + str(iso[1])
    datestring = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")
    try:
		index = allWeeks.index(datestring)
    except:
		index = -1
    if index == -1:
		allWeeks.append(datestring)
		weekCounts.append(1)
    else:
		weekCounts[index] = weekCounts[index] + 1

    #Maintain count for day of week
    dayOfWeek = date.weekday()
    dayOfWeekCount[dayOfWeek] = dayOfWeekCount[dayOfWeek] + 1

    #Maintain message and char counts
    senderIndex = 0 if message["sender"] == 'me' else 1
    messageCount[senderIndex] = messageCount[senderIndex] + 1
    charCount[senderIndex] = charCount[senderIndex] + len(message["content"])

    #Maintain responseTimes
    if prevMili > 0 and not prevPerson == message["sender"]:
        if prevPerson == 'me':
            myResponseTime.append(prevMili - int(message["sent"]))
        else:
            theirResponseTime.append(prevMili - int(message["sent"]))
    prevMili = int(message["sent"])
    prevPerson = message["sender"]


def plotGraph(scatter, xData, yData, title, xTitle, yTitle, mode='lines'):
    if scatter:
        data = [go.Scatter(x=xData, y=yData, mode=mode)]
    else:
        data = [go.Bar(x=xData, y=yData)]
    layout = go.Layout(
        title = title,
        hovermode = 'closest',
        xaxis = dict(title=xTitle),
        yaxis = dict(title=yTitle),
        showlegend = False
    )
    py.plot(go.Figure(data=data, layout=layout), filename= title + ' - ' + personName)

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
people = ['Me', personName]
plotGraph(True, allDates, dateCounts, "Messages Per Day Over Time", "Date", "Number of Messages")
plotGraph(True, allWeeks, weekCounts, "Messages Per Week Over Time", "Week", "Number of Messages", mode='lines+markers')
plotGraph(False, days, dayOfWeekCount, "Messages Per Day Of Week", "Day of Week", "Number of Messages")
plotGraph(False, people, charCount, "Characters Sent Comparison", "Sender", "Number of Characters")
plotGraph(False, people, messageCount, "Messages Sent Comparison", "Sender", "Number of Messages")

theirMedian = (statistics.median(theirResponseTime)/1000.0)
myMedian = (statistics.median(myResponseTime)/1000.0)
theirMean = (statistics.mean(theirResponseTime)/1000.0)
myMean = (statistics.mean(myResponseTime)/1000.0)
data = [go.Bar(x=people, y=[myMean, theirMean], name="Mean Reponse Time"),
        go.Bar(x=people, y=[myMedian, theirMedian], name="Median Reponse Time")]
layout = go.Layout(
    title = "Response Times",
    hovermode = 'closest',
    xaxis = dict(title="Person"),
    yaxis = dict(title="Seconds"),
    showlegend = True,
    barmode = 'group'
)
py.plot(go.Figure(data=data, layout=layout), filename= 'Response Times - ' + personName)
