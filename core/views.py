from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Profile, Transaction, Product, Purchase, Group, AwardReason, CoinAward, ProductCategory
# from decimal import Decimal - больше не нужен, используем int
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
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
    
    context = {
        'profile': profile,
        'transactions': transactions,
        'background_image': random_background['url'],
        'background_name': random_background['name'],
    }
    return render(request, 'core/dashboard.html', context)

from django.core.exceptions import PermissionDenied

@login_required
def shop(request):
    # Проверяем, что пользователь не является преподавателем
    if request.user.is_teacher() and not request.user.is_superuser:
        raise PermissionDenied("Преподаватели не могут совершать покупки в магазине")
    
    categories = ProductCategory.objects.all().order_by('order')
    
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
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может добавлять товары")
    
    if request.method == 'POST':
        try:
            product = Product.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                stock=request.POST['stock'],
                category_id=request.POST['category'],
                is_digital=request.POST.get('is_digital', False) == 'on',
                featured=request.POST.get('featured', False) == 'on'
            )
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            
            messages.success(request, f'Товар "{product.name}" успешно добавлен')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')
        
        return redirect('shop')

@login_required
def edit_product(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может редактировать товары")
    
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=request.POST['product_id'])
            product.name = request.POST['name']
            product.description = request.POST['description']
            product.price = request.POST['price']
            product.stock = request.POST['stock']
            product.category_id = request.POST['category']
            product.is_digital = request.POST.get('is_digital', False) == 'on'
            product.featured = request.POST.get('featured', False) == 'on'
            
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            messages.success(request, f'Товар "{product.name}" успешно обновлен')
        except Product.DoesNotExist:
            messages.error(request, 'Товар не найден')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении товара: {str(e)}')
        
        return redirect('shop')

@login_required
def get_product(request, product_id):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может получать данные товаров")
    
    try:
        product = Product.objects.get(id=product_id)
        data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': str(product.price),
            'stock': product.stock,
            'category': product.category_id if product.category else None,
            'is_digital': product.is_digital,
            'featured': product.featured
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
    
    product = get_object_or_404(Product, id=product_id, available=True)
    profile = Profile.objects.get(user=request.user)
    
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
            # Обновление основной информации
            user_to_edit.first_name = request.POST.get('first_name', '')
            user_to_edit.last_name = request.POST.get('last_name', '')
            user_to_edit.email = request.POST.get('email', '')
            user_to_edit.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            
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
        'is_own_profile': user_id is None,
    }
    return render(request, 'core/profile_edit.html', context)

@login_required
def knowledge_base(request):
    return render(request, 'core/knowledge_base.html')

