# AI Usage Documentation

## Tools Used
- ChatGPT for planning the project structure, Flask routes, SQL schema, validation logic, and UI layout.

## Key Prompts
1. Build a Flask + MySQL project that follows the exact assignment structure.
2. Generate CRUD routes for companies, jobs, applications, and contacts.
3. Create a job match feature that compares user skills against JSON requirements and ranks by percentage.
4. Produce a Bootstrap-based UI with dashboard cards, tables, and inline edit/add forms.

## What Worked Well
- AI helped generate boilerplate CRUD patterns quickly.
- AI helped design the matching algorithm for JSON skill arrays.
- AI helped organize the code into a consistent structure that matches the assignment requirements
- AI helped me build test cases and debug the code during development

## What I Modified
- Adjusted variable names and queries to match the required schema.
- Added validation for salary ranges, required fields, and JSON input.
- Kept the exact folder structure requested in the assignment.
- Included seed data in `schema.sql` to make testing easier.

## Lessons Learned
- AI is useful for scaffolding, but everything still needs testing.
- Schema consistency matters a lot in Flask + MySQL projects.
- It is important to customize generated code so it matches project requirements exactly.
