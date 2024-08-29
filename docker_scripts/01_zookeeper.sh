docker run -e JVMFLAGS="-Dzookeeper.4lw.commands.whitelist=*" -it --rm --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 quay.io/debezium/zookeeper:2.7
