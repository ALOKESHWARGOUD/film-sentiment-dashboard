import streamlit as st
import sqlite3
import pandas as pd
import datetime

# -----------------------------
# DB CONNECTION
# -----------------------------

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# ENSURE TABLES EXIST (NO ERROR)
# -----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS comments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
video_id TEXT,
comment_text TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS labels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
comment_id INTEGER,
employee_name TEXT,
label TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS employee_video(
employee_name TEXT PRIMARY KEY,
video_id TEXT
)
""")

conn.commit()

# -----------------------------
# UI
# -----------------------------

st.title("📊 Admin Analytics Dashboard")

password = st.text_input("Admin Password", type="password")

if password != "admin123":
    st.warning("Enter correct password")
    st.stop()

# -----------------------------
# REFRESH BUTTON
# -----------------------------

if st.button("🔄 Refresh Dashboard"):
    st.rerun()

# -----------------------------
# TOTAL LABELS
# -----------------------------

try:
    total = pd.read_sql("SELECT COUNT(*) as total FROM labels", conn)
    st.metric("Total Labeled Comments", total.iloc[0]["total"])
except:
    st.warning("No data available")

# -----------------------------
# EMPLOYEE PERFORMANCE
# -----------------------------

st.subheader("👨‍💻 Employee Performance")

try:
    employee_report = pd.read_sql("""

    SELECT 
    employee_name,
    COUNT(*) as total_labels,
    SUM(label='positive') as positive,
    SUM(label='neutral') as neutral,
    SUM(label='negative') as negative

    FROM labels
    GROUP BY employee_name

    """, conn)

    st.dataframe(employee_report)

except:
    st.warning("No employee data yet")

# -----------------------------
# CURRENT VIDEO TRACKING
# -----------------------------

st.subheader("🎬 Current Video per Employee")

try:
    video_report = pd.read_sql("""

    SELECT employee_name, video_id
    FROM employee_video

    """, conn)

    st.dataframe(video_report)

except:
    st.warning("No video assignments yet")

# -----------------------------
# VIDEO STATS
# -----------------------------

st.subheader("📺 Video-wise Dataset")

try:
    video_stats = pd.read_sql("""

    SELECT video_id, COUNT(*) as total_comments
    FROM comments
    GROUP BY video_id

    """, conn)

    st.dataframe(video_stats)

except:
    st.warning("No video data yet")

# -----------------------------
# SENTIMENT DISTRIBUTION
# -----------------------------

st.subheader("📊 Sentiment Distribution")

try:
    dist = pd.read_sql("""

    SELECT label, COUNT(*) as count
    FROM labels
    GROUP BY label

    """, conn)

    st.bar_chart(dist.set_index("label"))

except:
    st.warning("No sentiment data yet")

# -----------------------------
# DOWNLOAD SIMPLE REPORT
# -----------------------------

st.subheader("⬇️ Download Reports")

try:
    csv_report = employee_report.to_csv(index=False)

    st.download_button(
        "Download Employee Report",
        csv_report,
        "employee_report.csv",
        "text/csv"
    )

except:
    pass

# -----------------------------
# DOWNLOAD FULL DATASET
# -----------------------------

try:
    dataset = pd.read_sql("""

    SELECT 
    comments.comment_text,
    labels.label,
    labels.employee_name,
    comments.video_id

    FROM labels
    JOIN comments
    ON comments.id = labels.comment_id

    """, conn)

    csv_dataset = dataset.to_csv(index=False)

    st.download_button(
        "Download Full Dataset",
        csv_dataset,
        "sentiment_dataset.csv",
        "text/csv"
    )

except:
    pass

# -----------------------------
# ADVANCED STRUCTURED REPORT
# -----------------------------

st.subheader("📄 Generate Full Structured Report")

if st.button("Generate Report"):

    report_data = []

    # ---------------- MODEL INFO ----------------

    report_data.append(["Model Info", "Model Version", "v1"])
    report_data.append(["Model Info", "Generated On", str(datetime.date.today())])

    try:
        total_labels = pd.read_sql(
            "SELECT COUNT(*) as total FROM labels",
            conn
        ).iloc[0]["total"]
    except:
        total_labels = 0

    report_data.append(["Model Info", "Dataset Size", total_labels])

    # ---------------- PERFORMANCE ----------------

    report_data.append(["Performance", "Accuracy", "Dynamic"])
    report_data.append(["Performance", "Precision", "Dynamic"])
    report_data.append(["Performance", "Recall", "Dynamic"])

    # ---------------- DATASET ----------------

    report_data.append(["Dataset", "Total Labels", total_labels])

    try:
        dist = pd.read_sql("""
        SELECT label, COUNT(*) as count
        FROM labels
        GROUP BY label
        """, conn)

        for _, row in dist.iterrows():
            report_data.append(["Dataset", f"{row['label']} count", row["count"]])
    except:
        pass

    # ---------------- EMPLOYEE STATS ----------------

    try:
        emp = pd.read_sql("""
        SELECT employee_name, COUNT(*) as total
        FROM labels
        GROUP BY employee_name
        """, conn)

        for _, row in emp.iterrows():
            report_data.append(["Employee", f"{row['employee_name']} labels", row["total"]])
    except:
        pass

    # ---------------- CREATE DATAFRAME ----------------

    report_df = pd.DataFrame(report_data, columns=["Section", "Metric", "Value"])

    st.dataframe(report_df)

    # ---------------- DOWNLOAD REPORT ----------------

    csv = report_df.to_csv(index=False)

    st.download_button(
        "Download Full Structured Report",
        csv,
        "film_sentiment_report.csv",
        "text/csv"
    )