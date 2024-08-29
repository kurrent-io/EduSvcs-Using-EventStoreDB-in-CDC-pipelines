# Using EventStoreDB in your CDC(Change Data Capture) pipelines

## Introduction

### Overview

Moving Data from your operational Data Stores into your Data Warehouse, Data Lake, or Lake House is a common requirement.

A popular tool for that task is to implement a CDC pipeline using Debezium.

Debezium translates Change Data Capture (CDC) events from a variety of sources, and translates those CDC envents into a common format, allowing those events to be ingested by various sinks, including Data Lakes, LakeHouses, No SQl stores and more.

### Benefits of EventStoreDB

Using Event Store DB as a sink can be a very useful hub in your data redistribution workflow for the following reasons.

1. Event Store DB provides an immutable log of CDC events
2. Event Streams in Event Store DB can be subscribed to
3. Event Store DB projectioins engine allows subscription a granular subset of events, or a larger aggregation of events

Leveraging the ability to subscribe to CDC events **after** they land in EventStoreDB, with granular control over which subset of events to subscribe to, makes EventStoreDB act more like a hub, than just another sink.

Also the fact that the events are ordered, and durable provides options to reprocess, or audit and analyze as needed.

## Structure of this content

This content consists of 2 parts:

1. This document that provides a text overview of the features and benefits
2. The document code_example.md that provides an overview of the code in this github repo

## Architecture of typical Debezium based CDC pipeline

### At a high level the basic architecture involves these tools

<img src="./resources/excalidraw-animate_slow.svg" alt="Image of Database to Debezium to EventStoreDB Data Flow" style="width: 80%;"/>

### A more granular view of the tools, showing required supporting features and products

<img src="./resources/Data_flow_with_supporting_features.svg" alt="CDC pipeline with all the tools " style="width: 80%;"/>


## Lifecycle of a CDC Event (mysql->EventStoreDB)

Whenever data is modified in the source database, by a create (insert), delete, or update statement one or more CDC events will propagate through our pipleine in the following manner. This example will use a single row insert as an example. 

### Step 1. The database server, MySQL or MariaDB will write the event to it's binlog

The binlog is used for database replication, and all changes to the database are logged to the binlog if it is enabled. The binlog is usually enabled by default. Note that in order to get transaction ID's logged into the binlog the setting gtid_mode=ON must be set. The code example starts a docker container running MySQL, and that setting is enabled in the startup script. See ```03_mysql.sh``` in this repo.

### Step 2. Debezium will pick up the data change event from the binlog

Debezium is impersonating the role of another MySQL instance that would be acting as a replica to be used as a backup, or scaling reads. The setting of server-id is significant for this process, if you were fanning out multiple replicas with multiple debezium instances reading the binlog of a single mysql instance, setting unique server-ids is critical.

### Step 3. Debezium will transform the binlog event into a standard CDC event and post the event to a kafka topic

There will be one kafka topic per table. Note that in the example repository the code that reads from kafka only subscribes to 3 of the topics/tables.

Also note that typically once a message hase been consumed, the consumer informs kafka to not resend that message to this consumer group ```'enable.auto.commit': 'true'```. Setting this to false can be useful to quickly debug your code that processes messages, because when you restart your code you would not have to generate new messages in the pipeline, your code would reread the same messages each time it is restarted.

### Step 4. Python(or other language) application to consume kafka messages and write them to EventStoreDB

With change events being propogated through to a kafka topic per table, the remaining step is to read the kafka events, and write to EventStoreDB.

## Mapping of Database Tables to Kakfa topics

A quick review of Debezium behavior as it processes CDC events. 

Debezium will create one kafka topic per table. For each row changed a message will be created for that topic.

<img src="./resources/Database_table_to_kafka_topic.svg" alt="Database Tables mapped to Kafka Topics" style="width: 80%;"/>

## Mapping Kafka Topics/Messages to EventStoreDB Streams

The next step is to get messages from kafka topics into EventStoreDB streams.

There are a number of options you could choose when you write the CDC messages into EventStoreDB as events.

First, a quick review of EventStoreDB functionality.

1. EventStoreDB stores immutable Events into an append only log
2. When appending an event we specify the following
    * Stream Name
    * Event Type
    * Event Data
    * Event Metadata
3. Applications can subscribe to a stream or streams

With EventStoreDB's features in mind. Here is a review of some stream design options.

## One stream per topic/table

This configuration would be straightforward, the code may choose to extract a field from the kafka payload and use it to set "Event Type", or the code could more or less ingest the message content as is.

The immutable audit log functionality of EventStoreDB is preserved, ordering of vents is preservered, and clients could subscribe to changes for a particular table.

<img src="./resources/Kafka-ES-stream-per-topic.svg" style="width: 80%;" alt="image">

## One stream per row

This configuration is what the code example in this repository demonstrates. The following features of the event are set by parsing either the topic itself, or the payload of the message.

### 1. Stream Name set to TableName-rowid

As a message is consumed from the per table kafka topic it is parsed and the row identifier for the changed row is extracted and used as the second part of the Stream Name for the event. ```TableA-row1``` for example.

### 2. Event Type set to SQL operation

The message payload is parsed to extract the SQL operation, Delete, Insert(create),Update, Snapshot(initial read) and Event Type is set to that value.

### 3. Correlation ID set to transaction ID

A single transaction may modify more than one row, if GTID(global transaction ID's) are enabled on the MySQL server, Debezium will pick up that value and it will be part of the message payload. In the code example that value is extracted and becomes part of the events Metadata.

### Below is a diagram showing this design

Note to keep the diagram concise, only one tables row changes are diagrammed here. Many streams are created per table, and including each would quickly create a crowded image.

Since the relationship between SQL table events to streams diverges in this configuration it might be useful to describe an example.

If a row is created, and never modified, there will be a stream in EventStoreDB with a single event of Event Type Create

If a row is created, updated once, and then deleted there will be a stream in EventStoreDB with 3 events one of Event Type Create, one of Event Type Update, and one of Event Type Delete.

<img src="./resources/K-to-ES-stream-per-row.svg" style="width: 80%;" alt="image">

## Leveraging EventStoreDB projection Engine

EventStoreDB's built in projection engine can be extremely useful as a way of enabling applications, data scientists, or other data users to subscribe to changes across an aggregation of streams. The diagram below shows the functionality.

Basically, events from one stream may be projected into another stream. Here is the documentation, [projections](https://developers.eventstore.com/server/v5/projections.html#system-projections)

By enabling all projections on the EventStoreDB server you will be enabling the following functionality.

* Subscribe to changes to all rows in a table
* Subscribe to a stream of all Updates, or Inserts, or Deletes across all tables
* View all rows affected by a single transaction

Visualization of EventStoreDB projections as applied to CDC events. 

<img src="./resources/Projections.svg" style="width: 80%;" alt="image">

## Summary

This document provides a written overview, and introduction of the functionality that EventStoreDB can add to your CDC pipelines

There is more to this repository if you would like to explore.

### Shell scripts to build a pipeline

The shell scripts, 01****.sh, 02***.sh, etc are mostly docker commands to build a MySQL->Debezium->kafka->EventStoreDB pipeline. 

### SQL scripts to modify a MySQL database to create events for the pipeline

The sql folder contains these.

### Python code to process the kafka messages into EventStoreDB events

See the python folder.

If you have trouble running the python code locally, see our "Python From Scratch" Repository for advice on setting up your local Event Store python code environment.

The code in the github repo provides some examples of both writing a stream per row, and reading from the projections to build a few visualizations. 

------------------------------
