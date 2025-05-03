
# Hadoop MapReduce - Character and Word Count Execution Guide

This guide provides the exact commands to run **character count** and **word count** MapReduce jobs using **Hadoop Streaming** with **Python scripts**.

---

## 📦 Prerequisites
- **Hadoop** installed and configured
- **Python 3.x** installed

---

## 1. Setup Environment

### 🔧 Make Python Scripts Executable

Ensure that all the necessary Python scripts (`char_mapper.py`, `char_reducer.py`, `word_mapper.py`, `word_reducer.py`) are executable:

```bash
chmod +x char_mapper.py char_reducer.py word_mapper.py word_reducer.py
```

---

### 🗂️ Create Input Directory in HDFS

Create a directory on HDFS to store your input files:

```bash
hdfs dfs -mkdir -p input
```

---

### 📥 Upload Input File to HDFS

Upload the `input.txt` file to the `input` directory on HDFS:

```bash
hdfs dfs -put -f input.txt input/
```

---

### 🔍 Verify Input File on HDFS

Check if the file was successfully uploaded to HDFS:

```bash
hdfs dfs -ls input/
```

---

## 2. Execute MapReduce Jobs

### ❌ Remove Previous Output (If Exists)

If there is any existing output, remove it:

```bash
hdfs dfs -rm -r -f char_output
hdfs dfs -rm -r -f word_output
```

---

### 3. Run Character Count Job

Execute the **Character Count** MapReduce job using Hadoop Streaming:

```bash
hadoop jar %HADOOP_HOME%\share\hadoop\tools\lib\hadoop-streaming-*.jar ^
  -input input/input.txt ^
  -output char_output ^
  -mapper "python char_mapper.py" ^
  -reducer "python char_reducer.py"
```

---

### 4. View Character Count Results

To view the output of the character count job:

```bash
hdfs dfs -cat char_output/part-00000
```

---

### 5. Run Word Count Job

Execute the **Word Count** MapReduce job using Hadoop Streaming:

```bash
hadoop jar %HADOOP_HOME%\share\hadoop\tools\lib\hadoop-streaming-*.jar ^
  -input input/input.txt ^
  -output word_output ^
  -mapper "python word_mapper.py" ^
  -reducer "python word_reducer.py"
```

---

### 6. View Word Count Results

To view the output of the word count job:

```bash
hdfs dfs -cat word_output/part-00000
```

---

### 7. Copy Output from HDFS to Local File System

After processing, you can copy the results from HDFS to your local machine:

```bash
hdfs dfs -get char_output/part-00000 char_results.txt
hdfs dfs -get word_output/part-00000 word_results.txt
```

---

### 8. View Local Results

Finally, view the results locally:

```bash
cat char_results.txt
cat word_results.txt
```

---

## 📌 Author

Made with 💻 by `@ranjan`  

