from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Profile, Transaction, Product, Purchase, Group, AwardReason, CoinAward, ProductCategory, Parent, City, School, Course
# from decimal import Decimal - больше не нужен, используем int
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
from .forms import ParentForm, StudentParentLinkForm, CreateParentWithStudentForm, CityForm, SchoolForm, CourseForm, GroupForm, QuickCourseForm
import random

User = get_user_model()

# Список игровых фонов
GAME_BACKGROUNDS = [
    {
        'name': 'Standoff 2',
        'url': 'https://i.artfile.me/wallpaper/12-12-2022/1920x1080/video-igry-standoff-2-gorod-zdaniya-loka-1632196.jpg'
    },
    {
        'name': 'Dota 2',
        'url': 'https://pw.artfile.me/wallpaper/16-07-2017/650x366/video-igry-dota-2-dota-2-onlajn-action-r-1194082.jpg'
    },
    {
        'name': 'Steam',
        'url': 'https://steamcdn-a.akamaihd.net/steamcommunity/public/images/items/927890/9d24a13b19934ab0fd14228f74cbd6775984ac2f.jpg'
    },
    {
        'name': 'CS 2',
        'url': 'https://images.steamusercontent.com/ugc/2042997274847133077/8534B50A5A691EE7D3F1500E1CF03D41A37D03AC/?imw=5000&imh=5000&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=false'
    },
    {
        'name': 'Roblox',
        'url': 'https://abrakadabra.fun/uploads/posts/2022-03/1646887284_4-abrakadabra-fun-p-temi-dlya-robloksa-fon-7.jpg'
    }
]

@login_required
def dashboard(request):
    profile = Profile.objects.get_or_create(user=request.user)[0]
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')[:15]
    
    # Выбираем случайный фон при каждом входе
    random_background = random.choice(GAME_BACKGROUNDS)
    
    # Проверяем день рождения для учеников
    is_birthday = False
    birthday_coins_awarded = False
    
    if request.user.role == 'student' and request.user.birth_date:
        from datetime import date
        today = date.today()
        
        # Проверяем, сегодня ли день рождения (день и месяц)
        if (today.day == request.user.birth_date.day and 
            today.month == request.user.birth_date.month):
            is_birthday = True
            
            # Проверяем, были ли уже начислены монеты за этот день рождения
            birthday_award_today = Transaction.objects.filter(
                receiver=request.user,
                transaction_type='EARN',
                description__icontains='день рождения',
                created_at__date=today
            ).exists()
            
            # Если монеты еще не начислены - начисляем автоматически
            if not birthday_award_today:
                try:
                    # Начисляем 100 астрокоинов
                    profile.astrocoins += 100
                    profile.save()
                    
                    # Создаем запись о транзакции
                    Transaction.objects.create(
                        receiver=request.user,
                        amount=100,
                        transaction_type='EARN',
                        description=f'🎉 Поздравляем с днём рождения! Подарок от Астро-Маркета'
                    )
                    
                    birthday_coins_awarded = True
                    messages.success(request, '🎉 С днём рождения! Вам начислено 100 астрокоинов в подарок!')
                    
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Ошибка при начислении монет за день рождения пользователю {request.user.username}: {str(e)}')
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'background_image': random_background['url'],
        'background_name': random_background['name'],
        'is_birthday': is_birthday,
        'birthday_coins_awarded': birthday_coins_awarded,
    }
    return render(request, 'core/dashboard.html', context)

from django.core.exceptions import PermissionDenied

@login_required
def shop(request):
    # Проверяем, что пользователь не является преподавателем
    if request.user.is_teacher() and not request.user.is_superuser:
        raise PermissionDenied("Преподаватели не могут совершать покупки в магазине")
    
    # Получаем категории в зависимости от роли
    if hasattr(request.user, 'city') and request.user.city:
        # Показываем только категории из города пользователя
        categories = ProductCategory.objects.filter(city=request.user.city).order_by('order')
    else:
        # Если у пользователя нет города (главный суперадмин) - видит все
        categories = ProductCategory.objects.all().order_by('order')
    
    # Фильтруем товары в каждой категории по городу пользователя
    for category in categories:
        # Товары уже привязаны к тому же городу что и категория
        category.filtered_products = category.products.filter(
            city=category.city
        ).order_by('-featured', '-created_at')
    
    # Убираем категории без товаров ТОЛЬКО для учеников
    # Администраторы должны видеть все категории, чтобы добавлять в них товары
    if request.user.role == 'student':
        categories = [cat for cat in categories if cat.filtered_products.exists()]
    
    # Добавляем случайный фон и для магазина
    random_background = random.choice(GAME_BACKGROUNDS)
    
    context = {
        'categories': categories,
        'background_image': random_background['url'],
        'background_name': random_background['name'],
    }
    
    return render(request, 'core/shop.html', context)

@login_required
def add_product(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администраторы могут добавлять товары")
    
    if request.method == 'POST':
        try:
            # Автоматически привязываем к городу администратора
            city = request.user.city if hasattr(request.user, 'city') and request.user.city else None
            if not city and not request.user.is_superuser:
                raise Exception("У администратора не указан город")
            
            product = Product.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                stock=request.POST['stock'],
                category_id=request.POST['category'],
                city=city,  # Автоматически привязываем к городу
                is_digital=request.POST.get('is_digital', False) == 'on',
                featured=request.POST.get('featured', False) == 'on'
            )
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            city_name = city.name if city else "без города"
            messages.success(request, f'Товар "{product.name}" успешно добавлен в город: {city_name}')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')
        
        return redirect('shop')

@login_required
def edit_product(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администраторы могут редактировать товары")
    
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=request.POST['product_id'])
            
            # Проверяем права доступа - администратор может редактировать только товары своего города
            if (request.user.role == 'city_admin' and 
                hasattr(request.user, 'city') and request.user.city and 
                product.city != request.user.city):
                raise PermissionDenied("Вы можете редактировать только товары своего города")
            
            product.name = request.POST['name']
            product.description = request.POST['description']
            product.price = request.POST['price']
            product.stock = request.POST['stock']
            product.category_id = request.POST['category']
            product.is_digital = request.POST.get('is_digital', False) == 'on'
            product.featured = request.POST.get('featured', False) == 'on'
            
            # Город товара не изменяется - он привязан к городу администратора
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            city_name = product.city.name if product.city else "без города"
            messages.success(request, f'Товар "{product.name}" успешно обновлен в городе: {city_name}')
        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден')
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении товара: {str(e)}')
        
        return redirect('shop')

@login_required
def get_product(request, product_id):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администраторы могут получать данные товаров")
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Проверяем права доступа - администратор может получать только товары своего города
        if (request.user.role == 'city_admin' and 
            hasattr(request.user, 'city') and request.user.city and 
            product.city != request.user.city):
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': str(product.price),
            'stock': product.stock,
            'category': product.category_id if product.category else None,
            'is_digital': product.is_digital,
            'featured': product.featured,
            'city': product.city.id if product.city else None,  # ID города товара
            'city_name': product.city.name if product.city else 'Без города'  # Название города
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Товар не найден'}, status=404)

@login_required
def delete_product(request, product_id):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может удалять товары")
    
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            name = product.name
            product.delete()
            messages.success(request, f'Товар "{name}" успешно удален')
        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении товара: {str(e)}')
        
        return JsonResponse({'status': 'ok'})

