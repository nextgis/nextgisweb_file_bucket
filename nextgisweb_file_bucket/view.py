from nextgisweb.jsrealm import jsentry
from nextgisweb.resource import Resource, Widget
from nextgisweb.resource.view import resource_sections

from .model import FileBucket


class FileBucketWidget(Widget):
    resource = FileBucket
    operation = ("create", "update")
    amdmod = jsentry("@nextgisweb/file-bucket/resource-widget")


@resource_sections("@nextgisweb/file-bucket/resource-section")
def resource_section(obj: Resource, **kwargs) -> bool:
    return isinstance(obj, FileBucket)
