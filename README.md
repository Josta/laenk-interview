Project Setup

Follow these steps to get the project running locally.

1. Environment Configuration

All commands should be run from the root of the laenk-interview directory.

2. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage dependencies.

# Create the virtual environment (named 'venv')
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate


(On Windows, activate with: .\venv\Scripts\activate)

3. Install Dependencies

Install all required Python packages using the provided requirements.txt file.

# Ensure your virtual environment is active
pip install -r requirements.txt


4. Run Database Migrations

Apply the database schema to your local db.sqlite3 file.

python manage.py migrate


Populating the Database

To test the slow API, you must first populate the database with a large amount of mock data. A convenience script is provided for this.

Note: This script will generate 1.22 million database records (70k users, 150k appliers, 1M questions). This may take a few minutes to run.

python manage.py populate_db


You will see output in your terminal as the script progresses through each phase.

Running the Server

Once the database is populated, start the Django development server:

python manage.py runserver


Testing the API

The server will be running at http://127.0.0.1:8000/.

You can now access the slow API endpoint in your browser or through a tool like curl or Postman.

Slow API Endpoint: http://127.0.0.1:8000/api/v1/appliers/list/

This endpoint fetches all appliers who have more than 16 screening questions and serializes their data, along with the related user data.
