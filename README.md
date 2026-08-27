# Django Notification System

Django REST API for managing students, teachers, classes and notifications.

## What this project does

- Has three roles: Admin, Teacher and Student
- Admin can create classes and assign teachers and students
- Users can log in using JWT authentication
- Users can receive a login OTP through Telegram
- Admin can create notification templates and decide which roles can use them
- Teachers can notify selected students or all students in their assigned classes
- Admin can send notifications to any user
- Students can notify one student from their own class, with a one notification per hour limit
- Users can search their own notifications from the last 7 days
- GitHub Actions runs the tests and mock deployment
- Telegram messages are sent to admins when the CI workflow succeeds or fails

## Project Structure

```text
accounts/       users, roles and Telegram OTP
classes/        classes and teacher/student assignments
notifications/  templates and notifications
config/         Django settings and URLs
.github/        GitHub Actions workflow
manage.py       Django management command
requirements.txt project dependencies
```

## Setup

Clone the project:

```bash
git clone https://github.com/RR-coder/django-notification-system.git
cd django-notification-system
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Run the server:

```bash
python manage.py runserver
```

## Environment Variables

Telegram is used for login OTPs and CI notifications.

The following values are kept as environment variables or GitHub repository secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID
```

The bot token should not be committed to the repository.

## Authentication

JWT is used for API authentication.

Main authentication endpoints:

```text
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/me/
```

Telegram OTP endpoints:

```text
POST /api/auth/telegram/request-otp/
POST /api/auth/telegram/verify-otp/
```

The OTP is sent to the Telegram chat linked to the user. OTPs expire after a short period and cannot be reused.

## Roles and Permissions

### Admin

Admin can manage users and classes, assign teachers and students, manage notification templates and send notifications to users.

### Teacher

A teacher can send notifications to selected students or all students from classes assigned to that teacher.

### Student

A student can send a notification to one other student from the same class. Students are limited to one notification in an hour.

These checks are handled in the backend so they cannot be bypassed by changing a frontend request.

## Notification Templates

Notification templates are created by admins.

Each template has allowed roles. When a user tries to send a notification, the API checks whether the user's role is allowed to use the selected template.

Main endpoints:

```text
/api/notification-templates/
/api/notifications/
```

Notifications can be searched using the search parameter. Only the user's own notifications from the previous 7 days are returned.

Example:

```text
/api/notifications/?search=exam
```

## CI/CD

The GitHub Actions workflow is located at:

```text
.github/workflows/ci.yml
```

The workflow:

1. Installs the project dependencies.
2. Runs Django checks.
3. Runs the tests.
4. Runs collectstatic as a mock deployment step.
5. Sends a Telegram notification to the admin chat when the workflow succeeds or fails.

The workflow can also be started manually using the GitHub Actions Run workflow option.

There is no real hosting deployment in this project. The deployment step is mocked as allowed by the assignment.

## Testing

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
python manage.py test
```

The current test suite covers the Telegram OTP flow and its basic restrictions.

## Main Decisions

Django REST Framework was used because the project is mainly an API backend.

JWT was used for API authentication so protected API requests can be authenticated without using Django session authentication.

Telegram chat IDs are stored against users so an OTP is sent to the correct user's Telegram chat.

Role and class checks are done on the backend. This keeps notification permissions enforced even when requests are made directly to the API.

SQLite is used for local development because it is simple to set up. A production database can be used later if the project is deployed.

GitHub Actions uses a mock deployment because real hosting was not required. The tests and checks must pass before the deployment step is reached.

## Known Limitations

- The deployment is mocked and there is no production server.
- SQLite is intended for local development.
- Telegram configuration is required for Telegram OTP and CI Telegram messages.
