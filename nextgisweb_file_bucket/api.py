import zipstream
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response

from nextgisweb.pyramid.tomb import UnsafeFileResponse
from nextgisweb.resource import DataScope

from .model import FileBucket, FileBucketFile


def file_download(resource, request):
    request.resource_permission(DataScope.read)

    fname = request.matchdict["name"]
    fobj = FileBucketFile.filter_by(file_bucket_id=resource.id, name=fname).one_or_none()
    if fobj is None:
        raise HTTPNotFound()

    return UnsafeFileResponse(fobj.path, content_type=fobj.mime_type, request=request)


def export(resource, request):
    request.resource_permission(DataScope.read)

    zip_stream = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED, allowZip64=True)
    for f in resource.files:
        zip_stream.write(f.path, arcname=f.name)

    return Response(
        app_iter=zip_stream,
        content_type="application/zip",
        content_disposition='attachment; filename="%d.zip"' % resource.id,
    )


def setup_pyramid(comp, config):
    config.add_view(
        file_download,
        route_name="resource.file_download",
        context=FileBucket,
        request_method="GET",
    )

    config.add_view(
        export,
        route_name="resource.export",
        context=FileBucket,
        request_method="GET",
    )
