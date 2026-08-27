# Django Notification System

A Django REST API for managing users, classes, and notifications.

This project lets different types of users send notifications based on their role. It also includes Telegram OTP login and a GitHub Actions workflow for running tests and checking the deployment step.

## Features

- JWT based authentication
- Admin, Teacher and Student roles
- Class management
- Telegram OTP login
- OTP expiry and resend cooldown
- Role based notification permissions
- Notification templates
- Send notifications to selected users or groups
- Search notifications from the last 7 days
- GitHub Actions CI
- Telegram notification for CI success and failure

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- SQLite
- Telegram Bot API
- GitHub Actions

## Project Structure

The project is split into a few Django apps:

- accounts - handles users, authentication and Telegram OTP
- classes - handles classes and user assignments
- notifications - handles notification templates and notifications
- config - contains the main Django settings and URL configuration
- .github/workflows - contains the GitHub Actions CI workflow
- manage.py - Django management file
- requirements.txt - project dependencies

## Setup

Clone the repository and move into the project folder:

```bash
git clone https://github.com/RR-coder/django-notification-system.git
cd django-notification-system
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/` when the development server is started.

## Environment Variables

The Telegram bot token is kept outside the source code.

```text
TELEGRAM_BOT_TOKEN=your_bot_token
```

For GitHub Actions, these repository secrets are used:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID
```

The secrets can be added from Settings -> Secrets and variables -> Actions in the GitHub repository.

## Authentication

The API uses JWT authentication.

### Get Token

```text
POST /api/auth/token/
```

Example request:

```json
{
    "username": "student1",
    "password": "your_password"
}
```

### Refresh Token

```text
POST /api/auth/token/refresh/
```

### Current User

```text
GET /api/me/
```

Protected endpoints require the JWT access token.

## Telegram OTP

Telegram OTP is an additional login option. A Telegram chat ID needs to be linked to the user account before an OTP can be requested.

### Request OTP

```text
POST /api/auth/telegram/request-otp/
```

Example:

```json
{
    "username": "student1",
    "password": "your_password"
}
```

The OTP is sent to the user's linked Telegram chat.

### Verify OTP

```text
POST /api/auth/telegram/verify-otp/
```

Example:

```json
{
    "username": "student1",
    "otp": "123456"
}
```

The OTP has an expiry time, resend cooldown and limited verification attempts. A successfully used OTP cannot be used again.

## User Roles

There are three main roles in the project.

### Admin

Admins have the highest level of access. They can manage classes, users and notification related features and can send notifications to selected users or groups.

### Teacher

Teachers can work with students from their assigned classes and send notifications to those students.

### Student

Students have more limited notification permissions. A student can send a notification to another student from the same class, subject to the limits implemented in the API.

The backend checks the permissions instead of relying only on the frontend.

## Classes

Classes are used to connect teachers and students. Admin users can manage class assignments.

Teacher and student notification permissions are based on these class relationships.

## Notifications

Notifications are handled through:

```text
/api/notifications/
```

Notification templates are handled through:

```text
/api/notification-templates/
```

Before sending a notification, the API checks the sender's role and class relationship.

Notifications can also be searched using the `search` query parameter. The notification history is limited to the recent 7 days according to the project requirements.

Example:

```text
/api/notifications/?search=exam
```

## Main API Endpoints

```text
Authentication
POST /api/auth/token/
POST /api/auth/token/refresh/
POST /api/auth/telegram/request-otp/
POST /api/auth/telegram/verify-otp/
GET  /api/me/

Classes
/api/classes/

Notification Templates
/api/notification-templates/

Notifications
/api/notifications/
```

## Testing

Run the Django system check:

```bash
python manage.py check
```

Run the tests:

```bash
python manage.py test
```

The tests currently cover the Telegram OTP flow, including requesting an OTP, checking the Telegram chat, verifying the OTP, preventing OTP reuse and the resend cooldown.

## GitHub Actions

The CI workflow is stored in:

```text
.github/workflows/ci.yml
```

It runs on pushes and pull requests and can also be started manually from GitHub Actions.

The workflow:

1. Sets up Python and installs dependencies.
2. Runs Django system checks.
3. Runs the test suite.
4. Collects static files as part of a mock deployment step.
5. Sends a Telegram message when the workflow succeeds or fails.

The deployment step is only a mock for now because there is no production server connected to the project.

## Design Decisions

The project is split into separate Django apps so that users/authentication, classes and notifications are easier to manage separately.

JWT is used for API authentication because the application is built as a REST API. Telegram OTP is kept as a separate authentication flow and returns JWT tokens after successful verification.

Role and class based permission checks are handled on the backend. This is important because frontend checks alone would not prevent a user from sending a modified API request.

SQLite is used because it is simple for local development and is enough for the scope of this project. A production setup could use PostgreSQL or another production database.

The CI deployment stage is mocked because setting up an actual production server is outside the scope of the project.

## Security Notes

Do not commit Telegram bot tokens, passwords or other secrets to the repository.

The project uses GitHub repository secrets for Telegram CI notifications. Local environment files, the SQLite database, virtual environments and generated static files are excluded through `.gitignore`.

For a real production deployment, settings like `DEBUG`, `ALLOWED_HOSTS`, HTTPS and a production database would need to be configured properly.

## Known Limitations

- The deployment step in GitHub Actions is currently a mock deployment.
- SQLite is used for local development.
- Telegram configuration is required for Telegram OTP and CI notifications.

## Author

RR-coder

## Repository

https://github.com/RR-coder/django-notification-system