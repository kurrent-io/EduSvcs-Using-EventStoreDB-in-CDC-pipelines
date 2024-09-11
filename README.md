# Using EventStoreDB in CDC(Change Data Capture) pipelines

## Introduction

### Overview

Moving data from operational data stores into data warehouses, data lakes, or lakehouses is a common requirement for businesses.

A popular tool for implementing a CDC pipeline is Debezium.

Debezium translates CDC events from various sources into a common format, allowing them to be ingested by various sinks, including data lakes, lakehouses, NoSQL stores, and more.

### Benefits of EventStoreDB

For the following reasons, Using EventStoreDB as a sink can be a beneficial hub in a data redistribution workflow.

1. EventStoreDB provides an immutable log of CDC events
2. Users can subscribe to EventStoreDB fine-grained event streams
3. EventStoreDB's projection engine allows subscription to a granular subset of events or a more extensive aggregation of events

Leveraging the ability to subscribe to CDC events **after** they land in EventStoreDB, with granular control over which subset of events to subscribe to, allows EventStoreDB to function more like a hub than just another sink.

In addition, the events' order and durability provide options to reprocess or audit and analyze them as needed.


## Content structure 

This content consists of two parts:

1. This document serves as an overview of the features and benefits EventStoreDB brings to bear in the CDC process
2. code_example.md provides an overview of the code in this GitHub repo

## Architecture of typical Debezium-based CDC pipeline

### At a high level, the basic architecture involves these tools

<img src="./resources/excalidraw-animate_slow.svg" alt="Image of Database to Debezium to EventStoreDB Data Flow" style="width: 80%;"/>

### A more granular view of the tools, showing required supporting features and products

<img src="./resources/Data_flow_with_supporting_features.svg" alt="CDC pipeline with all the tools " style="width: 80%;"/>


## Lifecycle of a CDC event (MySQL -> EventStoreDB)

Whenever data is modified in the source database by a create (insert), delete, or update statement, one or more CDC events will propagate through the pipeline in the following manner. This example will use a single-row insert. 

### Step 1. The database server, MySQL or MariaDB, writes the event to its binlog

The binlog is used for database replication.  All changes to the database are logged to the binlog if enabled. The binlog is usually enabled by default. Note that to get transaction IDs logged into the binlog, the setting gtid_mode=ON must be set. The code example starts a Docker container running MySQL, and that setting is enabled in the startup script. See ```03_mysql.sh``` in this repo.

### Step 2. Debezium picks up the data change event from the binlog

Debezium impersonates the role of another MySQL instance that acts as a replica to be used as a backup or for scaling reads. Setting unique server-ids is critical when fanning out multiple replicas with multiple Debezium instances reading the binlog of a single MySQL instance.

### Step 3. Debezium transforms the binlog event into a standard CDC event and posts the event to a Kafka topic

There is one Kafka topic per table. Note that in the example repository, the code from Kafka only subscribes to three topics/tables.

Also note that typically, once a message has been consumed, the consumer informs Kafka not to resend that message to this consumer group ```'enable.auto.commit': 'true'```. Setting this to false can be helpful for quickly debugging code that processes messages. When restarting the code, you will not have to generate new messages in the pipeline; the code will reread the same messages each time it is restarted.

### Step 4. Python(or other language) application consumes Kafka messages and writes them to EventStoreDB

With change events propagated to a Kafka topic per table, the remaining step is to read the Kafka events and write to EventStoreDB.


## Mapping of database tables to Kafka topics

A quick review of Debezium behavior as it processes CDC events. 

Debezium will create one kafka topic per table. For each row changed, a message will be created for that topic.

<img src="./resources/Database_table_to_kafka_topic.svg" alt="Database Tables mapped to Kafka Topics" style="width: 80%;"/>


## Mapping Kafka topics/messages to EventStoreDB streams

The next step is to get messages from Kafka topics into EventStoreDB streams.

Several options are available to write the CDC messages into EventStoreDB as events.

First, here is a quick review of EventStoreDB functionality.

1. EventStoreDB stores immutable events into an append-only log
2. When appending an event, the following is specified:
    * Stream Name
    * Event Type
    * Event Data
    * Event Metadata
3. Applications can subscribe to a stream or streams

With EventStoreDB's features in mind. Here is a review of some stream design options.


## One stream per topic/table

This configuration is straightforward.  The code may choose to extract a field from the Kafka payload and use it to set "Event Type," or the code could ingest the message content as is.

The immutable audit log functionality of EventStoreDB and the order of events are preserved, and clients can subscribe to changes for a particular table.

<img src="./resources/Kafka-ES-stream-per-topic.svg" style="width: 80%;" alt="image">


## One stream per row

The code example in this repository demonstrates this configuration. The following event features are set by parsing either the topic itself or the message's payload.

### 1. Stream Name is set to TableName-rowid

As a message is consumed from the per table Kafka topic, it is parsed, and the row identifier for the changed row is extracted and used as the second part of the stream name for the event. ```TableA-row1``` for example.

### 2. Event Type is set to SQL operation

The message payload is parsed to extract the SQL operation: Delete, Insert(create), Update, Snapshot(initial read), and Event Type is set to that value.

### 3. Correlation ID is set to transaction ID

A single transaction may modify more than one row.  If GTID(global transaction IDs) are enabled on the MySQL server, Debezium picks up that value and includes it in the message payload. In the code example, that value is extracted and becomes part of the event metadata.

### The diagram illustrates this design

Note that only one table's row changes are included to keep the diagram concise. Many streams are created per table, and including each would quickly make a crowded image.

Since the relationship between SQL table events and streams diverges in this configuration, it might be helpful to describe an example.

If a row is created and never modified, a stream in EventStoreDB will contain a single event with the Event Type "Create." 

If a row is created, updated once, and then deleted, there will be a stream in EventStoreDB with three events with the Event Types "Create," "Update," and "Delete," respectively.

<img src="./resources/K-to-ES-stream-per-row.svg" style="width: 80%;" alt="image">


## Leveraging EventStoreDB projection engine

EventStoreDB's built-in projection engine can be extremely useful for enabling applications, data scientists, or other data users to subscribe to changes across an aggregation of streams. The diagram below shows the functionality.

Events from one stream are projected into another stream based on specific criteria. To learn more about Projections, please visit the Event Store documentation, [projections](https://developers.eventstore.com/server/v5/projections.html#system-projections)

Enabling all projections on the EventStoreDB server provides the following functionality.

* Subscribe to changes to all rows in a table
* Subscribe to a stream of all Updates, Inserts, or Deletes across all tables
* View all rows affected by a single transaction

Visualization of EventStoreDB projections as applied to CDC events. 

<img src="./resources/Projections.svg" style="width: 80%;" alt="image">


## Summary

This overview introduced some functionality that EventStoreDB can add to CDC pipelines.

There is more to this repository if you would like to explore it.

### Shell scripts to build a pipeline

The shell scripts, 01****.sh, 02***.sh, etc., are mostly Docker commands for building a MySQL -> Debezium -> Kafka -> EventStoreDB pipeline. 

### SQL scripts to modify a MySQL database to create events for the pipeline

These can be found in the sql folder.

### Python code to process the Kafka messages into EventStoreDB events

This is contained in the python folder.

If you have trouble running the Python code locally, see our "Python From Scratch" Repository for advice on setting up your local Event Store Python code environment.

The code in the GitHub repo provides some examples of writing a stream per row and reading from the projections to build a few visualizations. 

------------------------------
