from django_mongoengine.queryset import QuerySetManager

from .config import (
    DELETED_INVISIBLE,
    DELETED_ONLY_VISIBLE,
    DELETED_VISIBLE,
)
from .queryset import SafeDeletionQuerySet


class SafeDeletionQuerySetManager(QuerySetManager):
    """
    Default manager for the SafeDeletionDocument.

    If _safedeletion_visibility == DELETED_VISIBLE_BY_PK, the manager can returns deleted
    objects if they are accessed by primary key.

    :attribute _safedeletion_visibility: define what happens when you query masked objects.
        It can be one of ``DELETED_INVISIBLE`` and ``DELETED_VISIBLE_BY_PK``.
        Defaults to ``DELETED_INVISIBLE``.

        >>> from safedeletion_mongoengine.documents import SafeDeletionDocument
        >>> from safedeletion_mongoengine.managers import SafeDeletionQuerySetManager
        >>> class MyDocumentManager(SafeDeletionQuerySetManager):
        ...     _safedeletion_visibility = DELETED_VISIBLE_BY_PK

        >>> class MyDocument(SafeDeletionDocument):
        ...     _safedeletion_policy = SOFT_DELETE
        ...     my_field = fields.TextField()
        ...     objects = MyDocumentManager()
        >>>

    :attribute _queryset_class: define which class for queryset should be used
        This attribute allows to add custom filters for both deleted and not
        deleted objects. It is ``SafeDeletionQueryset`` by default.
        Custom queryset classes should be inherited from ``SafeDeletionQueryset``.
    """

    _safedeletion_visibility = DELETED_INVISIBLE
    _safedeletion_visibility_field = "pk"
    default = SafeDeletionQuerySet

    def __get__(self, instance, owner):
        queryset = super().__get__(instance, owner)
        setattr(queryset, "_safedeletion_visibility", self._safedeletion_visibility)
        setattr(
            queryset,
            "_safedeletion_visibility_field",
            self._safedeletion_visibility_field,
        )
        return queryset

    def all_with_deleted(self):
        """Show all models including the soft deleted documents.

        .. note::
            This is useful for related managers as those don't have access to
            ``all_objects``.
        """
        return self.all(force_visibility=DELETED_VISIBLE)

    def deleted_only(self):
        """Only show the soft deleted documents.

        .. note::
            This is useful for related managers as those don't have access to
            ``deleted_objects``.
        """
        return self.all(force_visibility=DELETED_ONLY_VISIBLE)

    def all(self, **kwargs):
        """Pass kwargs to ``SafeDeletionQuerySet.all()``.

        Args:
            force_visibility: Show deleted documents. (default: {None})

        .. note::
            The ``force_visibility`` argument is meant for related managers when no
            other managers like ``all_objects`` or ``deleted_objects`` are available.
        """
        force_visibility = kwargs.pop("force_visibility", None)

        qs = self.get_queryset()
        if force_visibility is not None:
            # pylint: disable=protected-access
            qs._safedeletion_force_visibility = force_visibility
        return qs


class SafeDeletionAllQuerySetManager(SafeDeletionQuerySetManager):
    """SafeDeletionQuerySetManager with ``_safedeletion_visibility`` set to ``DELETED_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedeletion_mongoengine.documents.SafeDeletionDocument.all_objects`.
    """

    _safedeletion_visibility = DELETED_VISIBLE


class SafeDeletionDeletedQuerySetManager(SafeDeletionQuerySetManager):
    """SafeDeletionQuerySetManager with ``_safedeletion_visibility`` set to ``DELETED_ONLY_VISIBLE``.

    .. note::
        This is used in :py:attr:`safedeletion_mongoengine.documents.SafeDeletionDocument.deleted_objects`.
    """

    _safedeletion_visibility = DELETED_ONLY_VISIBLE
