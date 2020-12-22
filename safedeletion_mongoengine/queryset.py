from django_mongoengine.queryset import QuerySet

from .config import (
    HARD_DELETE,
    DELETED_INVISIBLE,
    DELETED_ONLY_VISIBLE,
    DELETED_VISIBLE,
    DELETED_VISIBLE_BY_FIELD,
)


class SafeDeletionQuerySet(QuerySet):
    """Default queryset for the SafeDeletionQuerySetManager.

    Takes care of "lazily evaluating" safedeletion QuerySets. QuerySets passed
    within the ``SafeDeletionQuerySetManager`` will have all of the models available.
    The deleted policy is evaluated at the very end of the chain when the
    QuerySet itself is evaluated.
    """

    _safedeletion_visibility = DELETED_INVISIBLE
    _safedeletion_visibility_field = "pk"
    _safedeletion_filter_applied = False

    # pylint: disable=arguments-differ
    # pylint: disable=inconsistent-return-statements
    def delete(
        self,
        force_policy=None,
        signal_kwargs=None,
        write_concern=None,
        _from_doc_delete=False,
        cascade_refs=None,
    ):
        doc = self._document
        # pylint: disable=protected-access
        current_policy = (
            doc._safedeletion_policy if (force_policy is None) else force_policy
        )

        if current_policy == HARD_DELETE:
            return super().delete(write_concern, _from_doc_delete, cascade_refs)

        if write_concern is None:
            write_concern = {}

        for obj in self.all():
            obj.delete(
                force_policy=force_policy, signal_kwargs=signal_kwargs, **write_concern
            )

    def undelete(self, force_policy=None, **write_concern):
        for obj in self.all():
            obj.undelete(force_policy, **write_concern)

    def __call__(self, q_obj=None, **query):
        force_visibility = getattr(self, "_safedeletion_force_visibility", None)
        visibility = (
            force_visibility
            if force_visibility is not None
            else self._safedeletion_visibility
        )
        if not self._safedeletion_filter_applied and visibility in (
            DELETED_INVISIBLE,
            DELETED_VISIBLE_BY_FIELD,
            DELETED_ONLY_VISIBLE,
        ):
            visibility_query = (
                {"deleted": None}
                if visibility in (DELETED_INVISIBLE, DELETED_VISIBLE_BY_FIELD)
                else {"deleted__ne": None}
            )
            query.update(visibility_query)
            self._safedeletion_filter_applied = True

        return super().__call__(q_obj, **query)

    # pylint: disable=arguments-differ
    def all(self, force_visibility=None):
        """Override so related managers can also see the deleted models.

        A model's m2m field does not easily have access to `all_objects` and
        so setting `force_visibility` to True is a way of getting all of the
        models. It is not recommended to use `force_visibility` outside of related
        models because it will create a new queryset.

        Args:
            force_visibility: Force a deletion visibility. (default: {None})
        """

        if force_visibility is not None:
            # pylint: disable=attribute-defined-outside-init
            self._safedeletion_force_visibility = force_visibility
        return super().all()

    def _check_field_filter(self, **kwargs):
        """Check if the visibility for DELETED_VISIBLE_BY_FIELD needs t be put into effect.

        DELETED_VISIBLE_BY_FIELD is a temporary visibility flag that changes
        to DELETED_VISIBLE once asked for the named parameter defined in
        `_safedeletion_force_visibility`. When evaluating the queryset, it will
        then filter on all models.
        """

        if (
            self._safedeletion_visibility == DELETED_VISIBLE_BY_FIELD
            and self._safedeletion_visibility_field in kwargs
        ):
            # pylint: disable=attribute-defined-outside-init
            self._safedeletion_force_visibility = DELETED_VISIBLE

    def filter(self, *q_objs, **query):
        queryset = self.clone()

        # pylint: disable=protected-access
        queryset._check_field_filter(**query)
        return super(SafeDeletionQuerySet, queryset).filter(*q_objs, **query)

    def get(self, *q_objs, **query):
        queryset = self.clone()
        # pylint: disable=protected-access
        queryset._check_field_filter(**query)
        return super(SafeDeletionQuerySet, queryset).get(*q_objs, **query)

    def clone(self):
        clone = super().clone()
        # pylint: disable=protected-access
        clone._safedeletion_visibility = self._safedeletion_visibility
        clone._safedeletion_visibility_field = self._safedeletion_visibility_field
        clone._safedeletion_filter_applied = self._safedeletion_filter_applied
        if hasattr(self, "_safedeletion_force_visibility"):
            # pylint: disable=protected-access
            clone._safedeletion_force_visibility = self._safedeletion_force_visibility
        return clone
