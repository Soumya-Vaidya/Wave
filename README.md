# Wave: NLP powered Smart Journaling App

Wave provides users with the ability to journal daily entries while offering emotion prediction and analysis. With over 25 emotions and stress detection capabilities, users can gain valuable insights into their emotional well-being over time. The application also includes various data visualizations such as correlation of stress with emotions, emotions over a period of time, and more.


## Getting Started

To run the project, follow these steps:

1. Clone the repository 

```
git clone https://github.com/Soumya-Vaidya/Wave.git
```
2. Open the project folder.
3. Navigate to the `App` directory.

```
cd app
```
4. Install the required dependencies
```
pip install -r requirements.txt
```
5. To run the application, run the following command
```
python app.py
```
6. Visit http://localhost:8000/ in your browser to access the app.

Now, you're ready to start using Wave!

## Features

- **Customizable Profile:** Users can customize their profiles to personalize their journaling experience.
- **Daily Journal Entry:** Users can enter daily journal entries, which are editable only during that day, and receive live analysis of emotions and stress.
- **Color-Coded Entries:** Previous journal entries are displayed with color-coding according to the dominant emotion.
- **Detailed Analytics:** The application provides a detailed analytics page offering breakdowns of emotions and stress levels over time through pie charts, histograms, line charts, etc.
- **Data Encryption:** All data is encrypted with AES to ensure that no data is readable to anyone except the user.
- **Secure Endpoints:** Endpoints are secured using JWT authentication with the use of cookies.
- **Password Security:** User passwords are hashed using bcrypt for enhanced security.

## Tech Stack
- Python Flask for backend development.
- HTML, CSS, JavaScript, Bootstrap, and jQuery for frontend development.
- SQLite for database management.
- Scikit-learn's ExtraTrees Classifier, SGD, and Random Forest for emotion and stress classification models.
- Count Vectorizer for vectorization of text.
- NLTK for lemmatization, tokenization, etc.
- JWT, bcrypt, AES Engine (SQLAlchemy) for securing data.

