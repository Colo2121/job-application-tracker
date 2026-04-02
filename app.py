import json
from flask import Flask, render_template, request, redirect, url_for, flash
from mysql.connector import Error
from database import get_db_connection, test_connection

app = Flask(__name__)
app.secret_key = 'job-tracker-secret-key'


# ----------------------------
# Helpers
# ----------------------------
def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def normalize_text(value):
    value = (value or '').strip()
    return value if value else None


def parse_int(value, field_name, required=False):
    value = (value or '').strip()
    if not value:
        if required:
            raise ValueError(f'{field_name} is required.')
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f'{field_name} must be a whole number.') from exc


def parse_json_array_from_skills(text):
    text = (text or '').strip()
    if not text:
        return json.dumps([])

    skills = []
    seen = set()

    for raw_skill in text.split(','):
        skill = raw_skill.strip()
        if skill and skill.lower() not in seen:
            skills.append(skill)
            seen.add(skill.lower())

    return json.dumps(skills)


def parse_json_object_field(text, field_name):
    text = (text or '').strip()
    if not text:
        return json.dumps({})

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'{field_name} must be valid JSON.') from exc

    if not isinstance(parsed, dict):
        raise ValueError(f'{field_name} must be a JSON object.')

    return json.dumps(parsed)


def pretty_json(value):
    if value in (None, ''):
        return ''
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2)
    try:
        return json.dumps(json.loads(value), indent=2)
    except (json.JSONDecodeError, TypeError):
        return str(value)


def safe_json_loads(value, default):
    if value in (None, ''):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def normalize_skills(skills):
    return {skill.strip().lower(): skill.strip() for skill in skills if skill and skill.strip()}


def status_badge_class(status):
    mapping = {
        'Applied': 'secondary',
        'Screening': 'info',
        'Interview': 'warning text-dark',
        'Offer': 'success',
        'Rejected': 'danger',
        'Withdrawn': 'dark',
    }
    return mapping.get(status, 'secondary')


def enrich_job_requirements(rows):
    for row in rows:
        row['requirements_list'] = safe_json_loads(row.get('requirements'), [])
    return rows


def enrich_interview_data(rows):
    for row in rows:
        row['interview_parsed'] = safe_json_loads(row.get('interview_data'), {})
    return rows


@app.context_processor
def inject_globals():
    return {'status_badge_class': status_badge_class}


# ----------------------------
# Dashboard
# ----------------------------
@app.route('/')
@app.route('/dashboard')
@app.route('/home')
def dashboard():
    db_ok, db_message = test_connection()
    stats = {'companies': 0, 'jobs': 0, 'applications': 0, 'contacts': 0}
    status_counts = []
    recent_applications = []
    top_companies = []

    if db_ok:
        try:
            stats = fetch_one(
                """
                SELECT
                    (SELECT COUNT(*) FROM companies) AS companies,
                    (SELECT COUNT(*) FROM jobs) AS jobs,
                    (SELECT COUNT(*) FROM applications) AS applications,
                    (SELECT COUNT(*) FROM contacts) AS contacts
                """
            )

            status_counts = fetch_all(
                """
                SELECT status, COUNT(*) AS total
                FROM applications
                GROUP BY status
                ORDER BY total DESC, status ASC
                """
            )

            recent_applications = fetch_all(
                """
                SELECT a.application_id, a.application_date, a.status,
                       j.job_title, c.company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN companies c ON j.company_id = c.company_id
                ORDER BY a.application_date DESC, a.application_id DESC
                LIMIT 5
                """
            )

            top_companies = fetch_all(
                """
                SELECT c.company_name, COUNT(j.job_id) AS total_jobs
                FROM companies c
                LEFT JOIN jobs j ON c.company_id = j.company_id
                GROUP BY c.company_id, c.company_name
                ORDER BY total_jobs DESC, c.company_name ASC
                LIMIT 5
                """
            )
        except Error as exc:
            db_ok = False
            db_message = str(exc)

    return render_template(
        'dashboard.html',
        db_ok=db_ok,
        db_message=db_message,
        stats=stats,
        status_counts=status_counts,
        recent_applications=recent_applications,
        top_companies=top_companies,
    )


