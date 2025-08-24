-- Проверка структуры данных ученика в PostgreSQL
-- Запустите эту команду на вашем VPS: psql -d astrocoins_db -f check_student_structure.sql

\echo '=== СТРУКТУРА ТАБЛИЦ ==='

\echo '\n1. Структура таблицы User (core_user):'
\d core_user;

\echo '\n2. Структура таблицы Profile (core_profile):'
\d core_profile;

\echo '\n3. Структура таблицы Group (core_group):'
\d core_group;

\echo '\n4. Структура таблицы School (core_school):'
\d core_school;

\echo '\n5. Структура таблицы Course (core_course):'
\d core_course;

\echo '\n6. Структура таблицы City (core_city):'
\d core_city;

\echo '\n=== ПРИМЕРЫ ДАННЫХ ==='

\echo '\n7. Пример учеников:'
SELECT 
    u.id,
    u.username,
    u.first_name,
    u.last_name,
    u.middle_name,
    u.role,
    u.is_active,
    p.astrocoins as balance,
    g.name as group_name,
    s.name as school_name,
    c.name as course_name,
    city.name as city_name
FROM core_user u
LEFT JOIN core_profile p ON u.id = p.user_id
LEFT JOIN core_group g ON u.group_id = g.id
LEFT JOIN core_school s ON g.school_id = s.id
LEFT JOIN core_course course ON g.course_id = course.id
LEFT JOIN core_city city ON s.city_id = city.id
WHERE u.role = 'student'
LIMIT 5;

\echo '\n8. Статистика по ученикам:'
SELECT 
    COUNT(*) as total_students,
    COUNT(DISTINCT u.group_id) as groups_with_students,
    AVG(p.astrocoins) as avg_balance,
    MIN(p.astrocoins) as min_balance,
    MAX(p.astrocoins) as max_balance
FROM core_user u
LEFT JOIN core_profile p ON u.id = p.user_id
WHERE u.role = 'student';

\echo '\n9. Группы и их ученики:'
SELECT 
    g.name as group_name,
    COUNT(u.id) as students_count,
    s.name as school_name,
    course.name as course_name
FROM core_group g
LEFT JOIN core_user u ON u.group_id = g.id AND u.role = 'student'
LEFT JOIN core_school s ON g.school_id = s.id
LEFT JOIN core_course course ON g.course_id = course.id
GROUP BY g.id, g.name, s.name, course.name
ORDER BY students_count DESC;

\echo '\n10. Преподаватели и кураторы:'
SELECT 
    u.username,
    u.first_name,
    u.last_name,
    u.role,
    COUNT(DISTINCT g.id) as groups_count
FROM core_user u
LEFT JOIN core_group g ON g.teacher_id = u.id OR g.curator_id = u.id
WHERE u.role IN ('teacher', 'city_admin')
GROUP BY u.id, u.username, u.first_name, u.last_name, u.role
ORDER BY groups_count DESC;