@login_required
def groups(request):
    context = {}
    
    if request.user.is_teacher():
        # Для преподавателя показываем его группы и форму создания группы
        groups = Group.objects.filter(teacher=request.user)
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'create_group':
                name = request.POST.get('name')
                description = request.POST.get('description')
                if name:
                    Group.objects.create(
                        name=name,
                        description=description,
                        teacher=request.user
                    )
                    messages.success(request, 'Группа успешно создана')
            
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
        
        # Получаем шаблоны начислений для учителей
        from .models import AwardReason
        award_reasons = AwardReason.objects.all().order_by('coins')
        
        context.update({
            'teacher_groups': groups,
            'award_reasons': award_reasons,
            'is_teacher': True
        })
    else:
        # Для ученика показываем его группу и статистику
        if request.user.group:
            context.update({
                'student_group': request.user.group,
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
            
            try:
                reason = AwardReason.objects.get(id=reason_id)
                
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
                
                award = CoinAward.objects.create(
                    student=student,
                    teacher=request.user,
                    reason=reason,
                    amount=reason.coins,
                    comment=comment
                )
                messages.success(request, f'Начислено {reason.coins} AC')
                
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
    
    # Определяем какие пользователи доступны для просмотра
    if request.user.is_superuser:
        # Администратор видит всех
        available_users = User.objects.filter(role='student').select_related('profile', 'group')
        purchases = Purchase.objects.all().select_related('user', 'product', 'user__profile', 'user__group').order_by('-created_at')
        transfers = Transaction.objects.filter(transaction_type='TRANSFER').select_related('sender', 'receiver', 'sender__profile', 'receiver__profile', 'sender__group', 'receiver__group').order_by('-created_at')
    else:
        # Учитель видит только своих учеников
        available_users = User.objects.filter(role='student', group__teacher=request.user).select_related('profile', 'group')
        purchases = Purchase.objects.filter(user__group__teacher=request.user).select_related('user', 'product', 'user__profile', 'user__group').order_by('-created_at')
        transfers = Transaction.objects.filter(
            transaction_type='TRANSFER'
        ).filter(
            Q(sender__group__teacher=request.user) | Q(receiver__group__teacher=request.user)
        ).select_related('sender', 'receiver', 'sender__profile', 'receiver__profile', 'sender__group', 'receiver__group').order_by('-created_at')
    
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
        'purchases': purchases,
        'transfers': transfers,
        'is_superuser': request.user.is_superuser,
    }
    return render(request, 'core/activity_monitoring.html', context)

@login_required
def user_management(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администраторы могут управлять пользователями")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_user':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            group_id = request.POST.get('group')
            
            try:
                # Создаем пользователя с базовыми полями
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    role=role
                )
                
                # Если создается ученик, добавляем дополнительные поля
                if role == 'student':
                    birth_date = request.POST.get('birth_date')
                    parent_full_name = request.POST.get('parent_full_name')
                    parent_phone = request.POST.get('parent_phone')
                    
                    if not all([birth_date, parent_full_name, parent_phone]):
                        user.delete()
                        messages.error(request, 'Для ученика необходимо заполнить все дополнительные поля')
                        return redirect('user_management')
                    
                    user.birth_date = birth_date
                    user.parent_full_name = parent_full_name
                    user.parent_phone = parent_phone
                    
                    if group_id:
                        group = Group.objects.get(id=group_id)
                        user.group = group
                    
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
                
                if role == 'student':
                    birth_date = request.POST.get('birth_date')
                    parent_full_name = request.POST.get('parent_full_name')
                    parent_phone = request.POST.get('parent_phone')
                    balance = request.POST.get('balance')
                    
                    if not all([birth_date, parent_full_name, parent_phone]):
                        messages.error(request, 'Для ученика необходимо заполнить все дополнительные поля')
                        return redirect('user_management')
                    
                    user.birth_date = birth_date
                    user.parent_full_name = parent_full_name
                    user.parent_phone = parent_phone
                    
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
                else:
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
                user.delete()
                messages.success(request, f'Пользователь {username} успешно удален')
            except Exception as e:
                messages.error(request, f'Ошибка при удалении пользователя: {str(e)}')

        elif action == 'create_group':
            name = request.POST.get('name')
            teacher_id = request.POST.get('teacher')
            description = request.POST.get('description')
            
            try:
                teacher = User.objects.get(id=teacher_id, role='teacher')
                group = Group.objects.create(
                    name=name,
                    description=description,
                    teacher=teacher
                )
                messages.success(request, f'Группа {name} успешно создана')
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
                teacher = User.objects.get(id=teacher_id, role='teacher')
                
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
    
    context = {
        'teachers': User.objects.filter(role='teacher'),
        'students': User.objects.filter(role='student'),
        'groups': Group.objects.all().select_related('teacher')
    }
    return render(request, 'core/user_management.html', context)

@login_required
def add_category(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может добавлять категории товаров")
    
    if request.method == 'POST':
        try:
            category = ProductCategory.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', 'fas fa-cube'),
                is_featured=request.POST.get('is_featured', False) == 'on',
                order=int(request.POST.get('order', 0))
            )
            messages.success(request, f'Категория "{category.name}" успешно добавлена')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def edit_category(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может редактировать категории товаров")
    
    if request.method == 'POST':
        try:
            category = ProductCategory.objects.get(id=request.POST['category_id'])
            category.name = request.POST['name']
            category.description = request.POST.get('description', '')
            category.icon = request.POST.get('icon', 'fas fa-cube')
            category.is_featured = request.POST.get('is_featured', False) == 'on'
            category.order = int(request.POST.get('order', 0))
            category.save()
            
            messages.success(request, f'Категория "{category.name}" успешно обновлена')
        except ProductCategory.DoesNotExist:
            messages.error(request, 'Категория не найдена')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def delete_category(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может удалять категории товаров")
    
    if request.method == 'POST':
        try:
            category = ProductCategory.objects.get(id=request.POST['category_id'])
            category_name = category.name
            
            # Проверяем, есть ли товары в этой категории
            if category.products.exists():
                messages.error(request, f'Нельзя удалить категорию "{category_name}", так как в ней есть товары')
            else:
                category.delete()
                messages.success(request, f'Категория "{category_name}" успешно удалена')
        except ProductCategory.DoesNotExist:
            messages.error(request, 'Категория не найдена')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении категории: {str(e)}')
        
        return redirect('shop')

@login_required
def get_category(request, category_id):
    if not request.user.is_superuser:
        raise PermissionDenied("Только администратор может получать данные категорий")
    
    try:
        category = ProductCategory.objects.get(id=category_id)
        data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'is_featured': category.is_featured,
            'order': category.order
        }
        return JsonResponse(data)
    except ProductCategory.DoesNotExist:
        return JsonResponse({'error': 'Категория не найдена'}, status=404)