from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Ad, ExchangeProposal
from django.utils import timezone

class AdTests(TestCase):
    def setUp(self):
        # Создаем тестовых пользователей
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.client = Client()
        
        # Создаем тестовое объявление
        self.ad = Ad.objects.create(
            user=self.user1,
            title='Тестовый товар',
            description='Описание тестового товара',
            category='electronics',
            condition='new',
            status='active'
        )

    def test_ad_creation(self):
        """Тест создания объявления"""
        self.client.login(username='user1', password='testpass123')
        
        data = {
            'title': 'Новый товар',
            'description': 'Описание нового товара',
            'category': 'books',
            'condition': 'used'
        }
        
        response = self.client.post(reverse('ad_create'), data)
        self.assertEqual(response.status_code, 302)  # Редирект после успешного создания
        self.assertTrue(Ad.objects.filter(title='Новый товар').exists())

    def test_ad_edit(self):
        """Тест редактирования объявления"""
        self.client.login(username='user1', password='testpass123')
        
        data = {
            'title': 'Измененный заголовок',
            'description': 'Измененное описание',
            'category': 'electronics',
            'condition': 'new'
        }
        
        response = self.client.post(reverse('ad_edit', kwargs={'pk': self.ad.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что данные обновились
        updated_ad = Ad.objects.get(pk=self.ad.pk)
        self.assertEqual(updated_ad.title, 'Измененный заголовок')

    def test_ad_delete(self):
        """Тест удаления объявления"""
        self.client.login(username='user1', password='testpass123')
        
        response = self.client.post(reverse('ad_delete', kwargs={'pk': self.ad.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Ad.objects.filter(pk=self.ad.pk).exists())

    def test_ad_search(self):
        """Тест поиска объявлений"""
        # Создаем тестовое объявление и явно указываем статус active
        ad = Ad.objects.create(
            user=self.user1,
            title='Тестовый поисковый товар',
            description='Описание тестового товара для поиска',
            category='electronics',
            condition='new',
            status='active'  # Явно указываем статус
        )
        
        response = self.client.get(reverse('ad_list') + '?search=поисковый')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовый поисковый товар')


    def test_unauthorized_access(self):
        """Тест доступа неавторизованного пользователя"""
        response = self.client.get(reverse('ad_create'))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_wrong_user_edit(self):
        """Тест попытки редактирования чужого объявления"""
        self.client.login(username='user2', password='testpass123')
        
        data = {
            'title': 'Попытка изменить чужое объявление',
            'description': 'Новое описание',
            'category': 'electronics',
            'condition': 'new'
        }
        
        response = self.client.post(reverse('ad_edit', kwargs={'pk': self.ad.pk}), data)
        self.assertEqual(response.status_code, 302)  # Редирект
        
        # Проверяем, что данные не изменились
        unchanged_ad = Ad.objects.get(pk=self.ad.pk)
        self.assertEqual(unchanged_ad.title, 'Тестовый товар')

class ExchangeProposalTests(TestCase):
    def setUp(self):
        # Создаем пользователей
        self.user1 = User.objects.create_user(username='user1', password='testpass123')
        self.user2 = User.objects.create_user(username='user2', password='testpass123')
        self.client = Client()
        
        # Создаем объявления
        self.ad1 = Ad.objects.create(
            user=self.user1,
            title='Товар 1',
            description='Описание товара 1',
            category='electronics',
            condition='new',
            status='active'
        )
        
        self.ad2 = Ad.objects.create(
            user=self.user2,
            title='Товар 2',
            description='Описание товара 2',
            category='books',
            condition='used',
            status='active'
        )

    def test_proposal_creation(self):
        """Тест создания предложения обмена"""
        self.client.login(username='user1', password='testpass123')
        
        data = {
            'ad_sender': self.ad1.pk,
            'comment': 'Предлагаю обмен'
        }
        
        response = self.client.post(reverse('proposal_create', kwargs={'ad_id': self.ad2.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ExchangeProposal.objects.filter(ad_sender=self.ad1, ad_receiver=self.ad2).exists())

    def test_proposal_accept(self):
        """Тест принятия предложения обмена"""
        # Создаем предложение
        proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            comment='Тестовое предложение',
            status='pending'
        )
        
        self.client.login(username='user2', password='testpass123')
        
        # Принимаем предложение
        response = self.client.post(reverse('proposal_update_status', kwargs={'pk': proposal.pk}), 
                                  {'status': 'accepted'})
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что статусы объявлений обновились
        self.ad1.refresh_from_db()
        self.ad2.refresh_from_db()
        self.assertEqual(self.ad1.status, 'exchanged')
        self.assertEqual(self.ad2.status, 'exchanged')

    def test_proposal_reject(self):
        """Тест отклонения предложения обмена"""
        proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            comment='Тестовое предложение',
            status='pending'
        )
        
        self.client.login(username='user2', password='testpass123')
        
        response = self.client.post(reverse('proposal_update_status', kwargs={'pk': proposal.pk}), 
                                  {'status': 'rejected'})
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что объявления остались активными
        self.ad1.refresh_from_db()
        self.ad2.refresh_from_db()
        self.assertEqual(self.ad1.status, 'active')
        self.assertEqual(self.ad2.status, 'active')

    def test_duplicate_proposal(self):
        """Тест создания дубликата предложения"""
        # Создаем первое предложение
        ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            comment='Первое предложение',
            status='pending'
        )
        
        self.client.login(username='user1', password='testpass123')
        
        # Пытаемся создать второе предложение
        data = {
            'ad_sender': self.ad1.pk,
            'comment': 'Второе предложение'
        }
        
        response = self.client.post(reverse('proposal_create', kwargs={'ad_id': self.ad2.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что создано только одно предложение
        self.assertEqual(ExchangeProposal.objects.filter(
            ad_sender=self.ad1, 
            ad_receiver=self.ad2
        ).count(), 1)

    def test_exchanged_ad_proposal(self):
        """Тест попытки создания предложения для обмененного объявления"""
        # Помечаем объявление как обмененное
        self.ad2.status = 'exchanged'
        self.ad2.exchanged_at = timezone.now()
        self.ad2.save()
        
        self.client.login(username='user1', password='testpass123')
        
        data = {
            'ad_sender': self.ad1.pk,
            'comment': 'Предложение обмена'
        }
        
        response = self.client.post(reverse('proposal_create', kwargs={'ad_id': self.ad2.pk}), data)
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что предложение не создано
        self.assertFalse(ExchangeProposal.objects.filter(
            ad_sender=self.ad1, 
            ad_receiver=self.ad2
        ).exists())