@login_required
def purchase_product(request, product_id):
    if request.method != 'POST':
        return redirect('shop')
    
    # Проверяем, что пользователь не учитель (только ученики могут покупать)
    if request.user.is_teacher() and not request.user.is_superuser:
        messages.error(request, 'Преподаватели не могут совершать покупки в магазине!')
        return redirect('shop')
    
    # Дополнительная валидация product_id
    try:
        product_id = int(product_id)
        if product_id <= 0:
            raise ValueError("Invalid product ID")
    except (ValueError, TypeError):
        messages.error(request, 'Некорректный ID товара!')
        return redirect('shop')
    
    product = get_object_or_404(Product, id=product_id, available=True)
    
    # Проверяем доступность товара в городе ученика
    if request.user.is_student() and request.user.city:
        if product.city != request.user.city:
            messages.error(request, 'Этот товар недоступен в вашем городе!')
            return redirect('shop')
    
    # Проверяем наличие товара на складе
    if product.stock <= 0:
        messages.error(request, 'Товар закончился на складе!')
        return redirect('shop')
    
    profile = Profile.objects.get(user=request.user)
    
    # Дополнительная валидация цены
    if product.price <= 0:
        messages.error(request, 'Некорректная цена товара!')
        return redirect('shop')
    
    if profile.astrocoins < product.price:
        messages.error(request, 'Недостаточно AstroCoins для покупки!')
        return redirect('shop')
    
    # Используем транзакцию базы данных для атомарности
    with transaction.atomic():
        # Повторно проверяем наличие и блокируем товар
        product = Product.objects.select_for_update().get(id=product_id, available=True)
        
        if product.stock <= 0:
            messages.error(request, 'Товар закончился на складе!')
            return redirect('shop')
        
        # Повторно проверяем баланс пользователя
        profile = Profile.objects.select_for_update().get(user=request.user)
        
        if profile.astrocoins < product.price:
            messages.error(request, 'Недостаточно AstroCoins для покупки!')
            return redirect('shop')
        
        # Создаем транзакцию покупки
        Purchase.objects.create(
            user=request.user,
            product=product,
            total_price=product.price
        )
        
        # Списываем AstroCoins
        profile.astrocoins -= product.price
        profile.save()
        
        # Уменьшаем количество товара на складе
        product.stock -= 1
        product.save()
        
        # Записываем транзакцию
        Transaction.objects.create(
            sender=request.user,
            receiver=request.user,  # В случае покупки отправитель и получатель совпадают
            amount=product.price,
            transaction_type='SPEND',
            description=f'Покупка {product.name}'
        )
    
    messages.success(request, f'Вы успешно приобрели {product.name}!')
    return redirect('shop')

from django.http import JsonResponse
from django.db import transaction
from django.template.loader import render_to_string

@login_required
def transfer_coins(request):
    if request.method == 'POST':
        receiver_username = request.POST.get('receiver')
        amount = int(request.POST.get('amount', 0))
        
        try:
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Сумма перевода должна быть положительной!'})
            
            if amount < 20:
                return JsonResponse({'success': False, 'error': 'Минимальная сумма перевода: 20 AC'})
            
            with transaction.atomic():
                receiver = User.objects.select_for_update().get(username=receiver_username)
                sender_profile = Profile.objects.select_for_update().get(user=request.user)
                receiver_profile = Profile.objects.select_for_update().get(user=receiver)
                
                if receiver == request.user:
                    return JsonResponse({'success': False, 'error': 'Нельзя переводить AstroCoins самому себе!'})
                
                # Рассчитываем комиссию 5% за перевод
                commission = int(amount * 0.05)  # 5% комиссия, округляем до целого
                total_cost = amount + commission  # Общая сумма к списанию
                
                if sender_profile.astrocoins < total_cost:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Недостаточно AstroCoins! Нужно {total_cost} AC (перевод {amount} AC + комиссия {commission} AC)'
                    })
                
                # Выполняем перевод с комиссией
                sender_profile.astrocoins -= total_cost  # Списываем сумму + комиссию
                receiver_profile.astrocoins += amount    # Получатель получает только основную сумму
                
                sender_profile.save()
                receiver_profile.save()
                
                # Записываем транзакцию для отправителя (с комиссией)
                Transaction.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    amount=total_cost,
                    transaction_type='TRANSFER',
                    description=f'Перевод к {receiver_username} ({amount} AC + комиссия {commission} AC)'
                )
                
                # Записываем транзакцию для получателя (без комиссии)
                Transaction.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    amount=amount,
                    transaction_type='TRANSFER',
                    description=f'Перевод от {request.user.username}'
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Создаем HTML для новой транзакции
                    transaction_html = render_to_string('core/transaction_item.html', {
                        'transaction': Transaction.objects.filter(
                            Q(sender=request.user) | Q(receiver=request.user)
                        ).latest('created_at'),
                        'user': request.user
                    })
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Успешно переведено {amount} AC пользователю {receiver_username}! Комиссия: {commission} AC',
                        'new_balance': str(sender_profile.astrocoins),
                        'transaction_html': transaction_html
                    })
                else:
                    messages.success(request, f'Успешно переведено {amount} AC пользователю {receiver_username}! Списано: {total_cost} AC (включая комиссию {commission} AC)')
                    return redirect('dashboard')
                
        except User.DoesNotExist:
            error_message = 'Получатель не найден!'
        except Exception as e:
            error_message = 'Произошла ошибка при переводе!'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_message})
        else:
            messages.error(request, error_message)
            return redirect('dashboard')
            
    return redirect('dashboard')

@login_required
def profile(request):
    profile = Profile.objects.get(user=request.user)
    transactions = Transaction.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')
    purchases = Purchase.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагинация для транзакций
    transactions_paginator = Paginator(transactions, 10)
    transactions_page = request.GET.get('transactions_page')
    transactions = transactions_paginator.get_page(transactions_page)
    
    # Пагинация для покупок
    purchases_paginator = Paginator(purchases, 10)
    purchases_page = request.GET.get('purchases_page')
    purchases = purchases_paginator.get_page(purchases_page)
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'purchases': purchases,
    }
    return render(request, 'core/profile.html', context)

@login_required
def profile_edit(request, user_id=None):
    # Определяем, редактирует ли пользователь свой профиль
    is_own_profile = user_id is None
    
    # Если user_id не указан, значит пользователь пытается редактировать свой профиль
    if user_id is None:
        # Любой пользователь может редактировать свой профиль
        user_to_edit = request.user
    else:
        # Проверяем права на редактирование чужого профиля
        if not request.user.is_teacher():
            messages.error(request, 'У вас нет прав на редактирование профилей')
            return redirect('profile')
        
        user_to_edit = get_object_or_404(User, id=user_id)
        
        # Учитель может редактировать только своих учеников
        if not request.user.is_superuser and (
            not user_to_edit.is_student() or 
            (user_to_edit.group and user_to_edit.group.teacher != request.user)
        ):
            messages.error(request, 'Вы можете редактировать только своих учеников')
            return redirect('profile')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            try:
                # Обновление основной информации
                user_to_edit.first_name = request.POST.get('first_name', '')
                user_to_edit.last_name = request.POST.get('last_name', '')
                user_to_edit.email = request.POST.get('email', '')
                
                # Смена города (только для администраторов городов)
                if user_to_edit.role == 'city_admin' and is_own_profile:
                    new_city_id = request.POST.get('city')
                    
                    # Приводим к int для корректного сравнения
                    try:
                        new_city_id = int(new_city_id) if new_city_id else None
                    except (ValueError, TypeError):
                        new_city_id = None
                    
                    current_city_id = user_to_edit.city.id if user_to_edit.city else None
                    
                    # Проверяем, изменился ли город
                    if new_city_id and new_city_id != current_city_id:
                        try:
                            new_city = City.objects.get(id=new_city_id)
                            old_city_name = user_to_edit.city.name if user_to_edit.city else 'Не указан'
                            user_to_edit.city = new_city
                            
                            messages.warning(request, 
                                f'Город изменен с "{old_city_name}" на "{new_city.name}". '
                                f'ВНИМАНИЕ: Теперь вы будете видеть только данные нового города: '
                                f'учеников, товары, категории, группы. Доступ к данным прежнего города будет утерян.')
                        except City.DoesNotExist:
                            messages.error(request, 'Выбранный город не найден')
                            return redirect('profile_edit')
                
                user_to_edit.save()
                messages.success(request, 'Профиль успешно обновлен!')
                
            except Exception as e:
                # Логируем ошибку и показываем пользователю понятное сообщение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Ошибка при обновлении профиля пользователя {user_to_edit.username}: {str(e)}')
                messages.error(request, f'Произошла ошибка при сохранении профиля: {str(e)}')
                return redirect('profile_edit')
            
        elif action == 'change_password':
            # Смена пароля
            new_password = request.POST.get('new_password')
            if new_password:
                user_to_edit.set_password(new_password)
                user_to_edit.save()
                messages.success(request, 'Пароль успешно изменен!')
            else:
                messages.error(request, 'Новый пароль не может быть пустым')
        
        if user_id is None:
            # Если редактируем свой профиль - перенаправляем на свой профиль
            return redirect('profile')
        else:
            # Если редактируем чужой профиль - перенаправляем на профиль студента
            return redirect('student_profile', student_id=user_id)

    context = {
        'user_to_edit': user_to_edit,
        'is_own_profile': is_own_profile,
        'cities': City.objects.all().order_by('name'),  # Для выбора города
    }
    return render(request, 'core/profile_edit.html', context)

