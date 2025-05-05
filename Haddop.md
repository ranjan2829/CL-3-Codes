# Java

### Ohh boy youre fucked. Let's start

1. Open Terminal.

2. Run: `java -version`

If not downloaded download from: https://www.oracle.com/java/technologies/downloads/#jdk24-windows (remember over 3 billion devices run java)

run: `java -version` to verify. If not working re-install. If still not; raise hand andcall maam

3. Download hadoop from: https://dlcdn.apache.org/hadoop/common/hadoop-3.4.1/hadoop-3.4.1.tar.gz
   (clicking this link auto starts the download)

4. Extract the file in the C drive

5. Once ectracted, go to C folder. Then Hadoop-3.4.1. The etc folder. Then Hadoop folder

6. now open the `core-site.xml` file in vs code

Between `configuration` and `/configuration` paste this:

```xml
<configuration>
<property>
<name>fs.defaulterFS</name>
<value>hdfs://localhost:9000</value>
</property>
</configuration>
```

Save it and close.

Now open `mapred-site.xml` in vs code

same paste this:

```xml
<configuration>
<property>
<name>mapreduce.job.tracker</name>
<value>localhost:9870</value>
</property>
</configuration>
```

Great now last, open `hdfs-site.xml`
same between `configuration` paste this:

```xml
<configuration>
<property>
<name>dfs.replication</name>
<value>1</value>
</property>
</configuration>
```

Now open `hadoop-env.cmd` (please mind the extension, we are opening in windows so it needs to be the windows one as there is also an .sh one)

Now in C drive, open program files folder, inside it Java, inside it jdk-24 (if not there you will manually have to check where java is installed so try in program files or program files(x86))

Now copy the path of jdk-24 folder and in the `hadoop-env.cmd` folder, change the command on line 25 to `set JAVA_HOME= "C:\Program Files\Java\jdk-24"` (where post "=" it will be the location of java and mind "/" you have to use / not \)

save and close it

# Python

### Python wala karle bhai --

```

Title: Design and develop a distributed application to find the coolest/hottest year from the available
weather data. Use weather data from the Internet and process it using MapReduce.
Problem Statement: Develop a distributed application using MapReduce to analyze weather data
from the Internet and determine the coolest or hottest year based on temperature readings.
Prerequisite:
Basics of Python <===========================
Software Requirements: Jupyter
Hardware Requirements:
PIV, 2GB RAM, 500 GB HDD

```
https://github.com/1447bits/CL-3
```

pip install mrjob

```

```

python main.py

```

> make sure there is londonweather.csv

agar nahi hai to : https://raw.githubusercontent.com/alanjones2/dataviz/master/londonweather.csv

```

```

```

```