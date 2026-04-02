DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

CREATE TABLE companies (
    company_id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    website VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    notes TEXT
);

CREATE TABLE jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    job_type ENUM('Full-time', 'Part-time', 'Contract', 'Internship'),
    salary_min INT,
    salary_max INT,
    job_url VARCHAR(300),
    date_posted DATE,
    requirements JSON,
    CONSTRAINT fk_jobs_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE applications (
    application_id INT PRIMARY KEY AUTO_INCREMENT,
    job_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn') DEFAULT 'Applied',
    resume_version VARCHAR(50),
    cover_letter_sent BOOLEAN,
    interview_data JSON,
    CONSTRAINT fk_applications_job
        FOREIGN KEY (job_id)
        REFERENCES jobs(job_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE contacts (
    contact_id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes TEXT,
    CONSTRAINT fk_contacts_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('TechCorp', 'Software', 'https://techcorp.example.com', 'Miami', 'FL', 'Strong backend engineering roles.'),
('DataCo', 'Analytics', 'https://dataco.example.com', 'Orlando', 'FL', 'Often posts data analyst internships.'),
('CloudNova', 'Cloud Computing', 'https://cloudnova.example.com', 'Austin', 'TX', 'Known for DevOps and platform positions.');

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 85000, 110000, 'https://techcorp.example.com/jobs/1', '2026-03-10', JSON_ARRAY('Python', 'SQL', 'Flask')),
(2, 'Data Analyst', 'Internship', 25000, 35000, 'https://dataco.example.com/jobs/2', '2026-03-18', JSON_ARRAY('Python', 'SQL', 'Tableau')),
(3, 'Cloud Engineer', 'Full-time', 95000, 125000, 'https://cloudnova.example.com/jobs/3', '2026-03-21', JSON_ARRAY('AWS', 'Python', 'Docker', 'Git'));

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-03-20', 'Interview', 'v3', TRUE, JSON_OBJECT('interview_date', '2026-03-28', 'interviewers', JSON_ARRAY('Jane Smith', 'Alex Kim'), 'next_steps', 'Technical interview pending')),
(2, '2026-03-25', 'Applied', 'v2', FALSE, JSON_OBJECT('interview_date', NULL, 'interviewers', JSON_ARRAY(), 'next_steps', 'Waiting for recruiter response'));

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Jane Smith', 'Recruiter', 'jane.smith@techcorp.example.com', '305-555-1101', 'https://linkedin.com/in/janesmith', 'Primary recruiter contact.'),
(2, 'David Brown', 'Hiring Manager', 'david.brown@dataco.example.com', '407-555-2244', 'https://linkedin.com/in/davidbrown', 'Met during campus networking event.'),
(3, 'Sophia Lee', 'Talent Partner', 'sophia.lee@cloudnova.example.com', '512-555-7712', 'https://linkedin.com/in/sophialee', 'Good contact for cloud roles.');