# ----------------------------
# Companies
# ----------------------------
@app.route('/companies')
def companies():
    try:
        all_companies = fetch_all("SELECT * FROM companies ORDER BY company_name")
        selected_id = request.args.get('view', type=int)
        edit_id = request.args.get('edit', type=int)
        selected_company = None
        edit_company = None

        if selected_id:
            selected_company = fetch_one(
                "SELECT * FROM companies WHERE company_id = %s",
                (selected_id,)
            )

        if edit_id:
            edit_company = fetch_one(
                "SELECT * FROM companies WHERE company_id = %s",
                (edit_id,)
            )

        return render_template(
            'companies.html',
            companies=all_companies,
            selected_company=selected_company,
            edit_company=edit_company,
        )
    except Error as exc:
        flash(f'Database error: {exc}', 'danger')
        return render_template(
            'companies.html',
            companies=[],
            selected_company=None,
            edit_company=None,
        )


@app.route('/companies/add', methods=['POST'])
def add_company():
    try:
        company_name = normalize_text(request.form.get('company_name'))
        if not company_name:
            raise ValueError('Company name is required.')

        execute_query(
            """
            INSERT INTO companies (company_name, industry, website, city, state, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                company_name,
                normalize_text(request.form.get('industry')),
                normalize_text(request.form.get('website')),
                normalize_text(request.form.get('city')),
                normalize_text(request.form.get('state')),
                normalize_text(request.form.get('notes')),
            ),
        )
        flash('Company added successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('companies'))


@app.route('/companies/edit/<int:company_id>', methods=['POST'])
def edit_company(company_id):
    try:
        company_name = normalize_text(request.form.get('company_name'))
        if not company_name:
            raise ValueError('Company name is required.')

        execute_query(
            """
            UPDATE companies
            SET company_name = %s,
                industry = %s,
                website = %s,
                city = %s,
                state = %s,
                notes = %s
            WHERE company_id = %s
            """,
            (
                company_name,
                normalize_text(request.form.get('industry')),
                normalize_text(request.form.get('website')),
                normalize_text(request.form.get('city')),
                normalize_text(request.form.get('state')),
                normalize_text(request.form.get('notes')),
                company_id,
            ),
        )
        flash('Company updated successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('companies'))


@app.route('/companies/delete/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    try:
        execute_query("DELETE FROM companies WHERE company_id = %s", (company_id,))
        flash('Company deleted successfully.', 'success')
    except Error as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('companies'))


# ----------------------------
# Jobs
# ----------------------------
@app.route('/jobs')
def jobs():
    try:
        all_jobs = fetch_all(
            """
            SELECT j.*, c.company_name
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY j.date_posted DESC, j.job_title ASC
            """
        )
        enrich_job_requirements(all_jobs)

        all_companies = fetch_all(
            "SELECT company_id, company_name FROM companies ORDER BY company_name"
        )

        selected_id = request.args.get('view', type=int)
        edit_id = request.args.get('edit', type=int)
        selected_job = None
        edit_job = None

        if selected_id:
            selected_job = fetch_one(
                """
                SELECT j.*, c.company_name
                FROM jobs j
                JOIN companies c ON j.company_id = c.company_id
                WHERE j.job_id = %s
                """,
                (selected_id,),
            )
            if selected_job:
                selected_job['requirements_list'] = safe_json_loads(
                    selected_job.get('requirements'),
                    []
                )

        if edit_id:
            edit_job = fetch_one(
                "SELECT * FROM jobs WHERE job_id = %s",
                (edit_id,)
            )
            if edit_job:
                edit_job['requirements_text'] = ', '.join(
                    safe_json_loads(edit_job.get('requirements'), [])
                )

        return render_template(
            'jobs.html',
            jobs=all_jobs,
            companies=all_companies,
            selected_job=selected_job,
            edit_job=edit_job,
        )
    except Error as exc:
        flash(f'Database error: {exc}', 'danger')
        return render_template(
            'jobs.html',
            jobs=[],
            companies=[],
            selected_job=None,
            edit_job=None,
        )


@app.route('/jobs/add', methods=['POST'])
def add_job():
    try:
        company_id = parse_int(request.form.get('company_id'), 'Company', required=True)
        job_title = normalize_text(request.form.get('job_title'))
        if not job_title:
            raise ValueError('Job title is required.')

        salary_min = parse_int(request.form.get('salary_min'), 'Minimum salary')
        salary_max = parse_int(request.form.get('salary_max'), 'Maximum salary')

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise ValueError('Minimum salary cannot be greater than maximum salary.')

        execute_query(
            """
            INSERT INTO jobs (
                company_id, job_title, job_type, salary_min, salary_max,
                job_url, date_posted, requirements
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                company_id,
                job_title,
                normalize_text(request.form.get('job_type')),
                salary_min,
                salary_max,
                normalize_text(request.form.get('job_url')),
                request.form.get('date_posted') or None,
                parse_json_array_from_skills(request.form.get('requirements_text')),
            ),
        )
        flash('Job added successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('jobs'))


@app.route('/jobs/edit/<int:job_id>', methods=['POST'])
def edit_job(job_id):
    try:
        company_id = parse_int(request.form.get('company_id'), 'Company', required=True)
        job_title = normalize_text(request.form.get('job_title'))
        if not job_title:
            raise ValueError('Job title is required.')

        salary_min = parse_int(request.form.get('salary_min'), 'Minimum salary')
        salary_max = parse_int(request.form.get('salary_max'), 'Maximum salary')

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise ValueError('Minimum salary cannot be greater than maximum salary.')

        execute_query(
            """
            UPDATE jobs
            SET company_id = %s,
                job_title = %s,
                job_type = %s,
                salary_min = %s,
                salary_max = %s,
                job_url = %s,
                date_posted = %s,
                requirements = %s
            WHERE job_id = %s
            """,
            (
                company_id,
                job_title,
                normalize_text(request.form.get('job_type')),
                salary_min,
                salary_max,
                normalize_text(request.form.get('job_url')),
                request.form.get('date_posted') or None,
                parse_json_array_from_skills(request.form.get('requirements_text')),
                job_id,
            ),
        )
        flash('Job updated successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('jobs'))


@app.route('/jobs/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    try:
        execute_query("DELETE FROM jobs WHERE job_id = %s", (job_id,))
        flash('Job deleted successfully.', 'success')
    except Error as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('jobs'))


# ----------------------------
# Applications
# ----------------------------
@app.route('/applications')
def applications():
    try:
        all_applications = fetch_all(
            """
            SELECT a.*, j.job_title, c.company_name
            FROM applications a
            JOIN jobs j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.application_date DESC, a.application_id DESC
            """
        )
        enrich_interview_data(all_applications)

        all_jobs = fetch_all(
            """
            SELECT j.job_id, j.job_title, c.company_name
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY c.company_name, j.job_title
            """
        )

        selected_id = request.args.get('view', type=int)
        edit_id = request.args.get('edit', type=int)
        selected_application = None
        edit_application = None

        if selected_id:
            selected_application = fetch_one(
                """
                SELECT a.*, j.job_title, c.company_name
                FROM applications a
                JOIN jobs j ON a.job_id = j.job_id
                JOIN companies c ON j.company_id = c.company_id
                WHERE a.application_id = %s
                """,
                (selected_id,),
            )
            if selected_application:
                selected_application['interview_parsed'] = safe_json_loads(
                    selected_application.get('interview_data'),
                    {}
                )

        if edit_id:
            edit_application = fetch_one(
                "SELECT * FROM applications WHERE application_id = %s",
                (edit_id,)
            )
            if edit_application:
                edit_application['interview_data_pretty'] = pretty_json(
                    edit_application.get('interview_data')
                )

        return render_template(
            'applications.html',
            applications=all_applications,
            jobs=all_jobs,
            selected_application=selected_application,
            edit_application=edit_application,
        )
    except Error as exc:
        flash(f'Database error: {exc}', 'danger')
        return render_template(
            'applications.html',
            applications=[],
            jobs=[],
            selected_application=None,
            edit_application=None,
        )


@app.route('/applications/add', methods=['POST'])
def add_application():
    try:
        job_id = parse_int(request.form.get('job_id'), 'Job', required=True)
        application_date = request.form.get('application_date')
        if not application_date:
            raise ValueError('Application date is required.')

        execute_query(
            """
            INSERT INTO applications (
                job_id, application_date, status, resume_version,
                cover_letter_sent, interview_data
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                job_id,
                application_date,
                normalize_text(request.form.get('status')) or 'Applied',
                normalize_text(request.form.get('resume_version')),
                1 if request.form.get('cover_letter_sent') == 'on' else 0,
                parse_json_object_field(request.form.get('interview_data'), 'Interview data'),
            ),
        )
        flash('Application added successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('applications'))


@app.route('/applications/edit/<int:application_id>', methods=['POST'])
def edit_application(application_id):
    try:
        job_id = parse_int(request.form.get('job_id'), 'Job', required=True)
        application_date = request.form.get('application_date')
        if not application_date:
            raise ValueError('Application date is required.')

        execute_query(
            """
            UPDATE applications
            SET job_id = %s,
                application_date = %s,
                status = %s,
                resume_version = %s,
                cover_letter_sent = %s,
                interview_data = %s
            WHERE application_id = %s
            """,
            (
                job_id,
                application_date,
                normalize_text(request.form.get('status')) or 'Applied',
                normalize_text(request.form.get('resume_version')),
                1 if request.form.get('cover_letter_sent') == 'on' else 0,
                parse_json_object_field(request.form.get('interview_data'), 'Interview data'),
                application_id,
            ),
        )
        flash('Application updated successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('applications'))


@app.route('/applications/delete/<int:application_id>', methods=['POST'])
def delete_application(application_id):
    try:
        execute_query("DELETE FROM applications WHERE application_id = %s", (application_id,))
        flash('Application deleted successfully.', 'success')
    except Error as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('applications'))


# ----------------------------
# Contacts
# ----------------------------
@app.route('/contacts')
def contacts():
    try:
        all_contacts = fetch_all(
            """
            SELECT ct.*, c.company_name
            FROM contacts ct
            JOIN companies c ON ct.company_id = c.company_id
            ORDER BY c.company_name, ct.contact_name
            """
        )

        all_companies = fetch_all(
            "SELECT company_id, company_name FROM companies ORDER BY company_name"
        )

        selected_id = request.args.get('view', type=int)
        edit_id = request.args.get('edit', type=int)
        selected_contact = None
        edit_contact = None

        if selected_id:
            selected_contact = fetch_one(
                """
                SELECT ct.*, c.company_name
                FROM contacts ct
                JOIN companies c ON ct.company_id = c.company_id
                WHERE ct.contact_id = %s
                """,
                (selected_id,),
            )

        if edit_id:
            edit_contact = fetch_one(
                "SELECT * FROM contacts WHERE contact_id = %s",
                (edit_id,)
            )

        return render_template(
            'contacts.html',
            contacts=all_contacts,
            companies=all_companies,
            selected_contact=selected_contact,
            edit_contact=edit_contact,
        )
    except Error as exc:
        flash(f'Database error: {exc}', 'danger')
        return render_template(
            'contacts.html',
            contacts=[],
            companies=[],
            selected_contact=None,
            edit_contact=None,
        )


@app.route('/contacts/add', methods=['POST'])
def add_contact():
    try:
        company_id = parse_int(request.form.get('company_id'), 'Company', required=True)
        contact_name = normalize_text(request.form.get('contact_name'))
        if not contact_name:
            raise ValueError('Contact name is required.')

        execute_query(
            """
            INSERT INTO contacts (
                company_id, contact_name, title, email, phone,
                linkedin_url, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                company_id,
                contact_name,
                normalize_text(request.form.get('title')),
                normalize_text(request.form.get('email')),
                normalize_text(request.form.get('phone')),
                normalize_text(request.form.get('linkedin_url')),
                normalize_text(request.form.get('notes')),
            ),
        )
        flash('Contact added successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('contacts'))


@app.route('/contacts/edit/<int:contact_id>', methods=['POST'])
def edit_contact(contact_id):
    try:
        company_id = parse_int(request.form.get('company_id'), 'Company', required=True)
        contact_name = normalize_text(request.form.get('contact_name'))
        if not contact_name:
            raise ValueError('Contact name is required.')

        execute_query(
            """
            UPDATE contacts
            SET company_id = %s,
                contact_name = %s,
                title = %s,
                email = %s,
                phone = %s,
                linkedin_url = %s,
                notes = %s
            WHERE contact_id = %s
            """,
            (
                company_id,
                contact_name,
                normalize_text(request.form.get('title')),
                normalize_text(request.form.get('email')),
                normalize_text(request.form.get('phone')),
                normalize_text(request.form.get('linkedin_url')),
                normalize_text(request.form.get('notes')),
                contact_id,
            ),
        )
        flash('Contact updated successfully.', 'success')
    except (ValueError, Error) as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('contacts'))


@app.route('/contacts/delete/<int:contact_id>', methods=['POST'])
def delete_contact(contact_id):
    try:
        execute_query("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
        flash('Contact deleted successfully.', 'success')
    except Error as exc:
        flash(str(exc), 'danger')

    return redirect(url_for('contacts'))


# ----------------------------
# Job Match
# ----------------------------
@app.route('/job_match', methods=['GET', 'POST'])
@app.route('/job-match', methods=['GET', 'POST'])
def job_match():
    user_skills_text = ''
    results = []

    if request.method == 'POST':
        user_skills_text = request.form.get('skills', '')
        user_skills_list = [skill.strip() for skill in user_skills_text.split(',') if skill.strip()]
        normalized_user_skills = normalize_skills(user_skills_list)

        try:
            jobs_list = fetch_all(
                """
                SELECT j.job_id, j.job_title, j.job_type, j.requirements, c.company_name
                FROM jobs j
                JOIN companies c ON j.company_id = c.company_id
                ORDER BY j.job_title ASC
                """
            )

            for job in jobs_list:
                requirements = safe_json_loads(job.get('requirements'), [])
                normalized_requirements = normalize_skills(requirements)

                matched_lower = set(normalized_user_skills.keys()) & set(normalized_requirements.keys())
                matched = [normalized_requirements[key] for key in normalized_requirements if key in matched_lower]
                missing = [normalized_requirements[key] for key in normalized_requirements if key not in matched_lower]

                total_required = len(normalized_requirements)
                match_percentage = 0
                if total_required > 0:
                    match_percentage = round((len(matched) / total_required) * 100)

                results.append({
                    'job_id': job['job_id'],
                    'job_title': job['job_title'],
                    'company_name': job['company_name'],
                    'job_type': job['job_type'],
                    'requirements': list(normalized_requirements.values()),
                    'matched': matched,
                    'missing': missing,
                    'matched_count': len(matched),
                    'total_required': total_required,
                    'match_percentage': match_percentage,
                })

            results.sort(
                key=lambda item: (
                    -item['match_percentage'],
                    item['company_name'],
                    item['job_title']
                )
            )
        except Error as exc:
            flash(f'Database error: {exc}', 'danger')

    return render_template(
        'job_match.html',
        user_skills_text=user_skills_text,
        results=results
    )


# ----------------------------
# Run App
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)