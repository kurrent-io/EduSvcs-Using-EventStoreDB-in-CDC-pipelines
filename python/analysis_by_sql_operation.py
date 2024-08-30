from esdbclient import EventStoreDBClient
import pandas as pd
import matplotlib.pyplot as plt

#########
# Using CDC data represented in EventStoreDB for 
# analysis of SQL operations
#########

#########
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
        'Event_Type': event.type
        }

    )

######################
# Events in a projection are links to the 
# original event in other in another stream
# setting resolve_links to true will retrieve the 
# Event from the source stream
#####################


stream_list = ["$et-Insert","$et-Delete","$et-Snapshot","$et-Update"]
for stream in stream_list:
    try:
       events = client.get_stream(stream, resolve_links=True)
       for event in events:
          add_data(event)
          print("success")
    except:
        print(f"no such stream: {stream}")





client.close()

#############
# Process the data in the list
##########

# convert to pandas dataframe
df = pd.DataFrame(d)

# print some information to terminal
print("\n\nFIRST FEW LINES OF PANDAS DATAFRAME")
print(df.head())
print("\n\nSHAPE OF PANDAS DATAFRAME")
print(df.shape)


# Count records per Event Type
value_counts = df['Event_Type'].value_counts()

# Create a pie chart
value_counts.plot.pie(autopct='%1.1f%%')
plt.title('Category Distribution')

# Save figure to disk plt.show() could also be used
plt.savefig('SQL-op-distributionp-pie-chart.png')
plt.close()


# Create a bar chart
value_counts.plot.bar()
plt.savefig('SQL-op-distribution-bar-chart.png')


# Print to terminal
print("-" * 20)
for col in df.columns:
    print(f"Value counts for column {col}:")
    print(df[col].value_counts())
    print("-" * 20)