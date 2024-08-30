# Exploring the Code Example

*** WARNING if you encounter issues with rendering the plots, this code runs succesfully in python Python 3.11.9 *** 

The code here expects that you have a running CDC pipeline that feeds Change Events from MySQL, through Debezium and into kafka topics.

Setting up that pipeline is described in the README in the docker_scripts folder. 

That said, the code does show examples of reading from a Kafka topic that could easilly be modified for other use cases where you needed to get kafka data into EventStoreDB.

Also the examples on EventStoreDB system projections and reading from them to do some statistical analysis in Pandas, could also be modified for other use cases.

## Shell scripts to build a pipeline

It is assumed that you have started the docker containers in order, see the docker_scripts folder.

The shell scripts:
* 01_zookeeper.sh
* 02_kafka.sh
* 03_mysql.sh
* 04_mysql_CLI.sh
* 05_kafka_connect.sh
* 06_deploy_connector.sh
* 07_topic_watcher.sh
* 08_start_cluster.sh

## SQL scripts to modify a MySQL database to create events for the pipeline

The MySQL database comes prepopulated with a few rows of data, those rows will be read as "snapshot" events and will appear in the kafka topic per table.

There are sql scripts in the sql directory to add or delete rows to tables in the MySQL database, running in the docker container. Running those scripts will send CDC events through the CDC pipeline and into EventStoreDB.

Much of the code in this directory assumes you will be able to send CDC events through the pipeline to EventStoreDB by running those SQL scripts. 

## Python code to process the kafka messages into EventStoreDB events

The python folder contains examples of python code that reads from kafka and writes to EventStoreDB.

