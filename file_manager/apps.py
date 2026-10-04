from django.apps import AppConfig


class FileManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "file_manager"

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self.add_root_folder, sender=self, dispatch_uid='core.add_root_folder')

    def add_root_folder(self, **kwargs):
        from file_manager import models
        models.Folder.objects.update_or_create(
            root=True,
            defaults={"name": 'Inicio'},
            create_defaults={"name": "Inicio", "root": True}
        )
