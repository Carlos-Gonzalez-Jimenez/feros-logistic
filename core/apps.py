from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        import core.signals
        post_migrate.connect(self.add_schedules, sender=self, dispatch_uid='core.add_schedules')


    def add_schedules(self, **kwargs):
        from django_q.tasks import schedule
        from django_q.models import Schedule
        Schedule.objects.filter(name__in=['update_invoice_status']).delete()
        schedule(
            'core.task_schedules.update_invoice_status',
            name='update_invoice_status',
            schedule_type=Schedule.MINUTES, minutes=30
        )
        schedule(
            'core.task_schedules.update_booking_status',
            name='update_booking_status',
            schedule_type=Schedule.MINUTES, minutes=30
        )
