# FocusFlow

FocusFlow is a powerful task management web application built with Python Flask. It helps users efficiently organize their daily tasks, set due dates, reminders, and track progress with an intuitive interface.

## Features

- User registration, login, and authentication using Flask-Login.
- Create, update, and delete tasks.
- Assign tasks to custom categories.
- Set task due dates and reminder notifications.
- Mark tasks as completed by toggling a checkbox.
- Responsive design using Bootstrap 5 and Bootstrap Icons.
- Flash messages for user-friendly feedback.
- Logo and modern UI for better user experience.

## Technologies Used

- Python 3.x
- Flask web framework
- Flask-Login for authentication
- Flask-WTF for forms with CSRF protection
- SQLAlchemy ORM with SQLite (or other databases)
- Bootstrap 5 and Bootstrap Icons for frontend UI
- Jinja2 templating engine

## Installation

1. Clone the repo:  
git clone https://github.com/joanjullie59/pythontodo_list_website

2. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate # Linux/macOS
   venv\Scripts\activate # Windows

3. Install dependencies:
   pip install -r requirements.txt

4. Initialize the database:
- If using Flask-Migrate:
  ```
  flask db upgrade
  ```
- Or create the `todo` table and others according to your models.

5. Run the application:
flask run
or use python run.py


6. Open your browser at [http://localhost:5000](http://localhost:5000).

## Usage

- Register a new user account.
- Add tasks with optional categories, due dates, and reminders.
- Mark tasks as completed by clicking the checkbox.
- Update or delete tasks as needed.
- Logout to secure your account.

## Project Structure

- `focusflow/` - main Flask app package
- `routes.py` - routes and view functions
- `models.py` - SQLAlchemy data models
- `forms.py` - WTForms definitions
- `templates/` - Jinja2 HTML templates
- `static/` - static assets like CSS, images, and JavaScript

- `run.py` - app entrypoint
- `requirements.txt` - Python dependencies
- `README.md` - project documentation



## License

Specify your project's license here, e.g., MIT


Feel free to customize this `README.md` as per your specific project details or to add deployment instructions, testing, or contribution guidelines.



