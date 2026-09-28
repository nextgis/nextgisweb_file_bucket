from nextgisweb.env import Component


class FileBucketComponent(Component):
    def setup_pyramid(self, config) -> None:
        from . import api, view  # NOQA

        api.setup_pyramid(self, config)
