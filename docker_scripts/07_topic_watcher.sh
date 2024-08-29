docker run -it --rm --name watcher --link zookeeper:zookeeper --link kafka:kafka quay.io/debezium/kafka:2.7 watch-topic -a -k dbserver1.inventory.customers