@login_required
def knowledge_base(request):
    return render(request, 'core/knowledge_base.html')

# Страницы футера
def institutions(request):
    """Страница с контактными данными учреждений"""
    return render(request, 'core/footer/institutions.html')

def return_policy(request):
    """Страница с условиями возврата"""
    return render(request, 'core/footer/return_policy.html')

def data_transfer(request):
    """Страница с описанием процесса передачи данных"""
    return render(request, 'core/footer/data_transfer.html')

def privacy_policy(request):
    """Страница с политикой конфиденциальности"""
    return render(request, 'core/footer/privacy_policy.html')

def support(request):
    """Страница технической поддержки"""
    return render(request, 'core/footer/support.html')

def astrocoins_program(request):
    """Страница бонусной программы Астрокоины"""
    return render(request, 'core/footer/astrocoins_program.html')

def changelog(request):
    """Страница истории изменений"""
    return render(request, 'core/footer/changelog.html')

@login_required
def groups(request):
    context = {}
    
    if request.user.is_teacher():
        # Для преподавателя и администратора показываем группы в зависимости от роли
        from django.db.models import Q
        
        if request.user.role == 'city_admin' and hasattr(request.user, 'city') and request.user.city:
            # Администратор города видит ВСЕ группы своего города (независимо от того, кто учитель/куратор)
            groups = Group.objects.filter(
                school__city=request.user.city
            ).select_related('course', 'school', 'curator', 'teacher').distinct()
        else:
            # Обычный преподаватель видит только свои группы и где он куратор
            groups = Group.objects.filter(
                Q(teacher=request.user) | Q(curator=request.user)
            ).select_related('course', 'school', 'curator').distinct()
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'create_group':
                form = GroupForm(request.POST)
                if form.is_valid():
                    try:
                        group = form.save(commit=False)
                        # Если администратор не выбрал учителя, устанавливаем его самого
                        if not group.teacher:
                            group.teacher = request.user
                        group.save()
                        
                        teacher_name = group.teacher.get_full_name() or group.teacher.username
                        curator_info = ""
                        if group.curator:
                            curator_name = group.curator.get_full_name() or group.curator.username
                            curator_info = f", куратор: {curator_name}"
                        
                        messages.success(request, f'Группа "{group.name}" успешно создана (преподаватель: {teacher_name}{curator_info})')
                    except Exception as e:
                        messages.error(request, f'Ошибка при создании группы: {str(e)}')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f'{form.fields[field].label}: {error}')
            
            elif action == 'award_coins':
                student_id = request.POST.get('student_id')
                amount = int(request.POST.get('amount', 0))
                reason = request.POST.get('reason', '')
                
                try:
                    student = User.objects.get(id=student_id, role='student')
                    student_profile = Profile.objects.get(user=student)
                    
                    # Начисляем AstroCoins
                    student_profile.astrocoins += amount
                    student_profile.save()
                    
                    # Создаем транзакцию
                    Transaction.objects.create(
                        sender=request.user,
                        receiver=student,
                        amount=amount,
                        transaction_type='EARN',
                        description=f'Награда от преподавателя: {reason}'
                    )
                    
                    messages.success(request, f'Успешно начислено {amount} AstroCoins ученику {student.username}')
                except User.DoesNotExist:
                    messages.error(request, 'Ученик не найден')
                except Exception as e:
                    messages.error(request, 'Произошла ошибка при начислении AstroCoins')
            
            elif action == 'award_group':
                # Начисление астрокоинов всей группе
                group_id = request.POST.get('group_id')
                reason_id = request.POST.get('reason_id')
                comment = request.POST.get('comment', '')
                
                try:
                    group = Group.objects.get(id=group_id)
                    reason = AwardReason.objects.get(id=reason_id)
                    
                    # Проверяем права доступа
                    if not (request.user.is_superuser or group.teacher == request.user):
                        messages.error(request, 'У вас нет прав для начисления астрокоинов этой группе')
                        return redirect('groups')
                    
                    # Получаем всех учеников группы
                    students = group.students.filter(role='student')
                    
                    if not students.exists():
                        messages.warning(request, 'В группе нет учеников для начисления')
                        return redirect('groups')
                    
                    # Начисляем астрокоины каждому ученику
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    awards_count = 0
                    for student in students:
                        try:
                            logger.info(f"Групповое начисление: student_id={student.id}, teacher_id={request.user.id}, reason_id={reason.id}, amount={reason.coins}")
                            
                            award = CoinAward.objects.create(
                                student=student,
                                teacher=request.user,
                                reason=reason,
                                amount=reason.coins,
                                comment=comment
                            )
                            awards_count += 1
                            logger.info(f"Групповая награда создана: award_id={award.id} для student_id={student.id}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка при групповом начислении для student_id={student.id}: {e}")
                            messages.error(request, f'Ошибка при начислении ученику {student.get_full_name() or student.username}: {str(e)}')
                    
                    messages.success(request, f'Успешно начислено {reason.coins} AC каждому из {awards_count} учеников группы "{group.name}"')
                    
                except Group.DoesNotExist:
                    messages.error(request, 'Группа не найдена')
                except AwardReason.DoesNotExist:
                    messages.error(request, 'Причина начисления не найдена')
                except Exception as e:
                    messages.error(request, f'Произошла ошибка при начислении: {str(e)}')
            
            elif action == 'award_student':
                # Начисление астрокоинов индивидуальному ученику
                student_id = request.POST.get('student_id')
                reason_id = request.POST.get('reason_id')
                comment = request.POST.get('comment', '')
                
                try:
                    student = User.objects.get(id=student_id, role='student')
                    reason = AwardReason.objects.get(id=reason_id)
                    
                    # Проверяем права доступа
                    if not (request.user.is_superuser or 
                           (student.group and student.group.teacher == request.user)):
                        messages.error(request, 'У вас нет прав для начисления астрокоинов этому ученику')
                        return redirect('groups')
                    
                    # Создаем награду
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    try:
                        logger.info(f"Создание награды: student_id={student.id}, teacher_id={request.user.id}, reason_id={reason.id}, amount={reason.coins}")
                        
                        award = CoinAward.objects.create(
                            student=student,
                            teacher=request.user,
                            reason=reason,
                            amount=reason.coins,
                            comment=comment
                        )
                        
                        logger.info(f"Награда создана успешно: award_id={award.id}")
                        messages.success(request, f'Успешно начислено {reason.coins} AC ученику {student.get_full_name() or student.username}')
                        
                    except Exception as e:
                        logger.error(f"Ошибка при создании награды: {e}")
                        messages.error(request, f'Ошибка при начислении: {str(e)}')
                    
                except User.DoesNotExist:
                    messages.error(request, 'Ученик не найден')
                except AwardReason.DoesNotExist:
                    messages.error(request, 'Причина начисления не найдена')
                except Exception as e:
                    messages.error(request, f'Произошла ошибка при начислении: {str(e)}')
            
            elif action == 'add_student_to_group':
                # Добавление ученика в группу (только для администраторов)
                if request.user.is_superuser:
                    student_id = request.POST.get('student_id')
                    group_id = request.POST.get('group_id')
                    
                    try:
                        student = User.objects.get(id=student_id, role='student')
                        group = Group.objects.get(id=group_id)
                        
                        # Проверяем что администратор города может работать только с учениками своего города
                        if (hasattr(request.user, 'city') and request.user.city and 
                            request.user.role == 'city_admin' and 
                            student.city != request.user.city):
                            messages.error(request, f'Вы можете добавлять только учеников из вашего города ({request.user.city.name})')
                            return redirect('groups')
                        
                        # Проверяем что ученик еще не в группе
                        if student.group:
                            messages.warning(request, f'Ученик {student.get_full_name() or student.username} уже состоит в группе "{student.group.name}"')
                        else:
                            student.group = group
                            student.save()
                            messages.success(request, f'Ученик {student.get_full_name() or student.username} добавлен в группу "{group.name}"')
                    
                    except User.DoesNotExist:
                        messages.error(request, 'Ученик не найден')
                    except Group.DoesNotExist:
                        messages.error(request, 'Группа не найдена')
                    except Exception as e:
                        messages.error(request, f'Ошибка при добавлении ученика в группу: {str(e)}')
                else:
                    messages.error(request, 'Недостаточно прав для добавления учеников в группу')
            
            elif action == 'remove_student_from_group':
                # Удаление ученика из группы (только для администраторов)
                if request.user.is_superuser:
                    student_id = request.POST.get('student_id')
                    
                    try:
                        student = User.objects.get(id=student_id, role='student')
                        
                        # Проверяем что администратор города может работать только с учениками своего города
                        if (hasattr(request.user, 'city') and request.user.city and 
                            request.user.role == 'city_admin' and 
                            student.city != request.user.city):
                            messages.error(request, f'Вы можете управлять только учениками из вашего города ({request.user.city.name})')
                            return redirect('groups')
                        
                        group_name = student.group.name if student.group else 'Без группы'
                        
                        student.group = None
                        student.save()
                        messages.success(request, f'Ученик {student.get_full_name() or student.username} удален из группы "{group_name}"')
                    
                    except User.DoesNotExist:
                        messages.error(request, 'Ученик не найден')
                    except Exception as e:
                        messages.error(request, f'Ошибка при удалении ученика из группы: {str(e)}')
                else:
                    messages.error(request, 'Недостаточно прав для удаления учеников из группы')
        
        # Получаем шаблоны начислений для учителей
        award_reasons = AwardReason.objects.all().order_by('coins')
        
        context.update({
            'groups': groups,
            'award_reasons': award_reasons,
            'is_teacher': True,
            'is_superuser': request.user.is_superuser,
            'group_form': GroupForm(),
            'cities': City.objects.all().order_by('name'),
            'schools': School.objects.all().order_by('city__name', 'name'),
            'courses': Course.objects.filter(is_active=True).order_by('school__name', 'name'),
        })
        
        # Для администраторов добавляем список учеников для управления группами
        if request.user.is_superuser:
            # Фильтруем учеников по городу администратора
            students_query = User.objects.filter(role='student').select_related('group')
            students_without_group_query = User.objects.filter(role='student', group=None)
            
            # Если у администратора есть город, показываем только учеников этого города
            if hasattr(request.user, 'city') and request.user.city and request.user.role == 'city_admin':
                students_query = students_query.filter(city=request.user.city)
                students_without_group_query = students_without_group_query.filter(city=request.user.city)
            
            context.update({
                'all_students': students_query.order_by('username'),
                'students_without_group': students_without_group_query.order_by('username'),
            })
    else:
        # Для ученика показываем его группу и статистику
        if request.user.group:
            context.update({
                'group': request.user.group,
                'classmates': request.user.group.students.exclude(id=request.user.id),
                'is_teacher': False
            })
    
    return render(request, 'core/groups.html', context)

