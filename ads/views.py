from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from rest_framework import viewsets, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Ad, ExchangeProposal
from .serializers import AdSerializer, ExchangeProposalSerializer
from .forms import AdForm, ExchangeProposalForm, UserRegistrationForm, UserLoginForm



# Кастомное представление для входа
class CustomLoginView(LoginView):
    form_class = UserLoginForm
    template_name = 'registration/login.html'

# Веб-представления
def ad_list(request):
    try:
        # Показываем только активные объявления с валидными ID
        ads = Ad.objects.exclude(pk__isnull=True).filter(status='active')
        
        # Поиск
        search_query = request.GET.get('search', '')
        if search_query:
            ads = ads.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Фильтрация по категории
        category = request.GET.get('category', '')
        if category:
            ads = ads.filter(category=category)
        
        # Фильтрация по состоянию
        condition = request.GET.get('condition', '')
        if condition:
            ads = ads.filter(condition=condition)
        
        # Пагинация
        paginator = Paginator(ads, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'category_choices': Ad.CATEGORY_CHOICES,
            'condition_choices': Ad.CONDITION_CHOICES,
            'search_query': search_query,
            'selected_category': category,
            'selected_condition': condition,
        }
        return render(request, 'ads/ad_list.html', context)
    except Exception as e:
        print(f"Error in ad_list view: {str(e)}")
        return render(request, 'ads/ad_list.html', {
            'page_obj': [],
            'category_choices': Ad.CATEGORY_CHOICES,
            'condition_choices': Ad.CONDITION_CHOICES,
            'search_query': '',
            'selected_category': '',
            'selected_condition': '',
            'error': 'Произошла ошибка при загрузке объявлений'
        })


