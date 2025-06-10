from django.db import models
from django.contrib.auth.models import User

class Ad(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Новый'),
        ('used', 'Б/у'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Активно'),
        ('exchanged', 'Обменяно'),
    ]
    
    CATEGORY_CHOICES = [
        ('electronics', 'Электроника'),
        ('appliances', 'Бытовая техника'),
        ('clothing', 'Одежда и обувь'),
        ('books', 'Книги'),
        ('sports', 'Спорт и отдых'),
        ('toys', 'Игрушки'),
        ('furniture', 'Мебель'),
        ('auto', 'Автотовары'),
        ('beauty', 'Красота и здоровье'),
        ('garden', 'Дача и сад'),
        ('other', 'Другое'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    image_url = models.ImageField(upload_to='ads/', null=True, blank=True, verbose_name='Изображение')
    category = models.CharField(
        max_length=100, 
        choices=CATEGORY_CHOICES,
        verbose_name='Категория'
    )
    condition = models.CharField(
        max_length=50, 
        choices=CONDITION_CHOICES,
        verbose_name='Состояние'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус объявления'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    exchanged_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата обмена')

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class ExchangeProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]
    
    ad_sender = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='sent_proposals')
    ad_receiver = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='received_proposals')
    comment = models.TextField(verbose_name='Комментарий')
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Предложение обмена'
        verbose_name_plural = 'Предложения обмена'
        ordering = ['-created_at']

    def __str__(self):
        return f'Обмен {self.ad_sender} на {self.ad_receiver}'
