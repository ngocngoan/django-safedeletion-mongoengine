from mongoengine import CASCADE, fields
from safedeletion_mongoengine.config import (
    DELETED_VISIBLE_BY_PK,
    HARD_DELETE,
    HARD_DELETE_NOCASCADE,
    SOFT_DELETE,
)
from safedeletion_mongoengine.managers import SafeDeletionQuerySetManager
from safedeletion_mongoengine.documents import SafeDeletionDocument


class Author(SafeDeletionDocument):
    _safedeletion_mongoengine_policy = HARD_DELETE_NOCASCADE


class CategoryManager(SafeDeletionQuerySetManager):
    _safedeletion_mongoengine_visibility = DELETED_VISIBLE_BY_PK


class Category(SafeDeletionDocument):
    _safedeletion_mongoengine_policy = SOFT_DELETE

    name = fields.StringField(max_length=100, blank=True)

    def __str__(self):
        return self.name


# Explicitly use SafeDeletionDocument instead of SafeDeletionDocument to test both
class Article(SafeDeletionDocument):
    _safedeletion_mongoengine_policy = HARD_DELETE

    author = fields.ReferenceField(Author, reverse_delete_rule=CASCADE)
    category = fields.ReferenceField(
        Category, reverse_delete_rule=CASCADE, null=True, default=None
    )
