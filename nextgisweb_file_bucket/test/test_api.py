import zipfile
from io import BytesIO

import pytest
import webtest

from nextgisweb.resource.test import ResourceAPI

pytestmark = pytest.mark.usefixtures("ngw_resource_defaults", "ngw_auth_administrator")

TEST_FILE1 = {"name": "rose.flw", "content": b"rose"}
TEST_FILE2 = {"name": "orchid.flw", "content": b"orchid"}
TEST_FILE3 = {"name": "daisy.flw", "content": b"daisy"}


def test_bucket_crud(ngw_webtest_app):
    rapi = ResourceAPI(ngw_webtest_app)

    resp = ngw_webtest_app.post(
        "/api/component/file_upload/",
        data=[
            ["files[]", webtest.Upload(TEST_FILE1["name"], TEST_FILE1["content"])],
            ["files[]", webtest.Upload(TEST_FILE2["name"], TEST_FILE2["content"])],
            ["files[]", webtest.Upload(TEST_FILE3["name"], TEST_FILE3["content"])],
        ],
    )

    res_id = rapi.create(
        "file_bucket",
        {"file_bucket": {"files": resp.json["upload_meta"]}},
    )

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE1['name']}")
    assert resp.body == TEST_FILE1["content"]

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE2['name']}")
    assert resp.body == TEST_FILE2["content"]

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE3['name']}")
    assert resp.body == TEST_FILE3["content"]

    rapi.update_request(res_id, {"file_bucket": {"files": [{"name": "iam/../bad"}]}}, status=422)

    rapi.update(res_id, {"file_bucket": {"files": [{"name": TEST_FILE1["name"]}]}})
    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE1['name']}", status=200)
    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE2['name']}", status=404)

    resp = ngw_webtest_app.post(
        "/api/component/file_upload/",
        data={"file": webtest.Upload(TEST_FILE1["name"], TEST_FILE1["content"])},
    )

    rapi.update_request(res_id, {"file_bucket": {"files": resp.json["upload_meta"]}})

    rapi.delete(res_id)
    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE3['name']}", status=404)


def test_archive(ngw_webtest_app):
    rapi = ResourceAPI(ngw_webtest_app)
    ngw_webtest_app.authorization = ("Basic", ("administrator", "admin"))

    def make_archive(files):
        data = BytesIO()
        with zipfile.ZipFile(
            data,
            mode="a",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=False,
        ) as archive:
            for f in files:
                archive.writestr(f["name"], f["content"])
        data.seek(0)

        resp = ngw_webtest_app.put("/api/component/file_upload/", data=data.read())
        return resp.json

    a1 = make_archive([TEST_FILE1, TEST_FILE2])

    bucket_data = {"file_bucket": {"archive": a1, "files": []}}
    rapi.create_request("file_bucket", bucket_data, status=422)

    del bucket_data["file_bucket"]["files"]
    res_id = rapi.create("file_bucket", bucket_data)

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE1['name']}")
    assert resp.content_type == "text/plain"
    assert resp.body == TEST_FILE1["content"]

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE2['name']}")
    assert resp.content_type == "text/plain"
    assert resp.body == TEST_FILE2["content"]

    a2 = make_archive([TEST_FILE2, TEST_FILE3])
    rapi.update(res_id, {"file_bucket": {"archive": a2}})

    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE1['name']}", status=404)
    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE2['name']}", status=200)
    ngw_webtest_app.get(f"/api/resource/{res_id}/file/{TEST_FILE3['name']}", status=200)

    resp = ngw_webtest_app.get(f"/api/resource/{res_id}/export", status=200)
    with zipfile.ZipFile(
        BytesIO(resp.body),
        mode="r",
        compression=zipfile.ZIP_DEFLATED,
        allowZip64=False,
    ) as archive:
        assert archive.read(TEST_FILE2["name"]) == TEST_FILE2["content"]
        assert archive.read(TEST_FILE3["name"]) == TEST_FILE3["content"]

    ngw_webtest_app.delete(f"/api/resource/{res_id}", status=200)
