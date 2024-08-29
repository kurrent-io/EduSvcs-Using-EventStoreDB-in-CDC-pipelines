from esdbclient import EventStoreDBClient, NewEvent, StreamState

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
events = client.get_stream("$ce-customers", resolve_links=True)


for event in events:
    print(f" \n {event.type}")
    print(event.data)

print("success")
client.close()