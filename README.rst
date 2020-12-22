================================
Django Safe Deletion Mongoengine
================================

THIS PROJECT CURRENTLY IS UNSTABLE

Right now we're targeting to get things working on Django 3.0,
Mongoengine 0.22.0 and Django Mongoengine 0.4.4 support,
but not tested in production.

What is it ?
------------

This library is similar to `Django Safedelete <https://github.com/makinacorpus/django-safedelete>`_,
but it is compatible for `Django Mongoengine <https://github.com/mongoengine/django-mongoengine>`_.
You can refer document at `https://django-safedelete.readthedocs.io <https://django-safedelete.readthedocs.io/>`_.


Example
-------

.. code::

    # imports
    from mongoengine import CASCADE, fields
    from safedeletion_mongoengine.documents import SafeDeletionDocument
    from safedeletion_mongoengine.config import HARD_DELETE_NOCASCADE

    # Documents

    # We create a new document, with the given policy : Objects will be hard-deleted,
    # or soft deleted if other objects would have been deleted too.

    class Article(SafeDeletionDocument):
        _safedeletion_policy = HARD_DELETE_NOCASCADE

        name = fields.StringField(max_length=100)

    class Order(SafeDeletionDocument):
        _safedeletion_policy = HARD_DELETE_NOCASCADE

        name = fields.StringField(max_length=100)
        articles = fields.ReferenceField(Article, reverse_delete_rule=CASCADE)


    # Example of use

    >>> article1 = Article(name='article1')
    >>> article1.save()

    >>> article2 = Article(name='article2')
    >>> article2.save()

    >>> order = Order(name='order')
    >>> order.save()
    >>> order.articles.add(article1)

    # This article will be masked, but not deleted from the database as it is still referenced
    # in an order.
    >>> article1.delete()

    # This article will be deleted from the database.
    >>> article2.delete()


Compatibilities
---------------

*  Django 3.0 using python 3.6 to 3.8.


Installation
------------

Clone this repository and copy the folder ``safedeletion_mongoengine`` to your Django project as an app

Add ``safedeletion_mongoengine`` in your ``INSTALLED_APPS``:

.. code::

    INSTALLED_APPS = [
        "django_mongoengine",
        "django_mongoengine.mongo_auth",
        "django_mongoengine.mongo_admin",
        "safedeletion_mongoengine",
        [...]
    ]


Licensing
---------

Please see the LICENSE file.

Contacts
--------

Please see the AUTHORS file.
