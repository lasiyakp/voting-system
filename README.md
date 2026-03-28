# Web-Based Voting System (Flask + Decision Tree)

A complete beginner-friendly voting system project using:
- **Python + Flask** (backend)
- **HTML/CSS + Bootstrap + Chart.js** (frontend)
- **SQLite** (dummy database)
- **DecisionTreeClassifier** from scikit-learn (dummy ML integration)

---

## Features

- Dummy login (Admin/User roles)
- User dashboard with vote stats and ML prediction
- Voting page (one vote per user)
- Live results page
- Admin dashboard:
  - Add/Delete candidates
  - View users list
  - View all votes
  - Reset voting
- Flash messages for user feedback
- Chart.js graph for candidate-wise votes

---

## Project Structure

```text
voting-system/
│── app.py
│── voting.db                # Auto-created on first run
│── requirements.txt
│── model/
│   └── decision_tree.py
│── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── vote.html
│   ├── results.html
│   └── admin.html
│── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── dashboard.js
└── README.md
```

---

## Database Tables

1. **users** (`id`, `username`, `password`, `role`, `age`, `gender`, `prev_vote`)
2. **candidates** (`id`, `name`, `party`)
3. **votes** (`user_id`, `candidate_id`, `voted_at`)

> `votes.user_id` is unique to prevent duplicate voting.

---

## Dummy Accounts

- **Admin**: `admin / admin123`
- **User**: `alice / user123`
- **User**: `bob / user123`
- **User**: `charlie / user123`

---

## Machine Learning (Decision Tree)

- File: `model/decision_tree.py`
- Uses `DecisionTreeClassifier`
- Dummy input features:
  - Age
  - Gender
  - Previous vote
- Output:
  - Predicted candidate (displayed on user dashboard)

This is for demo/viva purposes only.

---

## How to Run (Step-by-Step)

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment**
   - Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Flask app**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

On first run, `voting.db` is automatically created with sample data.

---

## Viva Note

Decision Tree is used to classify users based on dummy features (age, gender, and previous vote) and predict likely voting behavior.
