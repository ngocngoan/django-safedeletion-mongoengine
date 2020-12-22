from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from mongoengine import CASCADE, fields
from django_mongoengine import Document

from .config import (
    HARD_DELETE,
    HARD_DELETE_NOCASCADE,
    NO_DELETE,
    SOFT_DELETE,
    SOFT_DELETE_CASCADE,
)
from .managers import (
    SafeDeletionQuerySetManager,
    SafeDeletionAllQuerySetManager,
    SafeDeletionDeletedQuerySetManager,
)
from .queryset import SafeDeletionQuerySet
from .signals import post_undelete


# Create your models here.
class SafeDeletionDocument(Document):
    _safedeletion_policy = SOFT_DELETE

    deleted = fields.DateTimeField(
        verbose_name=_("deleted at"),
        default=None,
        help_text=_("Designates whether the object has been deleted."),
    )

    meta = {"abstract": True, "queryset_class": SafeDeletionQuerySet}

    objects = SafeDeletionQuerySetManager()
    all_objects = SafeDeletionAllQuerySetManager()
    deleted_objects = SafeDeletionDeletedQuerySetManager()

    @property
    def _qs(self):
        """Return the default queryset corresponding to this document."""
        if not hasattr(self, "__objects"):
            # pylint: disable=attribute-defined-outside-init
            self.__objects = SafeDeletionQuerySet(self, self._get_collection())
        return self.__objects

    def save(self, keep_deleted=False, **kwargs):
        was_undeleted = False
        if not keep_deleted:
            if self.deleted and self.pk:
                was_undeleted = True
            self.deleted = None

        super().save(**kwargs)

        if was_undeleted:
            # TODO: save on the other database
            # send undelete signal
            document = self.switch_db(db_alias=self._state.db)
            post_undelete.send(sender=self.__class__, document=document)

    def undelete_cascade(self, delete_rules: list, update: dict, **write_concern):
        for rule_entry, rule in delete_rules:
            document_cls, field_name = rule_entry
            if not issubclass(document_cls, SafeDeletionDocument):
                continue

            if document_cls._meta.get("abstract"):
                continue

            if rule == CASCADE:
                document_cls.deleted_objects(**{field_name: self}).update(
                    write_concern=write_concern, **update
                )

    def undelete(self, force_policy=None, **write_concern):
        current_policy = force_policy or self._safedeletion_policy

        assert self.deleted
        self.save(keep_deleted=False, **write_concern)

        if current_policy == SOFT_DELETE_CASCADE:
            # undelete with relate documents
            delete_rules = self._meta.get("delete_rules") or {}
            delete_rules = list(delete_rules.items())
            update = {"unset__deleted": 1}
            self.undelete_cascade(
                delete_rules=delete_rules, update=update, **write_concern
            )

    def delete_cascade(self, delete_rules: list, update: dict, **write_concern):
        for rule_entry, rule in delete_rules:
            document_cls, field_name = rule_entry
            if not issubclass(document_cls, SafeDeletionDocument):
                continue

            if document_cls._meta.get("abstract"):
                continue

            if rule == CASCADE:
                document_cls.objects(**{field_name: self}).update(
                    write_concern=write_concern, **update
                )

    # pylint: disable=inconsistent-return-statements
    def delete(self, force_policy=None, signal_kwargs=None, **write_concern):
        current_policy = (
            self._safedeletion_policy if (force_policy is None) else force_policy
        )
        now = timezone.now()

        if current_policy == NO_DELETE:
            # Don't do anything.
            return

        if current_policy == SOFT_DELETE:
            # Only soft-delete the object, marking it as deleted.
            self.deleted = now
            self.save(keep_deleted=True)
            return

        delete_rules = self._meta.get("delete_rules") or {}
        delete_rules = list(delete_rules.items())

        if current_policy == HARD_DELETE_NOCASCADE:
            force_policy = SOFT_DELETE if len(delete_rules) > 0 else HARD_DELETE
            self._safedeletion_policy = (
                self._safedeletion_policy if len(delete_rules) > 0 else HARD_DELETE
            )
            return self.delete(
                force_policy, signal_kwargs=signal_kwargs, **write_concern
            )

        if current_policy == SOFT_DELETE_CASCADE:
            update = {"deleted": now}
            self.delete_cascade(
                delete_rules=delete_rules, update=update, **write_concern
            )
            return self.delete(
                force_policy=SOFT_DELETE, signal_kwargs=signal_kwargs, **write_concern
            )

        if current_policy == HARD_DELETE:
            return super().delete(signal_kwargs, **write_concern)
