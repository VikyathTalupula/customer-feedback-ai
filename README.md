# Customer Feedback Analysis & Automated Response

## Overview
A retail company receives thousands of customer reviews every week, and its support team reads them by hand to find the
urgent, negative ones. This project automates that work:

1. Clean the review data with Python and Pandas.
2. Build new features from the data (feature engineering).
3. Pick out the **Critical** reviews with simple rules and find the most common complaint keywords.
4. Use Generative AI (Google Gemini) to draft short, empathetic apology emails for the 3 most critical, detailed reviews.

Only Python, Pandas and plotting libraries are used. **No machine-learning code** (no sklearn, no trained models) is used.

## Files
| File | Description |
|---|---|
| `Customer_Feedback_Analysis_T_S_S_V_VIKYATH.ipynb` | The Jupyter / Google Colab notebook with all the code |
| `README.md` | This file |
| `generated_emails.md` | Created automatically when the notebook runs: the 3 AI-generated emails |

## Dataset
Kaggle: **Women's E-Commerce Clothing Reviews** (`Womens Clothing E-Commerce Reviews.csv`).
It has about 23,486 reviews with the review text, a 1-5 star rating, and details such as age, department and division.

## Approach

### 1. Data cleaning
- Dropped the extra index column (`Unnamed: 0`).
- Dropped rows with **no review text or no rating**, since they cannot be analysed.
- Filled the remaining blanks: `Age` with the **median**, category columns (Division, Department, Class) with the
  **most common value (mode)**, and a missing `Title` with empty text.
- Removed duplicate reviews (23,486 rows became 22,634).
- **Text cleaning:** made a new column `clean_review` in lower case, with special characters, numbers and extra spaces
  removed. The original `Review Text` is kept so it can be quoted in the emails.

### 2. Feature engineering (done by hand, no ML)
| Step | New columns / method |
|---|---|
| Text features | `char_count`, `word_count`, `exclamation_count`, `has_title` |
| Positive / negative words | Two hand-made word sets give `neg_word_count`, `pos_word_count` and `sentiment_score` (positive minus negative) |
| Complaint themes (1 = mentioned, 0 = not) | `theme_damaged`, `theme_delivery`, `theme_service`, `theme_quality`, `theme_sizing`, `theme_refund`, plus `theme_count` |
| Outlier handling | IQR rule (`Q1 - 1.5*IQR`, `Q3 + 1.5*IQR`) with capping on `Age` and `Positive Feedback Count`; box plots before and after for Age |
| Scaling | Min-max scaling with a formula: `age_scaled`, `word_count_scaled` |
| Encoding (no sklearn) | Label encoding (`department_code`) and one-hot encoding (`division_*`) |
| Critical flag and scores | `is_critical`, `severity_score`, `severity_scaled`, `priority_score` |
| Correlation heatmap | Shows how the new features relate to each other |

**Severity score** = 3 points for every missing star (5-star = 0, 1-star = 12) + 1 point per negative word + 2 points per
complaint theme + 2 points if the customer does not recommend the product.
**Priority score** = scaled severity + scaled review length, so the worst *and* most detailed reviews rank first.

### 3. Rule-based filtering and insights (no ML)
- **Critical review = rating of 1 or 2 stars**, a plain condition on the `Rating` column.
  Result: **2,369 critical reviews out of 22,634 (10.5%)**.
- **Complaint keywords:** every word in the critical reviews is counted with a dictionary loop (filler words in a
  `stopwords` list are ignored), and the top 15 are shown in a list and a bar chart.
- **Department view:** `groupby` (reviews, critical count, average severity) and `crosstab` show which departments
  have the most critical reviews.

### 4. Generative AI outreach
- The 3 critical reviews with the highest `priority_score` are selected.
- Each review, plus the problem themes found by our rules, is sent to Gemini with a prompt that makes it act as a
  **Customer Support Agent** and write a short apology email (maximum 120 words) that:
  - has a subject line and a greeting,
  - apologises and mentions the **specific** problems in the review,
  - offers a next step (refund, replacement or a call from support),
  - sounds warm and human, ends with "Customer Care Team", and does not invent facts.
- The emails are displayed as Markdown in the notebook and saved to `generated_emails.md`.

## How to run (Google Colab)
1. Open the notebook in Google Colab.
2. Download the dataset from Kaggle, upload it to Colab (folder icon on the left), right-click the file, choose
   **Copy path**, and paste that path into the `pd.read_csv("...")` line in section 2 if it differs from the one there.
3. Get a free Gemini API key from https://aistudio.google.com/apikey.
4. In Colab, click the **key icon (Secrets)** on the left, add a secret named exactly `Gemini_API_key`
   (the name used in the notebook code), paste your key as the value, and switch on **Notebook access**.
   Never paste the key into the notebook itself.
5. Choose **Runtime -> Run all**. The first Gen AI cell runs `!pip install -q google-genai`.
6. Find the results in the notebook output and in `generated_emails.md` (folder icon -> refresh -> download it before
   closing Colab, because Colab deletes its files when the session ends).

**Troubleshooting**
- *"model not found"*: change the `model_name` value in the Gen AI setup cell to a current Gemini model name.
- *503 UNAVAILABLE*: Google's servers are busy. Wait a minute and run the email cell again.

## Notes
- The positive/negative word lists, theme keywords and severity points are simple, hand-made rules based on common
  sense. They can be adjusted by editing the word sets and the formula.
- Keyword counting depends on the `stopwords` list. Add any filler word that appears in the top keywords.
