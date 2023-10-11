from django.core.validators import MaxValueValidator, MinValueValidator, ValidationError
from django.db import models


class Position(models.Model):
    position_name = models.CharField(max_length=300)
    hourly_rate = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    def __str__(self):
        return self.position_name

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(hourly_rate__lte=100), name='max_rate')
        ]
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


class Employee(models.Model):
    """ Ни один из объектов Position не будет удален, если на нем работает хотя бы один сотрудник
    (models.PROTECT)"""

    employee_name = models.CharField(max_length=100)
    position = models.ForeignKey(Position, on_delete=models.PROTECT, related_name='employees')

    def __str__(self):
        return self.employee_name

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'


class Task(models.Model):
    task_name = models.CharField(max_length=300)

    def __str__(self):
        return self.task_name

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'


class Timesheet(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='timesheets')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='timesheets')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f"{self.employee}: {self.task}"

    def save(self, *args, **kwargs):
        """Метод проверяет пересечение временных рядов для данного таймшита,
        используя start_time, end_time, и employee текущего таймшита.
        Метод filter фильтрует все таймшиты сотрудника,
        для которого временной ряд пересекается с текущим таймшитом.
        Если мы обновляем уже существующую запись, проверка сначала исключает этот таймшит из рассмотрения,
        чтобы он не сравнивался сам с собой и не вызывал ложные сообщения об ошибках.
        Если существует хотя бы один таймшит, нарушающий условия, вызывается исключение ValidationError
        с соответствующим сообщением. Переопределяем метод save, чтобы перед сохранением записи
        (созданием или обновлением) вызывался наш пользовательский валидатор.
        Это гарантирует, что для каждого таймшита будет выполнена проверка пересечения временных рядов перед
         сохранением в базе данных."""

        if self.start_time >= self.end_time:
            raise ValidationError('Время окончания работы должно быть позже времени начала')

        overlapping_timesheets = Timesheet.objects.filter(
            employee=self.employee,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )

        if self.pk:
            # исключаем текущий таймшит из проверки, так как он уже существует, и мы его обновляем
            overlapping_timesheets = overlapping_timesheets.exclude(pk=self.pk)

        if overlapping_timesheets.exists():
            raise ValidationError(
                f"Сотрудник не может работать над двумя задачами одновременно. "
                f"Найден пересекающийся таймшит: {overlapping_timesheets.first()}"
            )

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Таймшит'
        verbose_name_plural = 'Таймшиты'
        ordering = ['employee']