@login_required
def news(request):
    return render(request, 'core/news.html')

@login_required
def manage_coins(request, student_id):
    if not request.user.is_teacher():
        raise PermissionDenied("Только преподаватели могут управлять астрокоинами")
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Проверяем, что студент находится в группе преподавателя
    if not request.user.is_superuser and student.group.teacher != request.user:
        raise PermissionDenied("Вы можете управлять астрокоинами только своих учеников")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'award':
            reason_id = request.POST.get('reason')
            comment = request.POST.get('comment', '')
            
            # Дополнительная валидация входных данных
            try:
                reason_id = int(reason_id)
                if reason_id <= 0:
                    raise ValueError("Invalid reason ID")
            except (ValueError, TypeError):
                messages.error(request, 'Некорректная причина начисления!')
                return redirect('manage_coins', student_id=student_id)
            
            # Валидация комментария
            if len(comment) > 500:
                messages.error(request, 'Комментарий слишком длинный (максимум 500 символов)!')
                return redirect('manage_coins', student_id=student_id)
            
            try:
                reason = AwardReason.objects.get(id=reason_id)
                
                # Проверяем разумность суммы начисления
                if reason.coins <= 0:
                    messages.error(request, 'Некорректная сумма для начисления!')
                    return redirect('manage_coins', student_id=student_id)
                
                if reason.coins > 1000:  # Ограничение на максимальную сумму
                    messages.error(request, 'Слишком большая сумма для одного начисления!')
                    return redirect('manage_coins', student_id=student_id)
                
                # Проверяем ограничение по времени
                if reason.cooldown_days > 0:
                    last_award = CoinAward.objects.filter(
                        student=student,
                        reason=reason,
                        created_at__gte=timezone.now() - timedelta(days=reason.cooldown_days)
                    ).first()
                    
                    if last_award:
                        messages.error(request, f'Эту награду можно выдать только раз в {reason.cooldown_days} дней')
                        return redirect('manage_coins', student_id=student_id)
                
                # Проверяем лимит начислений в день (защита от спама)
                today_awards = CoinAward.objects.filter(
                    student=student,
                    teacher=request.user,
                    created_at__date=timezone.now().date()
                ).count()
                
                if today_awards >= 10:  # Максимум 10 начислений в день от одного учителя
                    messages.error(request, 'Превышен дневной лимит начислений для этого ученика!')
                    return redirect('manage_coins', student_id=student_id)
                
                # Используем транзакцию базы данных для атомарности
                with transaction.atomic():
                    award = CoinAward.objects.create(
                        student=student,
                        teacher=request.user,
                        reason=reason,
                        amount=reason.coins,
                        comment=comment
                    )
                    messages.success(request, f'Начислено {reason.coins} AC ученику {student.get_full_name() or student.username}')
                
            except AwardReason.DoesNotExist:
                messages.error(request, 'Причина не найдена')
            except Exception as e:
                messages.error(request, f'Ошибка при начислении: {str(e)}')
        
        elif action == 'delete_award':
            award_id = request.POST.get('award_id')
            try:
                award = CoinAward.objects.get(id=award_id)
                
                # Проверяем права на удаление
                if not request.user.is_superuser and award.teacher != request.user:
                    raise PermissionDenied("Вы можете удалять только свои начисления")
                
                award.delete()
                messages.success(request, 'Начисление успешно удалено')
            except CoinAward.DoesNotExist:
                messages.error(request, 'Начисление не найдено')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении: {str(e)}')
    
    # Получаем историю начислений
    awards = CoinAward.objects.filter(student=student).order_by('-created_at')
    reasons = AwardReason.objects.all()
    
    context = {
        'student': student,
        'awards': awards,
        'reasons': reasons,
    }
    return render(request, 'core/manage_coins.html', context)

@login_required
def student_profile(request, student_id):
    if not request.user.is_teacher():
        raise PermissionDenied("Только преподаватели могут просматривать профили учеников")
    
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Проверяем, что студент находится в группе преподавателя
    if not request.user.is_superuser and student.group.teacher != request.user:
        raise PermissionDenied("Вы можете просматривать только своих учеников")
    
    transactions = Transaction.objects.filter(
        Q(sender=student) | Q(receiver=student)
    ).order_by('-created_at')
    
    purchases = Purchase.objects.filter(user=student).order_by('-created_at')
    awards = CoinAward.objects.filter(student=student).order_by('-created_at')
    
    context = {
        'student': student,
        'transactions': transactions,
        'purchases': purchases,
        'awards': awards,
    }
    return render(request, 'core/student_profile.html', context)

