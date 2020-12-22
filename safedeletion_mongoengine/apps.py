from django.apps import AppConfig


class SafedeletionMongoengineConfig(AppConfig):
    name = "safedeletion_mongoengine"
    verbose_name = "Safe Delete for Mongoengine"

    def ready(self):
        pass
