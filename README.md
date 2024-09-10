# Using EventStoreDB in your CDC(Change Data Capture) pipelines

## Introduction

### Overview

Moving data from your operational data stores into your data warehouse, data lake, or lakehouse is a common requirement.

A popular tool for that task is implementing a CDC pipeline using Debezium.

Debezium translates Change Data Capture (CDC) events from various sources into a common format, allowing them to be ingested by various sinks, including Data Lakes, LakeHouses, No SQL stores, and more.

### Benefits of EventStoreDB

For the following reasons, Using EventStoreDB as a sink can be a very useful hub in your data redistribution workflow.

1. EventStoreDB provides an immutable log of CDC events
2. Users can subscribe to EventStoreDB Event Streams
3. EventStoreDB Projections Engine allows subscription to a granular subset of events or a more extensive aggregation of events

Leveraging the ability to subscribe to CDC events **after** they land in EventStoreDB, with granular control over which subset of events to subscribe to, makes EventStoreDB act more like a hub than just another sink.

Also, the fact that the events are ordered and durable provides options to reprocess or audit and analyze as needed.

## Structure of this content

This content consists of two parts:

1. This document provides a text overview of the features and benefits
2. The document code_example.md that provides an overview of the code in this GitHub repo

## Architecture of typical Debezium-based CDC pipeline

### At a high level, the basic architecture involves these tools

<img src="./resources/excalidraw-animate_slow.svg" alt="Image of Database to Debezium to EventStoreDB Data Flow" style="width: 80%;"/>

### A more granular view of the tools, showing required supporting features and products

<img src="./resources/Data_flow_with_supporting_features.svg" alt="CDC pipeline with all the tools " style="width: 80%;"/>


## Lifecycle of a CDC Event (mysql->EventStoreDB)

Whenever data is modified in the source database by a create (insert), delete, or update statement, one or more CDC events will propagate through your pipeline in the following manner. This example will use a single-row insert. 

### Step 1. The database server, MySQL or MariaDB, will write the event to its binlog

The binlog is used for database replication, and all changes to the database are logged to the binlog if it is enabled. The binlog is usually enabled by default. Note that to get transaction IDs logged into the binlog, the setting gtid_mode=ON must be set. The code example starts a docker container running MySQL, and that setting is enabled in the startup script. See ```03_mysql.sh``` in this repo.

### Step 2. Debezium will pick up the data change event from the binlog

Debezium is impersonating the role of another MySQL instance that would act as a replica to be used as a backup or scaling reads. The setting of server-id is significant for this process. If you were fanning out multiple replicas with multiple Debezium instances reading the binlog of a single MySQL instance, setting unique server-ids is critical.

### Step 3. Debezium will transform the binlog event into a standard CDC event and post the event to a kafka topic

There will be one Kafka topic per table. Note that in the example repository, the code from Kafka only subscribes to three topics/tables.

Also note that typically, once a message has been consumed, the consumer informs Kafka not to resend that message to this consumer group ```'enable.auto.commit': 'true'```. Setting this to false can be helpful for quickly debugging your code that processes messages. When you restart your code, you will not have to generate new messages in the pipeline; your code will reread the same messages each time it is restarted.

### Step 4. Python(or other language) application to consume Kafka messages and write them to EventStoreDB

With change events propagated to a Kafka topic per table, the remaining step is to read the Kafka events and write to EventStoreDB.

## Mapping of Database Tables to Kafka topics

A quick review of Debezium behavior as it processes CDC events. 

Debezium will create one kafka topic per table. For each row changed, a message will be created for that topic.

<img src="./resources/Database_table_to_kafka_topic.svg" alt="Database Tables mapped to Kafka Topics" style="width: 80%;"/>

## Mapping Kafka Topics/Messages to EventStoreDB Streams

The next step is to get messages from Kafka topics into EventStoreDB streams.

You could choose several options when you write the CDC messages into EventStoreDB as events.

First, here is a quick review of EventStoreDB functionality.

1. EventStoreDB stores immutable Events into an append-only log
2. When appending an event, we specify the following
    * Stream Name
    * Event Type
    * Event Data
    * Event Metadata
3. Applications can subscribe to a stream or streams

With EventStoreDB's features in mind. Here is a review of some stream design options.

## One stream per topic/table

This configuration would be straightforward, the code may choose to extract a field from the kafka payload and use it to set "Event Type", or the code could more or less ingest the message content as is.

The immutable audit log functionality of EventStoreDB is preserved, the order of events is preserved, and clients can subscribe to changes for a particular table.

<img src="./resources/Kafka-ES-stream-per-topic.svg" style="width: 80%;" alt="image">

## One stream per row

The code example in this repository demonstrates this configuration. The following features of the event are set by parsing either the topic itself or the message's payload.

### 1. Stream Name set to TableName-rowid

As a message is consumed from the per table Kafka topic, it is parsed, and the row identifier for the changed row is extracted and used as the second part of the Stream Name for the event. ```TableA-row1``` for example.

### 2. Event Type set to SQL operation

The message payload is parsed to extract the SQL operation: Delete, Insert(create), Update, Snapshot(initial read), and Event Type is set to that value.

### 3. Correlation ID set to transaction ID

A single transaction may modify more than one row.  If GTID(global transaction IDs) are enabled on the MySQL server, Debezium will pick up that value and include it in the message payload. In the code example, that value is extracted and becomes part of the event Metadata.

### Below is a diagram showing this design

Note that to keep the diagram concise, only one table's row changes are included. Many streams are created per table, and including each would quickly create a crowded image.

Since the relationship between SQL table events to streams diverges in this configuration, it might be helpful to describe an example.

If a row is created and never modified, there will be a stream in EventStoreDB with a single event of Event Type Create.

If a row is created, updated once, and then deleted, there will be a stream in EventStoreDB with three events: one of Event Type Create, one of Event Type Update, and one of Event Type Delete.

<img src="./resources/K-to-ES-stream-per-row.svg" style="width: 80%;" alt="image">

## Leveraging EventStoreDB projection Engine

EventStoreDB's built-in projection engine can be extremely useful for enabling applications, data scientists, or other data users to subscribe to changes across an aggregation of streams. The diagram below shows the functionality.

Events from one stream may be projected into another stream. Here is the documentation, [projections](https://developers.eventstore.com/server/v5/projections.html#system-projections)

Enabling all projections on the EventStoreDB server provides the following functionality.

* Subscribe to changes to all rows in a table
* Subscribe to a stream of all Updates, Inserts, or Deletes across all tables
* View all rows affected by a single transaction

Visualization of EventStoreDB projections as applied to CDC events. 

<img src="./resources/Projections.svg" style="width: 80%;" alt="image">

## Summary

This overview introduces the functionality that EventStoreDB can add to your CDC pipelines.

There is more to this repository if you would like to explore it.

### Shell scripts to build a pipeline

The shell scripts, 01****.sh, 02***.sh, etc are mostly docker commands to build a MySQL->Debezium->kafka->EventStoreDB pipeline. 

### SQL scripts to modify a MySQL database to create events for the pipeline

The sql folder contains these.

### Python code to process the Kafka messages into EventStoreDB events

See the Python folder.

If you have trouble running the Python code locally, see our "Python From Scratch" Repository for advice on setting up your local Event Store Python code environment.

The code in the GitHub repo provides some examples of writing a stream per row and reading from the projections to build a few visualizations. 

------------------------------
