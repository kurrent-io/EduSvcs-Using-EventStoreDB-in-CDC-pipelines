from esdbclient import EventStoreDBClient, NewEvent, StreamState
import json
import pandas as pd
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
from ydata_profiling import ProfileReport
import matplotlib.pyplot as plt
#from pandas_profiling import ProfileReport
# Import pandas profiling library
# import ydata_profiling as pp

#########
# Enabling Category projections allows 
# A client to read all the change event per table
# An application could also subscribe to this projection and changes 
# would pushed to the client. 
#########
client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")


# Note the setting resolve_links, events in a projection are links to the 
# original event in other languages the setting is resolveLinkTos = True
# The projection is ce-customers, any events in a stream with a name customers-xxxxx
# will become part of this projection
events = client.read_all(
    commit_position=0,
    limit=1000,
    resolve_links=True,
)

d = []
for event in events:
    # print((json.loads(event.metadata.decode('utf-8'))))
    # print(event.stream_name)
    # print(f"{event.type}")
    d.append(
        {
        #'metadata':json.loads(event.metadata.decode('utf-8')),
        'offset': json.loads(event.metadata.decode('utf-8'))['offset'],
        'correlationID' : json.loads(event.metadata.decode('utf-8'))['$correlationId'],
        'event': event.stream_name,
        'Event_Type': event.type
        }
    )
    print("##########")
    #print(event.data)


# d = []
# for p in game.players.passing():
#     d.append(
#         {
#             'Player': p,
#             'Team': p.team,
#             'Passer Rating':  p.passer_rating()
#         }
#     )

#print(d[0])
my_dataframe = pd.DataFrame(d)
print(my_dataframe.head())
#my_dataframe.plot(x="Event_Type", y="Age", kind="bar")
#plt.pie(my_dataframe["Event_Type"]) 
#plt.show() 

plt.hist(my_dataframe["Event_Type"]) 
plt.title("Histogram of SQL Ops")
#plt.show() 
plt.savefig("SQL_OP_HISTO")
plt.close()

## View distibution of transaction size
## 
plt.hist(my_dataframe["correlationID"]) 
plt.title("Histogram of Correlation ID")
#plt.xticks(rotation="vertical")
plt.xticks(rotation=45, ha='right')
plt.subplots_adjust(bottom=0.55)
#plt.figure.Figure.auto

#plt.show() 
plt.savefig("Correlation_Histo")
plt.close()

######## NEXT ######
#plt = (my_dataframe["correlationID"].).plot.bar()

fig, ax = plt.subplots(1,1)
plt = my_dataframe["correlationID"].value_counts().plot.bar()
fig.tight_layout()
fig.savefig("correlation_bar")
#plt.figure.savefig("Correlation_bar")
# plt.title("Barof Correlation ID")
# #plt.xticks(rotation="vertical")
# plt.xticks(rotation=45, ha='right')
# plt.subplots_adjust(bottom=0.55)
# plt.figure.Figure.auto

# #plt.show() 
# plt.savefig("Bar_Histo")
# plt.close()



# this creates a series, have to 
correlation_Id_counts = (my_dataframe["correlationID"].value_counts())

print("###### Correlation ID Counts#########")
print(correlation_Id_counts)


SQL_Operation_counts = (my_dataframe["Event_Type"].value_counts())
print("###### SQL OP Counts#########")
print(SQL_Operation_counts)
# this should plot it
#plot = my_dataframe.groupby("correlationID").plot(kind="bar", title="DataFrameGroupBy Plot")
#plot.show()

profile = ProfileReport(my_dataframe, title="Profiling Report")
profile.to_file("your_report.html")
#profile = ProfileReport(my_dataframe)
#profile.to_file("output.html")
#pp.ProfileReport(my_dataframe, title="Pandas Profiling Report").to_file("report.html")
#my_dataframe.eval()
print("success")
client.close()