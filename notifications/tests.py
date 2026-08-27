from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from datetime import timedelta

from accounts.models import User
from classes.models import Class
from notifications.models import Notification, NotificationTemplate

class NotificationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='adminpass', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher', password='teacherpass', role=User.Role.TEACHER)
        self.student1 = User.objects.create_user(username='student1', password='studentpass', role=User.Role.STUDENT)
        self.student2 = User.objects.create_user(username='student2', password='studentpass', role=User.Role.STUDENT)
        self.student3 = User.objects.create_user(username='student3', password='studentpass', role=User.Role.STUDENT)

        self.class1 = Class.objects.create(name='Class 1')
        self.class2 = Class.objects.create(name='Class 2')

        self.class1.teachers.add(self.teacher)

        self.class1.students.add(self.student1, self.student2)
        self.class2.students.add(self.student3)

        self.admin_template = NotificationTemplate.objects.create(
            name='Admin Template',
            title='Admin Title',
            message='Admin Message',
            allowed_roles=[User.Role.ADMIN.value]
        )
        self.teacher_template = NotificationTemplate.objects.create(
            name='Teacher Template',
            title='Teacher Title',
            message='Teacher Message',
            allowed_roles=[User.Role.TEACHER.value]
        )
        self.student_template = NotificationTemplate.objects.create(
            name='Student Template',
            title='Student Title',
            message='Student Message',
            allowed_roles=[User.Role.STUDENT.value]
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_admin_can_notify_any_user(self):
        self.authenticate(self.admin)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student3.id],
            'notification_type': 'GENERAL',
            'template_id': self.admin_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.sender, self.admin)
        self.assertEqual(notification.recipient, self.student3)
        self.assertEqual(notification.title, self.admin_template.title)
        self.assertEqual(notification.message, self.admin_template.message)

    def test_teacher_can_notify_selected_students_in_assigned_classes(self):
        self.authenticate(self.teacher)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student1.id],
            'notification_type': 'GENERAL',
            'template_id': self.teacher_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.first()
        self.assertEqual(notification.sender, self.teacher)
        self.assertEqual(notification.recipient, self.student1)
        self.assertEqual(notification.title, self.teacher_template.title)
        self.assertEqual(notification.message, self.teacher_template.message)

    def test_teacher_can_notify_all_students_in_assigned_classes(self):
        self.authenticate(self.teacher)
        url = '/api/notifications/'
        data = {
            'send_to_all': True,
            'notification_type': 'GENERAL',
            'template_id': self.teacher_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notifications = Notification.objects.filter(sender=self.teacher)
        class1_students = set(self.class1.students.all())
        notified_students = set(n.recipient for n in notifications)
        self.assertTrue(class1_students.issubset(notified_students))

    def test_teacher_cannot_notify_students_outside_assigned_classes(self):
        self.authenticate(self.teacher)
        url = '/api/notifications/'
        outsider = self.student3
        data = {
            'recipient_ids': [outsider.id],
            'notification_type': 'GENERAL',
            'template_id': self.teacher_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('recipient_ids', response.data)

    def test_student_can_notify_exactly_one_student_from_own_class(self):
        self.authenticate(self.student1)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student2.id],
            'notification_type': 'GENERAL',
            'template_id': self.student_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.first()
        self.assertEqual(notification.sender, self.student1)
        self.assertEqual(notification.recipient, self.student2)
        self.assertEqual(notification.title, self.student_template.title)
        self.assertEqual(notification.message, self.student_template.message)

    def test_student_cannot_notify_student_outside_own_class(self):
        self.authenticate(self.student1)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student3.id],
            'notification_type': 'GENERAL',
            'template_id': self.student_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('recipient_ids', response.data)

    def test_student_cannot_notify_multiple_recipients(self):
        self.authenticate(self.student1)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student2.id, self.student3.id],  # sending multiple recipients
            'notification_type': 'GENERAL',
            'template_id': self.student_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('recipient_ids', response.data)
        self.assertIn('exactly one student', str(response.data['recipient_ids']))

    def test_student_cannot_send_notification_within_one_hour(self):
        self.authenticate(self.student1)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student2.id],
            'notification_type': 'GENERAL',
            'template_id': self.student_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Attempt to send again immediately
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('recipient_ids', response2.data)
        self.assertIn('one notification per hour', str(response2.data['recipient_ids']))

        # Modify created_at to more than 1 hour ago and try again
        notification = Notification.objects.filter(sender=self.student1).latest('created_at')
        notification.created_at = timezone.now() - timedelta(hours=2)
        notification.save()

        response3 = self.client.post(url, data, format='json')
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_use_notification_template_not_allowed_for_role(self):
        self.authenticate(self.student1)
        url = '/api/notifications/'
        data = {
            'recipient_ids': [self.student2.id],
            'notification_type': 'GENERAL',
            'template_id': self.admin_template.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('template_id', response.data)

    def test_user_sees_only_own_notifications_from_previous_7_days_and_can_search(self):
        now = timezone.now()
        old_date = now - timedelta(days=8)
        old_notification = Notification.objects.create(
            sender=self.teacher,
            recipient=self.student1,
            title='Old notification',
            message='Old message',
            notification_type='GENERAL',
            is_read=False,
        )
        old_notification.created_at = old_date
        old_notification.save(update_fields=['created_at'])
        recent_notification = Notification.objects.create(
            sender=self.teacher,
            recipient=self.student1,
            title='Recent notification',
            message='Recent message',
            notification_type='GENERAL',
            is_read=False,
            created_at=now - timedelta(days=3),
        )
        other_notification = Notification.objects.create(
            sender=self.teacher,
            recipient=self.student2,
            title='Other student notification',
            message='Message for other student',
            notification_type='GENERAL',
            is_read=False,
            created_at=now - timedelta(days=1),
        )

        self.authenticate(self.student1)
        url = '/api/notifications/'

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data
        titles = [item['title'] for item in results]
        self.assertIn('Recent notification', titles)
        self.assertNotIn('Old notification', titles)
        self.assertNotIn('Other student notification', titles)

        response_search = self.client.get(url, {'search': 'Recent'})
        self.assertEqual(response_search.status_code, status.HTTP_200_OK)
        results_search = response_search.data
        titles_search = [item['title'] for item in results_search]
        self.assertIn('Recent notification', titles_search)
        self.assertNotIn('Old notification', titles_search)
        self.assertNotIn('Other student notification', titles_search)
