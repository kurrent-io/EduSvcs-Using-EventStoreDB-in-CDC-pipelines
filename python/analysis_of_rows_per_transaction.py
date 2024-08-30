from esdbclient import EventStoreDBClient, NewEvent, StreamState
import json
import pandas as pd
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
from ydata_profiling import ProfileReport
import matplotlib.pyplot as plt

#########
# Using CDC data represented in EventStoreDB for 
# analysis of transactions
#########


##########
# Enabling By_Event_Type projection allows 
# A client to read or subscribe to a stream that contains
# all Delete, or all Update, or all Insert operations
# with those projections enabled some quick visualizations of the 
# distribution of operations can be performed using pandas 
#########

client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")

# create an empty list to store data
d = []

# create a function to add data from events
# into the list

def add_data(event):
     d.append(
        {
        #'metadata':json.loads(event.metadata.decode('utf-8')),
        #'offset': json.loads(event.metadata.decode('utf-8'))['offset'],
        'correlationID' : json.loads(event.metadata.decode('utf-8'))['$correlationId'],
        'event': event.stream_name,
        'Event_Type': event.type
        }
    )


######################
# Events in a projection are links to the 
# original event in other in another stream
# setting resolve_links to true will retrieve the 
# Event from the source stream
#####################


stream_list = ["$ce-customers"]
for stream in stream_list:
    try:
       events = client.get_stream(stream, resolve_links=True)
       for event in events:
          add_data(event)
    except:
        print(f"no such stream: {stream}")

client.close()

#############
# Process the data in the list
##########

# convert to pandas dataframe
df = pd.DataFrame(d)

# Remove the Snapshot Events (original debezium load of source tables)
df = df[df['Event_Type'] != 'Snapshot']

# print some information to terminal
print("\n\n####### VIEW OF Pandas Dataframe #######\n\n")
print(df.head())

# For this dataframe Shape will be rows,columns
print("\n\nDatafrane Shape \nRows : Columns")
print(df.shape)

# Count Correlation IDs, which will be the total number of transactions
# Snapshots have no transaction ID
# Remove rows where Age is less than 30
#df = df[df['correlationID'] != 'Snapshot']

counts = df['correlationID'].value_counts()
print(f"\n\nmax rows per transaction is {counts.max()}")  
print(f"min rows per transaction is {counts.min()}") 
print(f"median rows per transaction is {counts.median()}")

quantiles = counts.quantile([0.1, 0.2, 0.3 , 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
plt.bar(quantiles.index, quantiles.values)
plt.xlabel('Quantiles')
plt.ylabel('Number of rows per transaction')
plt.title('Quantiles of Value Counts')
plt.savefig("quantiles.png")


# percentage of single row transactions

percentage = (counts[counts > 1].sum() / counts.sum()) * 100

print(f"\n\npercentage of transactions of more than 1 row = {percentage}")
print(f"counts of single row transactions = {counts[counts == 1].sum()}")
print(f"counts of multi-row transactions = {counts[counts != 1].sum()}\n")




