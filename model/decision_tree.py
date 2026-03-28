"""Dummy Decision Tree model for voting prediction."""

import pandas as pd
from sklearn.tree import DecisionTreeClassifier


# ---------------------------
# Build dummy training dataset
# ---------------------------
def _train_model():
    # Dummy data for viva/demo purposes
    data = pd.DataFrame(
        [
            # age, gender, prev_vote, predicted_candidate
            (18, "F", "A", "Candidate B"),
            (20, "F", "B", "Candidate B"),
            (22, "M", "A", "Candidate A"),
            (25, "M", "A", "Candidate A"),
            (26, "F", "C", "Candidate C"),
            (28, "M", "B", "Candidate B"),
            (30, "M", "C", "Candidate C"),
            (32, "F", "A", "Candidate A"),
            (35, "M", "A", "Candidate A"),
            (38, "F", "B", "Candidate B"),
            (40, "M", "C", "Candidate C"),
            (45, "F", "A", "Candidate A"),
        ],
        columns=["age", "gender", "prev_vote", "label"],
    )

    # Convert categorical columns to numeric for scikit-learn
    encoded = pd.get_dummies(data[["age", "gender", "prev_vote"]], columns=["gender", "prev_vote"])
    X = encoded
    y = data["label"]

    clf = DecisionTreeClassifier(max_depth=4, random_state=42)
    clf.fit(X, y)

    return clf, X.columns


MODEL, FEATURE_COLUMNS = _train_model()


# ---------------------------
# Prediction function
# ---------------------------
def predict_candidate(age, gender, prev_vote):
    """Return predicted candidate using the trained decision tree."""
    input_df = pd.DataFrame(
        [{"age": age, "gender": gender, "prev_vote": prev_vote}]
    )
    input_encoded = pd.get_dummies(input_df, columns=["gender", "prev_vote"])

    # Align user input columns with model training columns
    aligned = input_encoded.reindex(columns=FEATURE_COLUMNS, fill_value=0)

    prediction = MODEL.predict(aligned)[0]
    return prediction
