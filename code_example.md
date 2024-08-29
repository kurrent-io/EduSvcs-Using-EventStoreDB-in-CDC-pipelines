# Exploring the Code Example

The Readme.md file provides a written overview, and introduction of the functionality that EventStoreDB can add to your CDC pipelines

This document provides an overview of building and running a pipeline using docker containers.

The needed code and scripts are included in this repo.

## Shell scripts to build a pipeline

The shell scripts:
* 01_zookeeper.sh
* 02_kafka.sh
* 03_mysql.sh
* 04_mysql_CLI.sh
* 05_kafka_connect.sh
* 06_deploy_connector.sh
* 07_topic_watcher.sh
* 08_start_cluster.sh

Are meant to be ran in order, and will create instances of Zookeeper, Kafka, MySQL, kafka connect, and EventStoreDB. 

Although this repo is not intended to be a tutorial on each of these tools, the content does describe in general terms the functionality of each.

## SQL scripts to modify a MySQL database to create events for the pipeline

The MySQL database comes prepopulated with a few rows of data, those rows will be read as "snapshot" events and will appear in the kafka topic per table.

There are sql scripts in the sql directory to add or delete rows to tables in the MySQL database, running in the docker container. Running those scripts will send CDC events through the CDC pipeline and into EventStoreDB.

## Python code to process the kafka messages into EventStoreDB events

The python folder contains examples of python code that reads from kafka and writes to EventStoreDB.

If you have trouble running the python code locally, see our [Python From Scratch](https://github.com/EventStore/EventStoreDB-From-Scratch-Python)Repository for advice on setting up your local Event Store python code environment. 

The code in the github repo provides some examples of both writing a stream per row, and reading from the projections to build a few visualizations.

## Running the demo

After starting all of the docker containers in order, you should have a working Debezium CDC pipeline.

If you run the python program 'k_to_es_stream_per_row.py' it will capture the initial snapshot events and write them to streams. The program will run in a continuous loop, you will have to hit ctrl-c to stop it.

After running it, you can look at MySQL and the EventStore Stream browser to see that the data has replicted over.


Here is a view of MySQL

```
mysql> show tables;
+---------------------+
| Tables_in_inventory |
+---------------------+
| addresses           |
| customers           |
| geom                |
| orders              |
| products            |
| products_on_hand    |
+---------------------+
6 rows in set (0.04 sec)
```

Note that our consumer code is only consuming 3 of those tables

```
c.subscribe(['dbserver1.inventory.customers','dbserver1.inventory.products','dbserver1.inventory.products_on_hand'])
```

This means that the first read of the consumer will get events for each row of the tables, customers, inventory, products_on_hand.

Viewing the stream browser shows those rows, are now read into individual streams as events of type "snapshot"
<br />
<br />
<img src="./resources/First_Snapshot_Stream_Status_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

<br />
<br />

## Using the built in projection system

If the projection subsystem is enabled, and projections are running, then you can view the projection streams. In this case changes to row 1 of the customers table will be written to stream customers-row1.  The category projection will split the stream-name on the ```-``` character and put all events to all streams that start with ```customers``` into the ```$category-customers``` stream. There is python code to read from that projection, see ```read_all_events_per_table.py``` in the python directory. 

<img src="./resources/Projections_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

<br />
<br />

## Processing of Inserts

After the initial snapshot is taken, Data Change events resulting from inserts, updates or deletes will be appended to the stream for that row.

In the sql folder there is a script ```add_customers.sql``` that will add 5 records to the customers table in a single transaction.

Note that the table has a unique constraint on email, so a second execution of this script will not add new rows.

If you run that script, ```sh sql/add_customers.sql ``` you will see the following streams are created.

This assumes k_to_es_stream_per_row.py is running, if you stopped it, restart it and it will pick up the new events from kafka.

The EventStoreDB stream browser will show 5 new streams, one per each row inserted into the customers table.

<img src="./resources/Rows_added_in_transaction_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

## Event Type projection

Adding 5 rows in an insert operation, means that 5 events were written to EventStoreDB with an EventType of "insert" 

The Event Type projection for insert will contain those rows. 

You can view that in the stream browser, or write some code to read that stream/projection. Note you would want to use the ```read_all_events_per_table.py``` code as an example, just change the stream name.

### Event Type Projections for this CDC example

Our code creates an Events with a type of one of the following.

* snapshot
* insert
* update
* delete

This means that there will be streams/projections created when the first event of that type is written, and those projections will be appended to as subsequent events of the Event Type are writte.

This adds great flexibility to your CDC pipelines by subscribing to or reading the projections based on Event Type, you can view all, inserts, updates, snapshots, and deletes in isolation.

<img src="./resources/Event_Type_projection_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>
<br />
<br />

Here is a view of the insert projection at this point. 

Note that over time it would include inserts all tables, at this point no other tables have had insert operations.

<img src="./resources/View_of_insert_projection.png" alt="my caption" style="width: 500px; border: 2px solid black;" />


### Correlation ID projection

The SQL script wrote 5 rows in a single transaction. MySQL stored that in it's binlog as GTID(Global Transaction ID), debezium recorded that as part of the payload for each row change triggered by that transaction. 

The python code read that field and wrote it into the event metadata.

There is a projection available based on events with matching ```correlationID's```

If you look at an event's metadata you can see the ```correlation ID``` you can use this to view all rows changed for that transaction. Note that ```snapshot``` events do not have a correlation ID, so look at the insert events generated by the multi-row insert ```add_customers.sql```

The following images demonstrate the functionality.

<img src="./resources/Correlation_ID_in_metadata.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

Here is the projection for all changes caused by the transaction. 

<img src="./resources/Transaction_projection_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