If you have trouble running the python code locally, see our [Python From Scratch](https://github.com/EventStore/EventStoreDB-From-Scratch-Python)Repository for advice on setting up your local Event Store python code environment. 

The code in the github repo provides some examples of both writing a stream per row, and reading from the projections to build a few visualizations.


### python virtualenv (venv) and requirements.txt

Your IDE may prompt you to enable the venv, and automatically run ```pip install -r requirements.txt``` within that venv.

If not, see the python from scratch repository [Python From Scratch](https://github.com/EventStore/EventStoreDB-From-Scratch-Python) and work through that example, perhaps first in github codespaces which we test regularly. And then run that example locally, it has fewer dependencies, a single docker container (this one has many),  and it is completely documented for the beginner. Getting that working, will get you through the learning curve of getting this one setup.

### description of each program in this folder

* kafka_reader_ESDB_writer.py

This is the code that reads from the kafka topic to generate events that are appended to EventStoreDB.

It runs in a continuous loop, but can be stopped with ```ctrl-c``` in the terminal

* kafka_consumer_demo.py

This is a simple demo of creating a kafka consumer in python that reads from one or more topics.

This is configured to NOT delete messages after consuming them, so it can be ran multiple times and will display the same messages to the terminal. It can be used to test that the CDC events are making it to Kafka. It could also be modified for any use case where you need to read from Kafka using python.

* read_all_events_per_table.py

Instead of writing the CDC pipeline's kafka topic to a single stream, the code in this example parses the Kafka message, extracts the rowid, and appends that event to a stream per row.

This code reads from EventStoreDB's built in ```By_Category``` projection which enables a reader to read, or subscribe to all changes for a table.

* read_all_events_for_a_single_transaction.py

This code leverages another of EventStoreDB's built in projections, the ```correlationID``` projection.

Our Event Writer code extracts the GTID (global transaction ID) from the Kafka payload, and writes that into the Events metadata as ```correlationID``` 

* analysis_by_sql_operation.py

This code reads from another one of EventStoreDB's projections, the ```EventType``` projection.

Events are read, and placed into a Pandas Dataframe for some simple analysis. 

This shows how having EventStoreDB in your CDC pipeline your CDC events are organized in a way that is well suited to Statistical Analysis and Machine Learning.

The analysis.... examples generate images of pie charts, bar graphs and histograms. Examples of those are stored in the examples_of_analysis_plots directory. View those if you are not interested in setting up the whole docker pipeline.

This code is more interesting after running the many_changes.sql script.

* analysis_of_rows_per_transaction.py

This example reads all changes from the customers table, and gathers correlationID (transaction ID's) into a Pandas dataframe. From the Pandas Dataframe it generates statistics on median, max, min number of rows per transaction.

This type of analysis could be useful to see if developers that are interacting with the Database are efficiently using transactions in their code. 

If you do not wish to run the code, examples of the output are available in the examples_of_analysis_plots folder.

This code is more interesting after running the many_changes.sql script.

## Running the demo

After starting all of the docker containers in order, you should have a working Debezium CDC pipeline.

If you run the python program 'kafka_reader_ESDB_writer.py' it will capture the initial snapshot events and write them to streams. The program will run in a continuous loop, you will have to hit ctrl-c to stop it.

After running it, you can look at MySQL and the EventStore Stream browser to see that the row data from MySQL has replicated over to Event data in  EventStoreDB.


For reference here is a view of MySQL

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

Note that although Debezium is capturing all 6 tables, our consumer code is only consuming 3 of those tables

```
c.subscribe(['dbserver1.inventory.customers','dbserver1.inventory.products','dbserver1.inventory.products_on_hand'])
```

On startup debezium captures a snapshot of existing rows, our first read of the consumer will get events that we will label as "snapshot" events for each row of the tables, customers, inventory, products_on_hand.

Viewing the stream browser http://localhost:2113/ shows those rows, are now read into individual streams as events of type "Snapshot"
<br />
<br />
<img src="./../resources/First_Snapshot_Stream_Status_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

<br />
<br />

## Using EventStoreDB's  built in projection system

If the projection subsystem is enabled, and projections are running, then you can view the projection streams. The shell script that starts the EventStoreDB docker container configures this. If you are using another method to start EventStoreDB, you may need to enable them. 

In this case changes to row 1 of the customers table will be written to stream customers-row1.

The category projection will split the stream-name on the ```-``` character and put all events to all streams that start with ```customers``` into the ```$category-customers``` stream. There is python code to read from that projection, see ```read_all_events_per_table.py``` in the python directory. 

<img src="./../resources/Projections_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

<br />
<br />

## Processing of Inserts

After the initial snapshot is taken, Data Change events resulting from inserts, updates or deletes will be appended to the stream for that row.

In the sql folder there is a script ```add_customers.sql``` that will add 5 records to the customers table in a single transaction.

Note that the table has a unique constraint on email, so a second execution of this script will not add new rows.

If you run that script, ```sh sql/add_customers.sql ``` you will see the following streams are created.

This assumes ```kafka_reader_ESDB_writer.py``` is running, if you stopped it, restart it and it will pick up the new events from kafka.

After running the SQL script, rhe EventStoreDB stream browser should show 5 new streams, one per each row inserted into the customers table.

<img src="./../resources/Rows_added_in_transaction_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

## Event Type projection

Adding 5 rows in an insert operation, means that 5 events were written to EventStoreDB with an EventType of "Insert".

The Event Type projection for "Insert" will contain those rows.

You can view that in the stream browser, http://localhost:2113/web/index.html#/streams/$et-Insert 

If you wanted to read or subscribe to that projection you could use the ```read_all_events_per_table.py``` code as an example, or the analysis_by_sql_operation.py as an example.

### Event Type Projections for this CDC example

Our code creates an Events with a type of one of the following.

* Snapshot
* Insert
* Update
* Delete

There will be streams/projections created when the first event of that type is written, and those projections will be appended to as subsequent events of that Event Type are appended.

The projection feature adds great flexibility to your CDC pipelines. Applications can subscribe to or read completely the projections based on Event Type. Enabling an analysis or processing of, inserts, updates, snapshots, and deletes in isolation or in aggregate.

<img src="./../resources/Event_Type_projection_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>
<br />
<br />

Here is a view of the insert projection at this point. 

Note that over time it would include inserts all tables, at this point no other tables have had insert operations.

<img src="./../resources/View_of_insert_projection.png" alt="my caption" style="width: 500px; border: 2px solid black;" />


### Correlation ID projection

The ```add_customers.sql``` wrote 5 rows in a single transaction. MySQL stored the transaction ID in it's binlog as GTID(Global Transaction ID), debezium recorded that as part of the payload for each row change triggered by that transaction.

The python code reads that field and writes it into the event metadata.

There is a projection available based on events with matching ```correlationID's```

If you look at an event's metadata you can see the ```correlationId``` you can use this to view all rows changed for that transaction. Note that ```snapshot``` events do not have a correlation ID, so look at the insert events generated by the multi-row insert ```add_customers.sql```

The following images demonstrate the functionality.

<img src="./../resources/Correlation_ID_in_metadata.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

Here is the projection for all changes caused by the transaction. 

<img src="./../resources/Transaction_projection_annotated.png" alt="my caption" style="width: 500px; border: 2px solid black;"/>

### Performing a large number of table changes

There is a sql script, ```many_changes.sql``` that will make many changes to the customers table.

Run that script to generate enough data to do something interesting with the data in EventStoreDB. 

``` sh many_changes.sgl```

Note if you have stopped the kafka_reader_ESDB_writer.py program, you can restart it, unread messages will persist in kafka long enough for the consumer to pick them up.

### Python Examples that calculate statistics across CDC events

After running ```many_changes.sql``` There should be hundreds of events in EventStoreDB. You can run the script multiple times, the first command deletes most of the rows, the rest of the command re-insert rows, some failures due to table constraints are expected.

#### Analysis by SQL operation

Events have an Event Type of Insert, Update, Delete, and Snapshot. This example  ```analysis_by_sql_operation.py``` creates a pandas dataframe by reading each of the EventType projections and pushing data into a Pandas Dataframe for analysis.

#### Analysis of Number of Rows changed per transaction

The ```analysis_of_rows_per_transaction.py``` reads all events for the customers table, and puts $correlationID into a pandas dataframe. The number of times a $correlationID appears in that dataframe is equal to the number of rows that transaction modified. This code analysis that and generates a few plots. 






