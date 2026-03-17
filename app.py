import streamlit as st
import sqlite3
from sklearn.linear_model import SGDClassifier
import numpy as np

# -----------------------------
# DATABASE
# -----------------------------

def get_db():
    conn = sqlite3.connect('comments.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_next_comment(conn):
    return conn.execute("""
        SELECT c.id, c.comment_text
        FROM comments c
        LEFT JOIN labels l ON c.id = l.comment_id
        WHERE l.comment_id IS NULL
        ORDER BY c.id ASC
        LIMIT 1
    """).fetchone()

def save_label(conn, comment_id, label):
    conn.execute(
        "INSERT INTO labels (comment_id, label) VALUES (?, ?)",
        (comment_id, label)
    )
    conn.commit()

# -----------------------------
# MODEL (AUTO LEARNING)
# -----------------------------

def init_model():
    if "model" not in st.session_state:
        st.session_state.model = SGDClassifier(loss="log_loss")
        st.session_state.training_buffer = []
        st.session_state.model_initialized = False

def update_model(comment_text, label):

    # Simple feature (replace later with vectorizer if needed)
    X = np.array([[hash(comment_text) % 10000]])
    y = np.array([label])

    st.session_state.training_buffer.append((X, y))

    if len(st.session_state.training_buffer) >= 10:

        X_batch = np.vstack([x for x, _ in st.session_state.training_buffer])
        y_batch = np.array([y for _, y in st.session_state.training_buffer])

        model = st.session_state.model

        if not st.session_state.model_initialized:
            model.partial_fit(X_batch, y_batch, classes=np.array([0, 1, 2]))
            st.session_state.model_initialized = True
        else:
            model.partial_fit(X_batch, y_batch)

        st.session_state.training_buffer.clear()
        st.success("✅ Model updated with batch")

# -----------------------------
# STREAMLIT UI
# -----------------------------

st.title("🎬 Employee Comment Labeling Dashboard")

conn = get_db()
init_model()

# -----------------------------
# SESSION STATE (CRITICAL FIX)
# -----------------------------

if "current_comment" not in st.session_state:
    st.session_state.current_comment = fetch_next_comment(conn)

comment_row = st.session_state.current_comment

# -----------------------------
# DISPLAY LOGIC
# -----------------------------

if comment_row is None:
    st.success("🎉 All comments labeled!")

else:
    comment_id = comment_row["id"]
    comment_text = comment_row["comment_text"]

    st.subheader("Comment")
    st.info(comment_text)

    # -----------------------------
    # MODEL PREDICTION (OPTIONAL)
    # -----------------------------

    try:
        X = np.array([[hash(comment_text) % 10000]])
        model = st.session_state.model

        if st.session_state.model_initialized:
            pred = model.predict(X)[0]
            probs = model.predict_proba(X)
            conf = probs.max()

            labels_map = {0: "Positive", 1: "Neutral", 2: "Negative"}

            st.write(f"🤖 Model: {labels_map[pred]} ({round(conf*100,1)}%)")
        else:
            st.write("🤖 Model: Not trained yet")

    except:
        st.write("Model error")

    # -----------------------------
    # LABEL HANDLER (KEY FIX)
    # -----------------------------

    def handle_label(label):

        # Prevent duplicate insert
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM labels WHERE comment_id=?",
            (comment_id,)
        )

        if cursor.fetchone() is None:
            save_label(conn, comment_id, label)
            update_model(comment_text, label)

        # 🔥 IMPORTANT: move to next comment explicitly
        st.session_state.current_comment = fetch_next_comment(conn)

        st.rerun()

    # -----------------------------
    # BUTTONS
    # -----------------------------

    col1, col2, col3 = st.columns(3)

    if col1.button("Positive ✅", key=f"pos_{comment_id}", use_container_width=True):
        handle_label(0)

    if col2.button("Neutral ⚪", key=f"neu_{comment_id}", use_container_width=True):
        handle_label(1)

    if col3.button("Negative ❌", key=f"neg_{comment_id}", use_container_width=True):
        handle_label(2)

# -----------------------------
# OPTIONAL: RESET BUTTON
# -----------------------------

if st.button("🔄 Reset Labels"):
    conn.execute("DELETE FROM labels")
    conn.commit()
    st.session_state.current_comment = fetch_next_comment(conn)
    st.success("Reset done")
    st.rerun()