@login_required
def my_ads(request):
    # Определяем, какие объявления показывать (активные или обмененные)
    show_archived = request.GET.get('archived', False)
    
    if show_archived:
        ads = Ad.objects.filter(user=request.user, status='exchanged').order_by('-exchanged_at')
    else:
        ads = Ad.objects.filter(user=request.user, status='active').order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(ads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Счетчики для вкладок
    active_count = Ad.objects.filter(user=request.user, status='active').count()
    archived_count = Ad.objects.filter(user=request.user, status='exchanged').count()
    
    context = {
        'page_obj': page_obj,
        'show_archived': show_archived,
        'active_count': active_count,
        'archived_count': archived_count,
    }
    return render(request, 'ads/my_ads.html', context)


def ad_detail(request, pk):
    try:
        ad = get_object_or_404(Ad, pk=pk)
    except Http404:
        messages.error(request, 'Объявление не найдено.')
        return redirect('ad_list')
    
    user_ads = []
    if request.user.is_authenticated:
        # Показываем только активные объявления пользователя для обмена
        user_ads = Ad.objects.filter(user=request.user, status='active').exclude(pk=pk)
    
    context = {
        'ad': ad,
        'user_ads': user_ads,
    }
    return render(request, 'ads/ad_detail.html', context)


@login_required
def ad_create(request):
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ad = form.save(commit=False)
                ad.user = request.user
                ad.save()
                messages.success(request, 'Объявление успешно создано!')
                return redirect('ad_detail', pk=ad.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при создании объявления: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = AdForm()
    
    return render(request, 'ads/ad_form.html', {'form': form, 'title': 'Создать объявление'})

@login_required
def ad_edit(request, pk):
    try:
        ad = get_object_or_404(Ad, pk=pk)
        
        # Проверяем, является ли пользователь автором объявления
        if ad.user != request.user:
            messages.error(request, 'У вас нет прав для редактирования этого объявления.')
            return redirect('ad_detail', pk=pk)
            
    except Http404:
        messages.error(request, 'Объявление не найдено.')
        return redirect('ad_list')
    
    if request.method == 'POST':
        form = AdForm(request.POST, request.FILES, instance=ad)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Объявление успешно обновлено!')
                return redirect('ad_detail', pk=ad.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении объявления: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = AdForm(instance=ad)
    
    return render(request, 'ads/ad_form.html', {'form': form, 'title': 'Редактировать объявление'})

@login_required
def ad_delete(request, pk):
    try:
        ad = get_object_or_404(Ad, pk=pk)
        
        # Проверяем, является ли пользователь автором объявления
        if ad.user != request.user:
            messages.error(request, 'У вас нет прав для удаления этого объявления.')
            return redirect('ad_detail', pk=pk)
            
    except Http404:
        messages.error(request, 'Объявление не найдено.')
        return redirect('ad_list')
    
    if request.method == 'POST':
        try:
            ad_title = ad.title  # Сохраняем название для сообщения
            ad.delete()
            messages.success(request, f'Объявление "{ad_title}" успешно удалено!')
            return redirect('my_ads')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении объявления: {str(e)}')
            return redirect('ad_detail', pk=pk)
    
    return render(request, 'ads/ad_confirm_delete.html', {'ad': ad})

@login_required
def proposal_create(request, ad_id):
    try:
        ad_receiver = get_object_or_404(Ad, pk=ad_id)
        
        # Проверяем, что объявление активно
        if ad_receiver.status != 'active':
            messages.error(request, 'Это объявление уже обменяно и недоступно для новых предложений.')
            return redirect('ad_detail', pk=ad_id)
        
        # Проверяем, что пользователь не пытается создать предложение на свое объявление
        if ad_receiver.user == request.user:
            messages.error(request, 'Вы не можете создать предложение обмена на свое собственное объявление.')
            return redirect('ad_detail', pk=ad_id)
            
    except Http404:
        messages.error(request, 'Объявление не найдено.')
        return redirect('ad_list')
    
    # Получаем только активные объявления пользователя
    user_ads = Ad.objects.filter(user=request.user, status='active')
    
    if not user_ads.exists():
        messages.error(request, 'У вас нет активных объявлений для обмена. Создайте объявление сначала.')
        return redirect('ad_create')
    
    if request.method == 'POST':
        form = ExchangeProposalForm(request.POST)
        ad_sender_id = request.POST.get('ad_sender')
        
        if form.is_valid() and ad_sender_id:
            try:
                ad_sender = get_object_or_404(Ad, pk=ad_sender_id, user=request.user, status='active')
                
                # Проверяем, нет ли уже такого предложения
                existing_proposal = ExchangeProposal.objects.filter(
                    ad_sender=ad_sender,
                    ad_receiver=ad_receiver,
                    status='pending'
                ).first()
                
                if existing_proposal:
                    messages.warning(request, 'У вас уже есть активное предложение обмена для этих товаров.')
                    return redirect('ad_detail', pk=ad_id)
                
                proposal = form.save(commit=False)
                proposal.ad_sender = ad_sender
                proposal.ad_receiver = ad_receiver
                proposal.save()
                messages.success(request, 'Предложение обмена отправлено!')
                return redirect('ad_detail', pk=ad_id)
                
            except Http404:
                messages.error(request, 'Выбранное объявление не найдено или уже обменяно.')
            except Exception as e:
                messages.error(request, f'Ошибка при создании предложения: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, заполните все поля корректно.')
    else:
        form = ExchangeProposalForm()
    
    context = {
        'form': form,
        'ad_receiver': ad_receiver,
        'user_ads': user_ads,
    }
    return render(request, 'ads/proposal_form.html', context)



@login_required
def proposal_list(request):
    # Базовые запросы
    sent_proposals = ExchangeProposal.objects.filter(ad_sender__user=request.user)
    received_proposals = ExchangeProposal.objects.filter(ad_receiver__user=request.user)
    
    # Фильтрация отправленных предложений
    sent_status = request.GET.get('sent_status', '')  # Пустая строка вместо None
    sent_receiver = request.GET.get('sent_receiver', '')  # Пустая строка вместо None
    
    if sent_status:
        sent_proposals = sent_proposals.filter(status=sent_status)
    if sent_receiver:
        sent_proposals = sent_proposals.filter(ad_receiver__user__username__icontains=sent_receiver)
    
    # Фильтрация полученных предложений
    received_status = request.GET.get('received_status', '')  # Пустая строка вместо None
    received_sender = request.GET.get('received_sender', '')  # Пустая строка вместо None
    
    if received_status:
        received_proposals = received_proposals.filter(status=received_status)
    if received_sender:
        received_proposals = received_proposals.filter(ad_sender__user__username__icontains=received_sender)
    
    # Сортировка
    sent_proposals = sent_proposals.order_by('-created_at')
    received_proposals = received_proposals.order_by('-created_at')
    
    # Получаем уникальные значения для фильтров
    sent_receivers = ExchangeProposal.objects.filter(ad_sender__user=request.user).values_list('ad_receiver__user__username', flat=True).distinct()
    received_senders = ExchangeProposal.objects.filter(ad_receiver__user=request.user).values_list('ad_sender__user__username', flat=True).distinct()
    
    context = {
        'sent_proposals': sent_proposals,
        'received_proposals': received_proposals,
        'sent_receivers': sent_receivers,
        'received_senders': received_senders,
        'status_choices': ExchangeProposal.STATUS_CHOICES,
        # Сохраняем текущие фильтры для формы
        'sent_status': sent_status,
        'sent_receiver': sent_receiver,
        'received_status': received_status,
        'received_sender': received_sender,
    }
    return render(request, 'ads/proposal_list.html', context)


@login_required
def proposal_update_status(request, pk):
    try:
        proposal = get_object_or_404(ExchangeProposal, pk=pk)
        
        # Проверяем, является ли пользователь получателем предложения
        if proposal.ad_receiver.user != request.user:
            messages.error(request, 'У вас нет прав для изменения статуса этого предложения.')
            return redirect('proposal_list')
            
    except Http404:
        messages.error(request, 'Предложение обмена не найдено.')
        return redirect('proposal_list')
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(ExchangeProposal.STATUS_CHOICES):
            try:
                # Проверяем, можно ли изменить статус
                if proposal.status != 'pending':
                    messages.warning(request, 'Статус этого предложения уже был изменен.')
                    return redirect('proposal_list')
                
                proposal.status = status
                
                # Если предложение принято
                if status == 'accepted':
                    now = timezone.now()
                    # Обновляем статус обоих объявлений
                    proposal.ad_sender.status = 'exchanged'
                    proposal.ad_receiver.status = 'exchanged'
                    proposal.ad_sender.exchanged_at = now
                    proposal.ad_receiver.exchanged_at = now
                    
                    # Сохраняем изменения
                    proposal.ad_sender.save()
                    proposal.ad_receiver.save()
                    
                    messages.success(request, 'Предложение принято! Объявления помечены как обмененные.')
                    
                    # Отклоняем все остальные активные предложения для этих объявлений
                    ExchangeProposal.objects.filter(
                        Q(ad_sender=proposal.ad_sender) | 
                        Q(ad_receiver=proposal.ad_sender) |
                        Q(ad_sender=proposal.ad_receiver) | 
                        Q(ad_receiver=proposal.ad_receiver),
                        status='pending'
                    ).exclude(pk=proposal.pk).update(status='rejected')
                    
                elif status == 'rejected':
                    messages.success(request, 'Предложение отклонено.')
                    
                proposal.save()
                    
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении статуса: {str(e)}')
        else:
            messages.error(request, 'Неверный статус!')
    
    return redirect('proposal_list')

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Регистрация успешна! Добро пожаловать!')
                return redirect('ad_list')
            except Exception as e:
                messages.error(request, f'Ошибка при регистрации: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

# API представления (оставляем как есть)
class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category']
    ordering_fields = ['created_at', 'title']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        queryset = Ad.objects.all()
        category = self.request.query_params.get('category', None)
        condition = self.request.query_params.get('condition', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if condition:
            queryset = queryset.filter(condition=condition)
            
        return queryset

class ExchangeProposalViewSet(viewsets.ModelViewSet):
    queryset = ExchangeProposal.objects.all()
    serializer_class = ExchangeProposalSerializer
    
    def perform_create(self, serializer):
        ad_sender_id = self.request.data.get('ad_sender')
        ad_sender = get_object_or_404(Ad, id=ad_sender_id, user=self.request.user)
        serializer.save()
    
    def get_queryset(self):
        user = self.request.user
        return ExchangeProposal.objects.filter(
            Q(ad_sender__user=user) | Q(ad_receiver__user=user)
        )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        proposal = self.get_object()
        if proposal.ad_receiver.user != request.user:
            return Response({'error': 'Unauthorized'}, status=403)
            
        new_status = request.data.get('status')
        if new_status in dict(ExchangeProposal.STATUS_CHOICES):
            proposal.status = new_status
            proposal.save()
            return Response({'status': 'updated'})
        return Response({'error': 'Invalid status'}, status=400)

@login_required
def my_ads_archive(request):
    # Получаем все объявления пользователя (активные и обмененные)
    all_ads = Ad.objects.filter(user=request.user).order_by('-created_at')
    
    # Фильтрация по статусу
    status_filter = request.GET.get('status', '')
    if status_filter:
        all_ads = all_ads.filter(status=status_filter)
    
    # Пагинация
    paginator = Paginator(all_ads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    total_ads = Ad.objects.filter(user=request.user).count()
    active_ads = Ad.objects.filter(user=request.user, status='active').count()
    exchanged_ads = Ad.objects.filter(user=request.user, status='exchanged').count()
    
    context = {
        'page_obj': page_obj,
        'status_choices': Ad.STATUS_CHOICES,
        'selected_status': status_filter,
        'total_ads': total_ads,
        'active_ads': active_ads,
        'exchanged_ads': exchanged_ads,
    }
    return render(request, 'ads/my_ads_archive.html', context)
