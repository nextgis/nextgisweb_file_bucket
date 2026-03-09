from nextgisweb.jsrealm import jsentry
from nextgisweb.resource import Widget
from nextgisweb.resource.view import resource_sections

from .model import FileBucket


class FileBucketWidget(Widget):
    resource = FileBucket
    operation = ("create", "update")
    amdmod = jsentry("@nextgisweb/file-bucket/resource-widget")


@resource_sections("@nextgisweb/file-bucket/resource-section")
def resource_section(obj, **kwargs):
    return isinstance(obj, FileBucket)


def setup_pyramid(comp, config):
    pass