@login_required
def activity_monitoring(request):
    """Мониторинг активности учеников (покупки и переводы)"""
    if not (request.user.is_teacher() or request.user.is_superuser):
        raise PermissionDenied("Только преподаватели и администраторы могут просматривать активность")
    
    # Получаем параметры фильтрации
    group_filter = request.GET.get('group_filter', '')
    hide_delivered = request.GET.get('hide_delivered', '') == 'on'
    
    # Определяем какие пользователи доступны для просмотра
    if request.user.is_superuser:
        if request.user.role == 'city_admin' and hasattr(request.user, 'city') and request.user.city:
            # Администратор города видит данные только своего города
            available_users = User.objects.filter(role='student', city=request.user.city).select_related('profile', 'group')
            purchases = Purchase.objects.filter(user__city=request.user.city).select_related('user', 'product', 'user__profile', 'user__group')
            transfers = Transaction.objects.filter(
                transaction_type='TRANSFER'
            ).filter(
                Q(sender__city=request.user.city) | Q(receiver__city=request.user.city)
            ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile', 'sender__group', 'receiver__group')
            available_groups = Group.objects.filter(school__city=request.user.city).order_by('name')
        else:
            # Главный суперадмин видит всех
            available_users = User.objects.filter(role='student').select_related('profile', 'group')
            purchases = Purchase.objects.all().select_related('user', 'product', 'user__profile', 'user__group')
            transfers = Transaction.objects.filter(transaction_type='TRANSFER').select_related('sender', 'receiver', 'sender__profile', 'receiver__profile', 'sender__group', 'receiver__group')
            available_groups = Group.objects.all().order_by('name')
    else:
        # Обычный учитель видит только своих учеников
        available_users = User.objects.filter(role='student', group__teacher=request.user).select_related('profile', 'group')
        purchases = Purchase.objects.filter(user__group__teacher=request.user).select_related('user', 'product', 'user__profile', 'user__group')
        transfers = Transaction.objects.filter(
            transaction_type='TRANSFER'
        ).filter(
            Q(sender__group__teacher=request.user) | Q(receiver__group__teacher=request.user)
        ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile', 'sender__group', 'receiver__group')
        available_groups = Group.objects.filter(teacher=request.user).order_by('name')
    
    # Применяем фильтр по группе
    if group_filter:
        purchases = purchases.filter(user__group_id=group_filter)
        transfers = transfers.filter(
            Q(sender__group_id=group_filter) | Q(receiver__group_id=group_filter)
        )
    
    # Фильтр для скрытия выданных товаров
    if hide_delivered:
        purchases = purchases.filter(delivered=False)
    
    # Сортировка по дате
    purchases = purchases.order_by('-created_at')
    transfers = transfers.order_by('-created_at')
    
    # Пагинация для покупок
    purchases_paginator = Paginator(purchases, 20)
    purchases_page = request.GET.get('purchases_page')
    purchases = purchases_paginator.get_page(purchases_page)
    
    # Пагинация для переводов
    transfers_paginator = Paginator(transfers, 20)
    transfers_page = request.GET.get('transfers_page')
    transfers = transfers_paginator.get_page(transfers_page)
    
    context = {
        'available_users': available_users,
        'available_groups': available_groups,
        'purchases': purchases,
        'transfers': transfers,
        'is_superuser': request.user.is_superuser,
        'group_filter': group_filter,
        'hide_delivered': hide_delivered,
    }
    return render(request, 'core/activity_monitoring.html', context)

@login_required
def mark_purchase_delivered(request, purchase_id):
    """API endpoint для отметки товара как выданного"""
    if not (request.user.is_superuser or request.user.is_teacher()):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'})
    
    if request.method == 'POST':
        try:
            purchase = Purchase.objects.get(id=purchase_id)
            
            # Проверяем права доступа: учитель может отмечать выдачу только для своих учеников
            if not request.user.is_superuser:
                if not (purchase.user.group and purchase.user.group.teacher == request.user):
                    return JsonResponse({'success': False, 'error': 'Вы можете отмечать выдачу только для своих учеников'})
            
            purchase.mark_as_delivered()
            return JsonResponse({'success': True})
        except Purchase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Покупка не найдена'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def mark_purchase_not_delivered(request, purchase_id):
    """API endpoint для отмены выдачи товара"""
    if not (request.user.is_superuser or request.user.is_teacher()):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'})
    
    if request.method == 'POST':
        try:
            purchase = Purchase.objects.get(id=purchase_id)
            
            # Проверяем права доступа: учитель может отменять выдачу только для своих учеников
            if not request.user.is_superuser:
                if not (purchase.user.group and purchase.user.group.teacher == request.user):
                    return JsonResponse({'success': False, 'error': 'Вы можете отменять выдачу только для своих учеников'})
            
            purchase.delivered = False
            purchase.delivered_date = None
            purchase.save()
            return JsonResponse({'success': True})
        except Purchase.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Покупка не найдена'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def user_management(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администраторы могут управлять пользователями")
    
    # Получаем параметры фильтрации для учеников
    birthday_filter = request.GET.get('birthday_filter', '')
    
    # Базовый запрос для учеников с фильтрацией по городу
    students_query = User.objects.filter(role='student').select_related('profile', 'group', 'parent', 'city')
    
    # Фильтруем по городу администратора (если он не главный суперадмин)
    if hasattr(request.user, 'city') and request.user.city and request.user.role == 'city_admin':
        students_query = students_query.filter(city=request.user.city)
    
    # Применяем фильтр по дню рождения
    if birthday_filter == 'this_month':
        from datetime import datetime, timedelta
        now = datetime.now()
        # Получаем всех учеников, у которых день рождения в этом месяце
        students_query = students_query.filter(
            birth_date__month=now.month,
            birth_date__isnull=False
        ).order_by('birth_date__day')
    elif birthday_filter == 'next_month':
        from datetime import datetime, timedelta
        now = datetime.now()
        next_month = now.month + 1 if now.month < 12 else 1
        next_year = now.year if now.month < 12 else now.year + 1
        # Получаем всех учеников, у которых день рождения в следующем месяце
        students_query = students_query.filter(
            birth_date__month=next_month,
            birth_date__year__lte=next_year,
            birth_date__isnull=False
        ).order_by('birth_date__day')
    else:
        students_query = students_query.order_by('username')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_user':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            group_id = request.POST.get('group')
            city_id = request.POST.get('city')  # Получаем выбранный город
            
            try:
                # Создаем пользователя с базовыми полями
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )
                
                # Устанавливаем город (обязательно для всех ролей)
                if city_id:
                    try:
                        city = City.objects.get(id=city_id)
                        user.city = city
                    except City.DoesNotExist:
                        user.delete()
                        messages.error(request, 'Выбранный город не найден')
                        return redirect('user_management')
                elif hasattr(request.user, 'city') and request.user.city and request.user.role == 'city_admin':
                    # Если администратор города создает пользователя, автоматически устанавливаем его город
                    user.city = request.user.city
                    messages.info(request, f'Автоматически назначен город: {user.city.name}')
                else:
                    # Город обязателен для всех пользователей, кроме главного суперадмина
                    if not request.user.is_superuser:
                        user.delete()
                        messages.error(request, 'Необходимо выбрать город для пользователя')
                        return redirect('user_management')
                
                # Если создается администратор, устанавливаем is_superuser
                if role == 'city_admin':
                    user.is_superuser = True
                    user.is_staff = True
                
                # Сохраняем изменения города и роли
                user.save()
                
                # Если создается учитель, добавляем город в cities (ManyToMany)
                if role == 'teacher' and user.city:
                    user.cities.add(user.city)
                
                # Если создается ученик, добавляем дополнительные поля
                if role == 'student':
                    birth_day = request.POST.get('birth_day')
                    birth_month = request.POST.get('birth_month')
                    birth_year = request.POST.get('birth_year')
                    parent_id = request.POST.get('parent')
                    
                    if not birth_day or not birth_month or not birth_year:
                        user.delete()
                        messages.error(request, 'Для ученика необходимо указать полную дату рождения (день, месяц, год)')
                        return redirect('user_management')
                    
                    # Формируем дату из отдельных полей
                    try:
                        from datetime import date
                        birth_date = date(int(birth_year), int(birth_month), int(birth_day))
                        user.birth_date = birth_date
                    except ValueError:
                        user.delete()
                        messages.error(request, 'Некорректная дата рождения')
                        return redirect('user_management')
                    
                    # Привязываем родителя, если выбран
                    if parent_id:
                        try:
                            parent = Parent.objects.get(id=parent_id)
                            user.parent = parent
                        except Parent.DoesNotExist:
                            messages.warning(request, 'Выбранный родитель не найден')
                    
                    # Привязываем к группе, если выбрана
                    if group_id:
                        try:
                            group = Group.objects.get(id=group_id)
                            user.group = group
                        except Group.DoesNotExist:
                            messages.warning(request, 'Выбранная группа не найдена')
                    
                    user.save()
                
                messages.success(request, f'Пользователь {username} успешно создан')
            except Exception as e:
                messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
        
        elif action == 'edit_user':
            user_id = request.POST.get('user_id')
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            group_id = request.POST.get('group')
            
            try:
                user = User.objects.get(id=user_id)
                user.username = username
                user.email = email
                user.role = role
                
                # Обновляем права администратора
                if role == 'city_admin':
                    user.is_superuser = True
                    user.is_staff = True
                else:
                    user.is_superuser = False
                    user.is_staff = False
                
                if role == 'student':
                    birth_day = request.POST.get('birth_day')
                    birth_month = request.POST.get('birth_month')
                    birth_year = request.POST.get('birth_year')
                    parent_id = request.POST.get('parent')
                    balance = request.POST.get('balance')
                    
                    # Формируем дату из отдельных полей, если все поля заполнены
                    if birth_day and birth_month and birth_year:
                        try:
                            from datetime import date
                            birth_date = date(int(birth_year), int(birth_month), int(birth_day))
                            user.birth_date = birth_date
                        except ValueError:
                            messages.error(request, 'Некорректная дата рождения')
                            return redirect('user_management')
                    elif not birth_day or not birth_month or not birth_year:
                        messages.error(request, 'Для ученика необходимо указать полную дату рождения (день, месяц, год)')
                        return redirect('user_management')
                    
                    # Обновляем родителя
                    if parent_id:
                        try:
                            parent = Parent.objects.get(id=parent_id)
                            user.parent = parent
                        except Parent.DoesNotExist:
                            messages.warning(request, 'Выбранный родитель не найден')
                            user.parent = None
                    else:
                        user.parent = None
                    
                    # Обновляем баланс, если указан
                    if balance is not None and balance != '':
                        try:
                            new_balance = int(balance)
                            if new_balance >= 0:
                                profile = Profile.objects.get_or_create(user=user)[0]
                                old_balance = profile.astrocoins
                                profile.astrocoins = new_balance
                                profile.save()
                                
                                # Записываем транзакцию об изменении баланса администратором
                                if old_balance != new_balance:
                                    Transaction.objects.create(
                                        sender=request.user,
                                        receiver=user,
                                        amount=abs(new_balance - old_balance),
                                        transaction_type='EARN' if new_balance > old_balance else 'SPEND',
                                        description=f'Корректировка баланса администратором (было: {old_balance}, стало: {new_balance})'
                                    )
                            else:
                                messages.error(request, 'Баланс не может быть отрицательным')
                                return redirect('user_management')
                        except ValueError:
                            messages.error(request, 'Некорректное значение баланса')
                            return redirect('user_management')
                    
                    if group_id:
                        group = Group.objects.get(id=group_id)
                        user.group = group
                    else:
                        user.group = None
                elif role == 'city_admin':
                    # Администраторы не имеют полей ученика
                    user.birth_date = None
                    user.parent_full_name = ''
                    user.parent_phone = ''
                    user.group = None
                else:
                    # Преподаватели не имеют полей ученика
                    user.birth_date = None
                    user.parent_full_name = ''
                    user.parent_phone = ''
                    user.group = None
                
                user.save()
                messages.success(request, f'Пользователь {username} успешно обновлен')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении пользователя: {str(e)}')
        
        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                username = user.username
                
                # Проверяем, есть ли у пользователя активные группы как преподаватель
                teaching_groups = Group.objects.filter(teacher=user, is_active=True)
                
                # Проверяем, есть ли у пользователя группы как куратор
                curated_groups = Group.objects.filter(curator=user, is_active=True)
                
                if teaching_groups.exists() or curated_groups.exists():
                    groups_info = []
                    if teaching_groups.exists():
                        teaching_list = [f'"{group.name}"' for group in teaching_groups]
                        groups_info.append(f"преподает в группах: {', '.join(teaching_list)}")
                    
                    if curated_groups.exists():
                        curated_list = [f'"{group.name}"' for group in curated_groups]
                        groups_info.append(f"курирует группы: {', '.join(curated_list)}")
                    
                    groups_text = '; '.join(groups_info)
                    
                    messages.error(request, 
                        f'Невозможно удалить пользователя {username}, так как он {groups_text}. '
                        f'Сначала переназначьте группы другому преподавателю/куратору или удалите группы.')
                    return redirect('user_management')
                
                user.delete()
                messages.success(request, f'Пользователь {username} успешно удален')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении пользователя: {str(e)}')

        elif action == 'create_group':
            name = request.POST.get('name')
            teacher_id = request.POST.get('teacher')
            curator_id = request.POST.get('curator')
            description = request.POST.get('description')
            
            try:
                teacher = User.objects.get(id=teacher_id, role__in=['teacher', 'city_admin'])
                
                # Получаем куратора, если выбран
                curator = None
                if curator_id:
                    try:
                        curator = User.objects.get(id=curator_id, role='city_admin')
                    except User.DoesNotExist:
                        messages.warning(request, 'Выбранный куратор не найден, группа создана без куратора')
                
                group = Group.objects.create(
                    name=name,
                    description=description,
                    teacher=teacher,
                    curator=curator
                )
                
                teacher_name = teacher.get_full_name() or teacher.username
                curator_info = ""
                if curator:
                    curator_name = curator.get_full_name() or curator.username
                    curator_info = f", куратор: {curator_name}"
                
                messages.success(request, f'Группа {name} успешно создана (преподаватель: {teacher_name}{curator_info})')
            except User.DoesNotExist:
                messages.error(request, 'Выбранный преподаватель не найден')
            except Exception as e:
                messages.error(request, f'Ошибка при создании группы: {str(e)}')

        elif action == 'edit_group':
            group_id = request.POST.get('group_id')
            name = request.POST.get('name')
            teacher_id = request.POST.get('teacher')
            
            try:
                group = Group.objects.get(id=group_id)
                teacher = User.objects.get(id=teacher_id, role__in=['teacher', 'city_admin'])
                
                group.name = name
                group.teacher = teacher
                group.save()
                
                messages.success(request, f'Группа {name} успешно обновлена')
            except Group.DoesNotExist:
                messages.error(request, 'Группа не найдена')
            except User.DoesNotExist:
                messages.error(request, 'Выбранный преподаватель не найден')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении группы: {str(e)}')

        elif action == 'delete_group':
            group_id = request.POST.get('group_id')
            try:
                group = Group.objects.get(id=group_id)
                name = group.name
                
                # Открепляем всех учеников от группы перед удалением
                User.objects.filter(group=group).update(group=None)
                
                group.delete()
                messages.success(request, f'Группа {name} успешно удалена')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении группы: {str(e)}')
    
    # Фильтруем учителей и группы по городу администратора
    if hasattr(request.user, 'city') and request.user.city and request.user.role == 'city_admin':
        # Администратор города видит:
        # 1. Учителей, которые работают в этом городе (ManyToMany cities) ИЛИ администраторов этого города (ForeignKey city)
        teachers_query = User.objects.filter(
            Q(role__in=['teacher', 'city_admin'], cities=request.user.city) |  # Учителя работающие в городе
            Q(role='city_admin', city=request.user.city)  # Администраторы этого города
        ).distinct().order_by('username')
        
        # 2. ВСЕ группы в школах этого города (независимо от того, кто создал)
        groups_query = Group.objects.filter(school__city=request.user.city).select_related('teacher', 'school')
        
        # 3. Родителей учеников этого города
        parents_query = Parent.objects.filter(students__city=request.user.city).distinct().order_by('full_name')
    else:
        # Главный суперадмин видит всех
        teachers_query = User.objects.filter(role__in=['teacher', 'city_admin']).order_by('username')
        groups_query = Group.objects.all().select_related('teacher', 'school')
        parents_query = Parent.objects.all().order_by('full_name')
    
    context = {
        'admins': User.objects.filter(role='city_admin').order_by('username'),
        'teachers': teachers_query,
        'students': students_query,
        'groups': groups_query,
        'parents': parents_query,
        'birthday_filter': birthday_filter,
        'cities': City.objects.all().order_by('name'),  # Для выбора города при создании пользователей
    }
    return render(request, 'core/user_management.html', context)

@login_required
def add_category(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администратор может добавлять категории товаров")
    
    if request.method == 'POST':
        try:
            # Автоматически привязываем к городу администратора
            city = request.user.city if hasattr(request.user, 'city') and request.user.city else None
            if not city and not request.user.is_superuser:
                raise Exception("У администратора не указан город")
            
            category = ProductCategory.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', 'fas fa-cube'),
                is_featured=request.POST.get('is_featured', False) == 'on',
                order=int(request.POST.get('order', 0)),
                city=city  # Автоматически привязываем к городу
            )
            
            city_name = city.name if city else "без города"
            messages.success(request, f'Категория "{category.name}" успешно добавлена в город: {city_name}')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def edit_category(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администратор может редактировать категории товаров")
    
    if request.method == 'POST':
        try:
            category = ProductCategory.objects.get(id=request.POST['category_id'])
            
            # Проверяем права доступа - администратор может редактировать только категории своего города
            if (request.user.role == 'city_admin' and 
                hasattr(request.user, 'city') and request.user.city and 
                category.city != request.user.city):
                raise PermissionDenied("Вы можете редактировать только категории своего города")
            
            category.name = request.POST['name']
            category.description = request.POST.get('description', '')
            category.icon = request.POST.get('icon', 'fas fa-cube')
            category.is_featured = request.POST.get('is_featured', False) == 'on'
            category.order = int(request.POST.get('order', 0))
            category.save()
            
            city_name = category.city.name if category.city else "без города"
            messages.success(request, f'Категория "{category.name}" успешно обновлена в городе: {city_name}')
        except ProductCategory.DoesNotExist:
            messages.error(request, 'Категория не найдена')
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def delete_category(request):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администратор может удалять категории товаров")
    
    if request.method == 'POST':
        try:
            category = ProductCategory.objects.get(id=request.POST['category_id'])
            
            # Проверяем права доступа - администратор может удалять только категории своего города
            if (request.user.role == 'city_admin' and 
                hasattr(request.user, 'city') and request.user.city and 
                category.city != request.user.city):
                raise PermissionDenied("Вы можете удалять только категории своего города")
            
            category_name = category.name
            city_name = category.city.name if category.city else "без города"
            
            # Проверяем, есть ли товары в этой категории
            if category.products.exists():
                messages.error(request, f'Нельзя удалить категорию "{category_name}", так как в ней есть товары')
            else:
                category.delete()
                messages.success(request, f'Категория "{category_name}" из города {city_name} успешно удалена')
        except ProductCategory.DoesNotExist:
            messages.error(request, 'Категория не найдена')
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка при удалении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def get_category(request, category_id):
    if not (request.user.is_superuser or request.user.role == 'city_admin'):
        raise PermissionDenied("Только администратор может получать данные категорий")
    
    try:
        category = ProductCategory.objects.get(id=category_id)
        
        # Проверяем права доступа - администратор может получать только категории своего города
        if (request.user.role == 'city_admin' and 
            hasattr(request.user, 'city') and request.user.city and 
            category.city != request.user.city):
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'is_featured': category.is_featured,
            'order': category.order,
            'city': category.city.id if category.city else None
        }
        return JsonResponse(data)
    except ProductCategory.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)


