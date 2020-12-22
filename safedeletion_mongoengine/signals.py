from mongoengine.signals import _signals


pre_softdelete = _signals.signal("pre_softdelete")
post_softdelete = _signals.signal("post_softdelete")
post_undelete = _signals.signal("post_undelete")
