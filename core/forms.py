from django import forms
from .models import Parent, User, City, School, Course, Group


class ParentForm(forms.ModelForm):
    """
    Форма для создания и редактирования родителей
    """
    class Meta:
        model = Parent
        fields = ['full_name', 'phone', 'email', 'address', 'work_place', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ФИО родителя'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (9XX) XXX-XX-XX',
                'pattern': r'\+7\s?[\(]{0,1}9[0-9]{2}[\)]{0,1}\s?\d{3}[-]{0,1}\d{2}[-]{0,1}\d{2}'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Адрес проживания'
            }),
            'work_place': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Место работы'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Простая валидация российского номера
            import re
            pattern = r'\+7\s?[\(]{0,1}9[0-9]{2}[\)]{0,1}\s?\d{3}[-]{0,1}\d{2}[-]{0,1}\d{2}'
            if not re.match(pattern, phone):
                raise forms.ValidationError('Введите корректный российский номер телефона в формате +7 (9XX) XXX-XX-XX')
        return phone


class StudentParentLinkForm(forms.ModelForm):
    """
    Форма для привязки родителя к ученику
    """
    parent = forms.ModelChoiceField(
        queryset=Parent.objects.all(),
        empty_label="Выберите родителя",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['parent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сортируем родителей по алфавиту
        self.fields['parent'].queryset = Parent.objects.all().order_by('full_name')


class CreateParentWithStudentForm(forms.Form):
    """
    Комбинированная форма для создания родителя и привязки к ученику
    """
    # Поля родителя
    parent_full_name = forms.CharField(
        max_length=255,
        label='ФИО родителя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ФИО родителя'
        })
    )
    parent_phone = forms.CharField(
        max_length=20,
        required=False,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (9XX) XXX-XX-XX',
            'pattern': r'\+7\s?[\(]{0,1}9[0-9]{2}[\)]{0,1}\s?\d{3}[-]{0,1}\d{2}[-]{0,1}\d{2}'
        })
    )
    parent_email = forms.EmailField(
        required=False,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    parent_address = forms.CharField(
        required=False,
        label='Адрес',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Адрес проживания'
        })
    )
    parent_work_place = forms.CharField(
        max_length=255,
        required=False,
        label='Место работы',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Место работы'
        })
    )
    parent_notes = forms.CharField(
        required=False,
        label='Заметки',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительные заметки'
        })
    )
    
    # Выбор ученика для привязки
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(role='student'),
        label='Ученик',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        help_text='Выберите ученика для привязки к родителю (опционально)'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Сортируем учеников по имени
        self.fields['student'].queryset = User.objects.filter(role='student').order_by('first_name', 'last_name', 'username')

    def clean_parent_phone(self):
        phone = self.cleaned_data.get('parent_phone')
        if phone:
            import re
            pattern = r'\+7\s?[\(]{0,1}9[0-9]{2}[\)]{0,1}\s?\d{3}[-]{0,1}\d{2}[-]{0,1}\d{2}'
            if not re.match(pattern, phone):
                raise forms.ValidationError('Введите корректный российский номер телефона в формате +7 (9XX) XXX-XX-XX')
        return phone

    def save(self):
        """
        Создает родителя и привязывает его к ученику
        """
        # Создаем родителя
        parent = Parent.objects.create(
            full_name=self.cleaned_data['parent_full_name'],
            phone=self.cleaned_data.get('parent_phone', ''),
            email=self.cleaned_data.get('parent_email', ''),
            address=self.cleaned_data.get('parent_address', ''),
            work_place=self.cleaned_data.get('parent_work_place', ''),
            notes=self.cleaned_data.get('parent_notes', ''),
        )
        
        # Привязываем к ученику, если выбран
        student = self.cleaned_data.get('student')
        if student:
            student.parent = parent
            student.save()
        
        return parent


# ===============================
# ФОРМЫ ДЛЯ ШКОЛЬНОЙ СИСТЕМЫ
# ===============================

class CityForm(forms.ModelForm):
    """
    Форма для создания и редактирования городов
    """
    class Meta:
        model = City
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название города'
            }),
        }


class SchoolForm(forms.ModelForm):
    """
    Форма для создания и редактирования школ
    """
    class Meta:
        model = School
        fields = ['city', 'name', 'director', 'representative', 'address', 'phone', 'email', 'website']
        widgets = {
            'city': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название учреждения'
            }),
            'director': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО директора'
            }),
            'representative': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ФИО представителя'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Полный адрес учреждения'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@school.ru'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://school.ru'
            }),
        }


class CourseForm(forms.ModelForm):
    """
    Форма для создания и редактирования курсов
    """
    class Meta:
        model = Course
        fields = ['school', 'name', 'description', 'duration_hours', 'is_active']
        widgets = {
            'school': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название курса'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание курса, цели, программа...'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
        
        if school:
            # Если указана школа, ограничиваем выбор только этой школой
            self.fields['school'].queryset = School.objects.filter(id=school.id)
            self.fields['school'].initial = school
        else:
            self.fields['school'].queryset = School.objects.all().order_by('city__name', 'name')


class GroupForm(forms.ModelForm):
    """
    Обновленная форма для создания и редактирования групп
    """
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'course', 'school', 'teacher', 'curator',
            'first_lesson_date', 'lesson_time', 'classroom', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название группы'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание группы'
            }),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'curator': forms.Select(attrs={'class': 'form-select'}),
            'first_lesson_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lesson_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'classroom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Кабинет/аудитория'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор преподавателей
        self.fields['teacher'].queryset = User.objects.filter(
            role__in=['teacher', 'admin']
        ).order_by('first_name', 'last_name', 'username')
        
        # Ограничиваем выбор кураторов
        self.fields['curator'].queryset = User.objects.filter(
            role='admin'
        ).order_by('first_name', 'last_name', 'username')
        self.fields['curator'].empty_label = "Не назначен"
        
        # Сортируем школы и курсы
        self.fields['school'].queryset = School.objects.all().order_by('city__name', 'name')
        self.fields['course'].queryset = Course.objects.filter(is_active=True).order_by('school__name', 'name')

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        school = cleaned_data.get('school')
        
        # Проверяем, что курс принадлежит выбранной школе
        if course and school and course.school != school:
            raise forms.ValidationError({
                'course': 'Выбранный курс не принадлежит указанной школе.'
            })
        
        return cleaned_data


class QuickCourseForm(forms.Form):
    """
    Быстрая форма для создания курса внутри школы
    """
    name = forms.CharField(
        max_length=255,
        label='Название курса',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название курса'
        })
    )
    description = forms.CharField(
        required=False,
        label='Описание',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Описание курса (опционально)'
        })
    )
    duration_hours = forms.IntegerField(
        initial=0,
        min_value=0,
        label='Продолжительность (часы)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )
    is_active = forms.BooleanField(
        initial=True,
        required=False,
        label='Активный курс',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def save(self, school):
        """
        Создает курс для указанной школы
        """
        course = Course.objects.create(
            school=school,
            name=self.cleaned_data['name'],
            description=self.cleaned_data.get('description', ''),
            duration_hours=self.cleaned_data.get('duration_hours', 0),
            is_active=self.cleaned_data.get('is_active', True)
        )
        return course