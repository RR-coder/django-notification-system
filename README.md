# django notification system

django rest api for managing students, teachers, classes and notifications

## what this project does

- has three roles: admin, teacher and student
- admin can create classes and assign teachers and students
- users can log in using jwt authentication
- users can receive a login otp through telegram
- admin can create notification templates and decide which roles can use them
- teachers can notify selected students or all students in their assigned classes
- admin can send notifications to any user
- students can notify one student from their own class, with a one notification per hour limit
- users can search their own notifications from the last 7 days
- github actions runs the tests and mock deployment
- telegram messages are sent to admins when the ci workflow succeeds or fails

## project structure

```text
accounts/       users, roles and telegram otp
classes/        classes and teacher/student assignments
notifications/  templates and notifications
config/         django settings and urls
.github/        github actions workflow
manage.py       django management command
requirements.txt project dependencies
```

## setup

clone the project:

```bash
git clone https://github.com/RR-coder/django-notification-system.git
cd django-notification-system
```

create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

install dependencies:

```bash
pip install -r requirements.txt
```

run migrations:

```bash
python manage.py migrate
```

run the server:

```bash
python manage.py runserver
```

## environment variables

telegram is used for login otps and ci notifications

the following values are kept as environment variables or github repository secrets:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_CHAT_ID
```

the bot token should not be committed to the repository

## authentication

jwt is used for api authentication

main authentication endpoints:

```text
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/me/
```

telegram otp endpoints:

```text
POST /api/auth/telegram/request-otp/
POST /api/auth/telegram/verify-otp/
```

the otp is sent to the telegram chat linked to the user. otps expire after a short period and cannot be reused

## roles and permissions

### admin

admin can manage users and classes, assign teachers and students, manage notification templates and send notifications to users

### teacher

a teacher can send notifications to selected students or all students from classes assigned to that teacher

### student

a student can send a notification to one other student from the same class. students are limited to one notification in an hour

these checks are handled in the backend so they cannot be bypassed by changing a frontend request

## notification templates

notification templates are created by admins

each template has allowed roles. when a user tries to send a notification, the api checks whether the user's role is allowed to use the selected template

main endpoints:

```text
/api/notification-templates/
/api/notifications/
```

notifications can be searched using the search parameter. only the user's own notifications from the previous 7 days are returned

example:

```text
/api/notifications/?search=exam
```

## ci/cd

the github actions workflow is located at:

```text
.github/workflows/ci.yml
```

the workflow:

1. installs the project dependencies
2. runs django checks
3. runs the tests
4. runs collectstatic as a mock deployment step
5. sends a telegram notification to the admin chat when the workflow succeeds or fails

the workflow can also be started manually using the github actions run workflow option

there is no real hosting deployment in this project. the deployment step is mocked as allowed by the assignment

## testing

run django checks:

```bash
python manage.py check
```

run tests:

```bash
python manage.py test
```

the test suite covers telegram otp, notifications and the main permission rules

## main decisions

django rest framework was used because the project is mainly an api backend

jwt was used for api authentication so protected api requests can be authenticated without using django session authentication

telegram chat ids are stored against users so an otp is sent to the correct user's telegram chat

role and class checks are done on the backend. this keeps notification permissions enforced even when requests are made directly to the api

sqlite is used for local development because it is simple to set up. a production database can be used later if the project is deployed

github actions uses a mock deployment because real hosting was not required. the tests and checks must pass before the deployment step is reached

## known limitations

- the deployment is mocked and there is no production server
- sqlite is intended for local development
- telegram configuration is required for telegram otp and ci telegram messages
