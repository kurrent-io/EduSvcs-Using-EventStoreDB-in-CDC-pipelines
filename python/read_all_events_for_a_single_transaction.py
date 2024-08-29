from esdbclient import EventStoreDBClient, NewEvent, StreamState

#########
# Enabling $by_correlation_id projections allows 
# A client to read all the changes caused by a transaction
#########
client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")


# Note the setting resolve_links, events in a projection are links to the 
# original event in other languages besides python the setting is resolveLinkTos = True
# The by correlation_id projection projects events with matching correlation ID's in the Event's 
# metadata to a stream

# Note you will have to replace the stream_name here with 
# a value from a multi-row operation. 
# the sql folder has an add_customers script that adds 5 customers in one transaction
# use the correlation ID from one of the per row events

stream_name = "$bc-085e79cf-5fd7-11ef-bc6e-0242ac110004:39"
events = client.get_stream(stream_name, resolve_links=True)


for event in events:
    print(f" \n {event.type}")
    print(event.data)

print("success")
client.close()