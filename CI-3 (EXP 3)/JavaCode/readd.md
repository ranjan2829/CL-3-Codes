You're getting the following error:

```
Input path does not exist: file:/user/input
```

This tells us Hadoop is trying to find the **input directory in your local file system**, not in HDFS (Hadoop Distributed File System). You likely **don't have HDFS set up**, or it's **not running**, so it's defaulting to the local file system.

---

### ✅ Let's fix this step-by-step:

#### 🔹 Step 1: Check whether Hadoop is in **Local (pseudo-distributed)** or **Standalone mode**

Run this:

```bash
hadoop version
```

If you're using Hadoop on your Mac **without HDFS (Standalone mode)**, then Hadoop expects local file paths — **not `/user/input`**, but something like:

```bash
hadoop jar WordCharCount.jar WordCharCount input/ output/
```

---

### ✅ Solution 1: Run in Standalone Mode (Local FS)

1. **Create local `input` directory and add `sample.txt`:**

```bash
mkdir -p input
cp sample.txt input/
```

2. **Run the job using local paths:**

```bash
hadoop jar WordCharCount.jar WordCharCount input output
```

3. **Check output:**

```bash
cat output/part-r-00000
```

---

### ✅ Solution 2: If you want to use HDFS (Pseudo-distributed mode)

1. **Start Hadoop (if not already):**

```bash
start-dfs.sh
```

2. **Format HDFS (only once):**

```bash
hdfs namenode -format
```

3. **Create HDFS input directory and put file:**

```bash
hadoop fs -mkdir -p /user/input
hadoop fs -put sample.txt /user/input/
```

4. **Run the job:**

```bash
hadoop jar WordCharCount.jar WordCharCount /user/input /user/output
```

5. **View result from HDFS:**

```bash
hadoop fs -cat /user/output/part-r-00000
```

---

### 🔍 Summary

| Mode       | Command to Use                                                        |
| ---------- | --------------------------------------------------------------------- |
| Local Mode | `hadoop jar WordCharCount.jar WordCharCount input/ output/`           |
| HDFS Mode  | `hadoop jar WordCharCount.jar WordCharCount /user/input /user/output` |

Let me know if you want a shell script to automate all steps or if you're unsure whether HDFS is running.
