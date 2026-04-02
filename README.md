# Job Application Tracker

<<<<<<< HEAD
A web application to help track job applications during the job search process.

## Features (Coming Soon)
- Track companies and job listings
- Record application submissions
- Manage interview schedules
- Store contact information

## Technologies
- MySQL Database
- Python with Flask
- HTML/CSS for the web interface
=======
A full-stack Flask + MySQL web application for tracking companies, job postings, applications, and contacts. The system also includes a dashboard and a job match feature that ranks jobs based on skill alignment using JSON data.

---

## Features

* Full CRUD operations for:

  * Companies
  * Jobs
  * Applications
  * Contacts
* Dashboard with:

  * Summary statistics
  * Recent applications
* Job match feature:

  * Calculates match percentage based on required skills (stored as JSON)
* Input validation:

  * Required fields
  * Salary range checks
  * JSON format validation
* Clean UI using Bootstrap

---

## Project Structure

job_tracker/
├── app.py
├── database.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── companies.html
│   ├── jobs.html
│   ├── applications.html
│   ├── contacts.html
│   └── job_match.html
├── static/
│   └── style.css
├── schema.sql
├── AI_USAGE.md
├── README.md
└── requirements.txt

---

## Requirements

* Python 3.10+
* MySQL Server 8.0+
* pip

---

## Setup Instructions

1. Create and activate a virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Create the database:

   ```
   mysql -u root -p < schema.sql
   ```

4. Ensure MySQL is running on port 3306.

5. Run the application:

   ```
   python app.py
   ```

6. Open the application in your browser:

   ```
   http://127.0.0.1:5000
   ```

---

## Database Configuration

The application connects to MySQL using the following settings (defined in `database.py`):

* Host: 127.0.0.1
* Port: 3306
* User: root
* Password: root
* Database: job_tracker

If your MySQL configuration is different, update the values inside `database.py`.

---

## Notes

* `jobs.requirements` is stored as a JSON array of required skills.
* `applications.interview_data` is stored as a JSON object.
* The `schema.sql` file initializes all required tables.
* The MySQL server must be running before starting the application.
* The project is intended for local development and educational purposes, that is why it is run using debug=True.

---

## Tested Environment

* Windows 10/11
* Python 3.x (virtual environment)
* MySQL Server 8.0
* MySQL Workbench

---

## AI Usage

See `AI_USAGE.md` for details on how AI tools were used during development.

---

## Author

Franco Silvestri