# ===============================
# УПРАВЛЕНИЕ РОДИТЕЛЯМИ
# ===============================

@login_required
def parent_management(request):
    """
    Страница управления родителями (только для администраторов)
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут управлять родителями")
    
    # Получаем всех родителей с количеством детей
    parents = Parent.objects.all().order_by('full_name')
    
    # Обработка поиска
    search_query = request.GET.get('search', '')
    if search_query:
        parents = parents.filter(
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(work_place__icontains=search_query)
        )
    
    # Пагинация
    paginator = Paginator(parents, 20)  # 20 родителей на страницу
    page_number = request.GET.get('page')
    parents_page = paginator.get_page(page_number)
    
    # Получаем учеников без родителей для быстрого привязывания
    students_without_parents = User.objects.filter(role='student', parent__isnull=True).order_by('first_name', 'last_name', 'username')
    
    context = {
        'parents': parents_page,
        'search_query': search_query,
        'students_without_parents': students_without_parents,
        'total_parents': Parent.objects.count(),
        'students_with_parents': User.objects.filter(role='student', parent__isnull=False).count(),
        'students_without_parents_count': students_without_parents.count(),
    }
    
    return render(request, 'core/parent_management.html', context)


@login_required
def create_parent(request):
    """
    Создание нового родителя
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут создавать родителей")
    
    if request.method == 'POST':
        form = CreateParentWithStudentForm(request.POST)
        if form.is_valid():
            try:
                parent = form.save()
                student = form.cleaned_data.get('student')
                if student:
                    messages.success(
                        request, 
                        f'Родитель "{parent.full_name}" успешно создан и привязан к ученику {student.get_full_name() or student.username}'
                    )
                else:
                    messages.success(request, f'Родитель "{parent.full_name}" успешно создан')
                return redirect('parent_management')
            except Exception as e:
                messages.error(request, f'Ошибка при создании родителя: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('parent_management')


@login_required
def edit_parent(request, parent_id):
    """
    Редактирование родителя
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут редактировать родителей")
    
    parent = get_object_or_404(Parent, id=parent_id)
    
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Данные родителя "{parent.full_name}" успешно обновлены')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении данных: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('parent_management')


@login_required
def delete_parent(request, parent_id):
    """
    Удаление родителя
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут удалять родителей")
    
    if request.method == 'POST':
        parent = get_object_or_404(Parent, id=parent_id)
        parent_name = parent.full_name
        students_count = parent.students_count
        
        try:
            parent.delete()
            if students_count > 0:
                messages.success(
                    request, 
                    f'Родитель "{parent_name}" удален. {students_count} ученик(ов) остались без привязки к родителю.'
                )
            else:
                messages.success(request, f'Родитель "{parent_name}" успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении родителя: {str(e)}')
    
    return redirect('parent_management')


@login_required
def link_student_parent(request):
    """
    Привязка ученика к родителю
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут привязывать учеников к родителям")
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        parent_id = request.POST.get('parent_id')
        
        try:
            student = get_object_or_404(User, id=student_id, role='student')
            parent = get_object_or_404(Parent, id=parent_id)
            
            old_parent = student.parent
            student.parent = parent
            student.save()
            
            if old_parent:
                messages.success(
                    request,
                    f'Ученик {student.get_full_name() or student.username} перепривязан с "{old_parent.full_name}" на "{parent.full_name}"'
                )
            else:
                messages.success(
                    request,
                    f'Ученик {student.get_full_name() or student.username} привязан к родителю "{parent.full_name}"'
                )
        except Exception as e:
            messages.error(request, f'Ошибка при привязке: {str(e)}')
    
    return redirect('parent_management')


@login_required
def unlink_student_parent(request, student_id):
    """
    Отвязка ученика от родителя
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут отвязывать учеников от родителей")
    
    if request.method == 'POST':
        student = get_object_or_404(User, id=student_id, role='student')
        
        try:
            parent_name = student.parent.full_name if student.parent else None
            student.parent = None
            student.save()
            
            if parent_name:
                messages.success(
                    request,
                    f'Ученик {student.get_full_name() or student.username} отвязан от родителя "{parent_name}"'
                )
            else:
                messages.info(request, f'У ученика {student.get_full_name() or student.username} не было привязанного родителя')
        except Exception as e:
            messages.error(request, f'Ошибка при отвязке: {str(e)}')
    
    return redirect('parent_management')


@login_required
def get_parent_data(request, parent_id):
    """
    API для получения данных родителя (для модального окна редактирования)
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    try:
        parent = Parent.objects.get(id=parent_id)
        data = {
            'id': parent.id,
            'full_name': parent.full_name,
            'phone': parent.phone,
            'email': parent.email,
            'address': parent.address,
            'work_place': parent.work_place,
            'notes': parent.notes,
            'students': [
                {
                    'id': student.id,
                    'name': student.get_full_name() or student.username,
                    'username': student.username
                }
                for student in parent.students.all()
            ]
        }
        return JsonResponse(data)
    except Parent.DoesNotExist:
        return JsonResponse({'error': 'Родитель не найден'}, status=404)


# ===============================
# УПРАВЛЕНИЕ ШКОЛЬНОЙ СИСТЕМОЙ
# ===============================

@login_required
def city_management(request):
    """
    Страница управления городами (только для администраторов)
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут управлять городами")
    
    cities = City.objects.all().order_by('name')
    
    # Обработка поиска
    search_query = request.GET.get('search', '')
    if search_query:
        cities = cities.filter(name__icontains=search_query)
    
    context = {
        'cities': cities,
        'search_query': search_query,
        'total_cities': City.objects.count(),
        'total_schools': School.objects.count(),
    }
    
    return render(request, 'core/city_management.html', context)


@login_required
def create_city(request):
    """
    Создание нового города
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут создавать города")
    
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            try:
                city = form.save()
                messages.success(request, f'Город "{city.name}" успешно создан')
                return redirect('city_management')
            except Exception as e:
                messages.error(request, f'Ошибка при создании города: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('city_management')


@login_required
def school_management(request):
    """
    Страница управления школами (только для администраторов)
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут управлять школами")
    
    schools = School.objects.all().select_related('city').order_by('city__name', 'name')
    
    # Обработка поиска
    search_query = request.GET.get('search', '')
    if search_query:
        schools = schools.filter(
            Q(name__icontains=search_query) |
            Q(city__name__icontains=search_query) |
            Q(director__icontains=search_query) |
            Q(representative__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Фильтр по городу
    city_filter = request.GET.get('city')
    if city_filter:
        schools = schools.filter(city_id=city_filter)
    
    # Пагинация
    paginator = Paginator(schools, 10)  # 10 школ на страницу
    page_number = request.GET.get('page')
    schools_page = paginator.get_page(page_number)
    
    context = {
        'schools': schools_page,
        'search_query': search_query,
        'city_filter': city_filter,
        'cities': City.objects.all().order_by('name'),
        'total_schools': School.objects.count(),
        'total_courses': Course.objects.count(),
        'total_groups': Group.objects.count(),
    }
    
    return render(request, 'core/school_management.html', context)


@login_required
def create_school(request):
    """
    Создание новой школы
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут создавать школы")
    
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            try:
                school = form.save()
                messages.success(request, f'Школа "{school.name}" успешно создана')
                return redirect('school_management')
            except Exception as e:
                messages.error(request, f'Ошибка при создании школы: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('school_management')


@login_required
def school_detail(request, school_id):
    """
    Детальная страница школы с курсами
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут просматривать детали школ")
    
    school = get_object_or_404(School, id=school_id)
    courses = school.courses.all().order_by('-is_active', 'name')
    
    # Обработка поиска курсов
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'school': school,
        'courses': courses,
        'search_query': search_query,
        'active_courses_count': school.courses.filter(is_active=True).count(),
        'inactive_courses_count': school.courses.filter(is_active=False).count(),
        'groups_count': school.groups.count(),
    }
    
    return render(request, 'core/school_detail.html', context)


@login_required
def create_course(request, school_id):
    """
    Создание курса для школы
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут создавать курсы")
    
    school = get_object_or_404(School, id=school_id)
    
    if request.method == 'POST':
        form = QuickCourseForm(request.POST)
        if form.is_valid():
            try:
                course = form.save(school)
                messages.success(request, f'Курс "{course.name}" успешно создан')
                return redirect('school_detail', school_id=school.id)
            except Exception as e:
                messages.error(request, f'Ошибка при создании курса: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('school_detail', school_id=school.id)


@login_required
def edit_course(request, course_id):
    """
    Редактирование курса
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут редактировать курсы")
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Курс "{course.name}" успешно обновлен')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении курса: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    
    return redirect('school_detail', school_id=course.school.id)


@login_required
def delete_course(request, course_id):
    """
    Удаление курса
    """
    if not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только администраторы могут удалять курсы")
    
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        school_id = course.school.id
        course_name = course.name
        groups_count = course.groups.count()
        
        try:
            course.delete()
            if groups_count > 0:
                messages.success(
                    request, 
                    f'Курс "{course_name}" удален. {groups_count} группа(групп) также удалена.'
                )
            else:
                messages.success(request, f'Курс "{course_name}" успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении курса: {str(e)}')
        
        return redirect('school_detail', school_id=school_id)
    
    return redirect('school_management')





@login_required
def get_courses_by_school(request, school_id):
    """
    API для получения курсов по школе (для динамической загрузки в формах)
    """
    try:
        school = School.objects.get(id=school_id)
        courses = school.courses.filter(is_active=True).order_by('name')
        data = {
            'courses': [
                {
                    'id': course.id,
                    'name': course.name,
                    'description': course.description,
                    'duration_hours': course.duration_hours
                }
                for course in courses
            ]
        }
        return JsonResponse(data)
    except School.DoesNotExist:
        return JsonResponse({'error': 'Школа не найдена'}, status=404)


@login_required
def get_group_students(request, group_id):
    """
    API для получения списка учеников группы
    """
    try:
        group = Group.objects.get(id=group_id)
        
        # Проверяем права доступа: либо преподаватель этой группы, либо суперпользователь
        if not (request.user.is_superuser or 
                (request.user.is_teacher and group.teacher == request.user)):
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)
        
        students = group.students.all().order_by('last_name', 'first_name', 'username')
        data = {
            'students': [
                {
                    'id': student.id,
                    'username': student.username,
                    'full_name': student.get_full_name() or student.username,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'astrocoins': student.profile.astrocoins,
                    'email': student.email,
                    'date_joined': student.date_joined.strftime('%d.%m.%Y'),
                }
                for student in students
            ],
            'group_name': group.name,
            'total_students': students.count()
        }
        return JsonResponse(data)
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Группа не найдена'}, status=404)


# ===============================
# КАСТОМНЫЕ СТРАНИЦЫ ОШИБОК
# ===============================

def custom_page_not_found_view(request, exception):
    """Кастомная страница 404"""
    return render(request, '404.html', status=404)

def custom_server_error_view(request):
    """Кастомная страница 500"""
    return render(request, '500.html', status=500)

def custom_permission_denied_view(request, exception):
    """Кастомная страница 403"""
    return render(request, '403.html', status=403)


@login_required
def get_courses_by_school(request, school_id):
    """
    API endpoint для получения курсов по школе
    """
    try:
        school = School.objects.get(id=school_id)
        courses = Course.objects.filter(school=school, is_active=True).order_by('name')
        
        courses_data = []
        for course in courses:
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'description': course.description,
            })
        
        return JsonResponse({
            'success': True,
            'courses': courses_data
        })
    
    except School.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Школа не найдена'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_group_students(request, group_id):
    """
    API endpoint для получения учеников группы
    """
    try:
        group = Group.objects.get(id=group_id)
        
        # Проверяем права доступа
        if not (request.user.is_superuser or 
                (request.user.is_teacher() and group.teacher == request.user)):
            return JsonResponse({
                'success': False,
                'error': 'Недостаточно прав для просмотра учеников группы'
            })
        
        students = User.objects.filter(group=group, role='student').order_by('username')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'username': student.username,
                'full_name': student.get_full_name() or student.username,
                'email': student.email,
                'astrocoins': student.profile.astrocoins if hasattr(student, 'profile') else 0,
                'date_joined': student.date_joined.strftime('%d.%m.%Y'),
            })
        
        return JsonResponse({
            'success': True,
            'group_name': group.name,
            'total_students': len(students_data),
            'students': students_data
        })
    
    except Group.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Группа не найдена'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })