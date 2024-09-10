from confluent_kafka import Consumer
import json
from json import dumps
from esdbclient import EventStoreDBClient, NewEvent, StreamState


###############
# This is a CDC example
# it reads the kafka topic
# that debezium is generating messages to
# for each change of the tables in the inventory
# database
########

##############
# Create a function to generate 
# a list of events
# It will be called from our kafka 
# polling loop
################

events_list = []

def event_generator(key, value, offset, timestamp):
  ################
  # Accepts key(json), value(json), offset(int), 
  # and timestamp(two fields) from kafka topic
  ###############

  # parse the JSON key and value into python dict
  key_dict = json.loads(key) 
  value_dict = json.loads(value) 

  # concatenate the key and value dicts
  combined_k_v = {'key': key_dict, 'value': value_dict} # combine the two
  
  # convert to a string
  value_string = json.dumps(combined_k_v)

  # extract the transaction ID (gtid)
  # Write as metadata
  gtid = value_dict['payload']['source']['gtid']
  metadata_string = f'{{"offset": {offset}, "timestamp": "{timestamp}", "$correlationId": "{gtid}"}}'

  #################
  # Pull the dml operation, insert, update, delete, etc
  # From the nested JSON(dict)
  # This will be reflected in the EventType
  ################
  
  dml_op = value_dict['payload']['op']
  
  match dml_op:
       case "u" :
        event_type = "Update"
       case "d" :
        event_type = "Delete"
       case "c":
        event_type = "Insert"
       case "r":
        event_type = "Snapshot" 
       case _:
        event_type = "Other"        
 
  ###############
  # Create an EventStore Event object
  #################
  
  event = NewEvent(
    type = event_type,
    data = value_string.encode("UTF-8"),
    metadata = metadata_string.encode("UTF-8")
    
    )
  
  #############
  # Append to a list
  # kafka consumer.poll seems to pull one event at a time
  # So this doesn't seem needed, but including in case
  # of edge case where multiple events are generated
  #############
  
  events_list.append(event)


###########
# Define a kafka consumer
# For testing purposes
# auto.commit is set to true, messages are deleted from queue after processing
# you may want to set this to false during development, so that you
# have events in the queue after minor code changes
# This leaves messages on kafka after reading theml
# enabling a restart to process old data rather
# than having to switch to mysql console to regenerate messages
###########

c = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'testing12345',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': 'true' 
})

#####################
# Subscribe to topics
# consumer.subscribe accepts a list of topics
# Debezium create one topic per table
# this example subscribes to a subset of vailable tables
#####################

c.subscribe(['dbserver1.inventory.customers','dbserver1.inventory.products','dbserver1.inventory.products_on_hand'])


####################
# Create Dictionary of table(topic) => Primary Key
# Knowing the Column(s) that serve as the Primary Key is
# useful this dictionary enables quick  lookup of Primary Key
######################


pk_lookup = {"dbserver1.inventory.products":"id","dbserver1.inventory.customers":"id","dbserver1.inventory.products_on_hand":"product_id"}




############
# Define EventStore Client
# The shell script that is provided starts a docker container
# with projections enabled and running
# If you are using your own eventstore, enable and start projections
#############
client = EventStoreDBClient(uri="esdb://localhost:2113?tls=false")



#############
# Create a function to write to Event Store
# stream_name will be table_name-rowid 
# where rowid is the primary key column for that table
# event type will be insert/delete/update/snapshot
#############

def stream_appender(events_array, stream_name):
    client.append_to_stream(
    stream_name,
    events = events_array,
    current_version = StreamState.ANY
)


##############
# This is the infinite polling loop for kafka
# ctrl-c in terminal to kill
#
##############

try:
    while True:
        msg = c.poll(1.0)
        if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
            print("Waiting... ctrl-c to stop....")
        elif msg.error():
            print("ERROR: %s".format(msg.error()))   
        else:
           # A message has arrived
        
            if(msg.value()):
                # decode the message, kafka sends bytes
                key = msg.key().decode('utf-8')
                value = msg.value().decode('utf-8')

                # extract offset and timestamp
                # These are stored in EventStoreDB as metadata
                offset = msg.offset()
                timestamp = msg.timestamp()
                 
                # Extract the row_id
                # Stream Name will be table_name-row_id
                # Lookup Primary Key, then extract from json
                # payload from kafka
                pk = pk_lookup[msg.topic()]
                row_id = json.loads(key)['payload'][pk]

                # Extract table name
                # and Database_name 
                # There are actually a number of ways to get thess values
                # Parsing the json of the decoded message in this example
                table_id = json.loads(value)['payload']['source']['table']
                db_id = json.loads(value)['payload']['source']['db']
                
                
                # Name the stream
                # Our convention in this example is
                # table_name-row_id
                # This enables use of the category projection
                stream_name = f"{table_id}-{str(row_id)}"

    
                # Informational output to console
                print("\nGOT AN EVENT\n")
                print(msg.topic())
                print(f"row_id = {row_id}")
                print(f"number of events: {len(events_list)}")
                print(f"VALUE is \n {value}")
                print(f"Key is \n {key}")

                # Call the event generator function
                event_generator(key, value, offset, timestamp)
                
                # append events to Event Store
                stream_appender(events_list,str(stream_name))
                
                # truncate the events list
                events_list.clear()



               
except KeyboardInterrupt:
    pass
finally:
        # Leave group and commit final offsets
        c.close()

