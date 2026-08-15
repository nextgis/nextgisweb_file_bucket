import os
import os.path
import zipfile
from datetime import datetime

import magic
import sqlalchemy as sa
import sqlalchemy.orm as orm
from msgspec import UNSET, Struct, UnsetType
from sqlalchemy.orm import Mapped, mapped_column

from nextgisweb.env import Base, DBSession, gettext
from nextgisweb.lib.datetime import utcnow_naive

from nextgisweb.core.exception import ValidationError
from nextgisweb.file_storage import FileObj
from nextgisweb.file_upload import FileUpload, FileUploadID, FileUploadRef
from nextgisweb.resource import (
    DataScope,
    Resource,
    ResourceGroup,
    ResourceScope,
    SAttribute,
    SColumn,
    Serializer,
)
from nextgisweb.resource.category import MiscellaneousCategory


class FileBucket(Resource):
    identity = "file_bucket"
    cls_display_name = gettext("File bucket")
    cls_category = MiscellaneousCategory

    __scope__ = DataScope

    tstamp: Mapped[datetime | None] = mapped_column(sa.DateTime())

    files: Mapped[list["FileBucketFile"]] = orm.relationship(
        cascade="all,delete-orphan",
        back_populates="file_bucket",
    )

    @classmethod
    def check_parent(cls, parent):
        return isinstance(parent, ResourceGroup)


class FileBucketFile(Base):
    __tablename__ = "file_bucket_file"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_bucket_id: Mapped[int] = mapped_column(sa.ForeignKey(FileBucket.id))
    fileobj_id: Mapped[int] = mapped_column(sa.ForeignKey(FileObj.id))
    name: Mapped[str] = mapped_column(sa.Unicode(255))
    mime_type: Mapped[str] = mapped_column(sa.Unicode)
    size: Mapped[int] = mapped_column(sa.BigInteger)

    __table_args__ = (sa.UniqueConstraint("file_bucket_id", "name"),)

    file_bucket: Mapped[FileBucket] = orm.relationship(back_populates="files")

    fileobj: Mapped[FileObj] = orm.relationship(lazy="joined")

    @property
    def path(self):
        return self.fileobj.filename()


def validate_filename(filename):
    # Проверяем на вещи типа ".." в имени файла или "/" в начале.
    return not os.path.isabs(filename) and filename == os.path.normpath(filename)


class ArchiveAttr(SAttribute):
    def set(self, srlzr: Serializer, value: FileUploadRef, *, create: bool):
        assert isinstance(srlzr.obj, FileBucket)
        srlzr.obj.tstamp = utcnow_naive()
        srlzr.obj.files[:] = []
        DBSession.flush()

        with zipfile.ZipFile(value().data_path, mode="r", allowZip64=True) as archive:
            for file_info in archive.infolist():
                if file_info.is_dir():
                    continue

                if not validate_filename(file_info.filename):
                    raise ValidationError(message="Insecure filename.")

                with archive.open(file_info, "r") as sf:
                    mime_type = magic.from_buffer(sf.read(1024), mime=True)
                    sf.seek(0)
                    fileobj = FileObj().copy_from(sf)

                filebucketfileobj = FileBucketFile(
                    name=file_info.filename,
                    size=file_info.file_size,
                    mime_type=mime_type,
                    fileobj=fileobj,
                )

                srlzr.obj.files.append(filebucketfileobj)


class FileUploadFileRead(Struct, kw_only=True):
    name: str
    size: int
    mime_type: str


class FileUploadFileWrite(Struct, kw_only=True):
    name: str
    id: FileUploadID | UnsetType = UNSET


class FilesAttr(SAttribute):
    def get(self, srlzr: Serializer) -> list[FileUploadFileRead]:
        assert isinstance(srlzr.obj, FileBucket)
        return [
            FileUploadFileRead(name=f.name, size=f.size, mime_type=f.mime_type)
            for f in sorted(srlzr.obj.files, key=lambda f: f.name)
        ]

    def set(self, srlzr: Serializer, value: list[FileUploadFileWrite], *, create: bool):
        assert isinstance(srlzr.obj, FileBucket)
        srlzr.obj.tstamp = utcnow_naive()

        files_info: dict[str, FileUploadFileWrite] = dict()
        for f in value:
            if not validate_filename(f.name):
                raise ValidationError(message="Insecure filename.")
            files_info[f.name] = f

        removed_files = list()
        for filebucket_file in srlzr.obj.files:
            if filebucket_file.name not in files_info:  # Removed file
                removed_files.append(filebucket_file)
            else:
                file_info = files_info.pop(filebucket_file.name)
                if file_info.id is not UNSET:
                    fupload = FileUpload(id=file_info.id)
                    filebucket_file.fileobj = fupload.to_fileobj()
                else:  # Untouched file
                    pass

        for f in removed_files:
            srlzr.obj.files.remove(f)

        for name, file_info in files_info.items():  # New file
            assert file_info.id is not UNSET
            fupload = FileUpload(id=file_info.id)
            filebucket_file = FileBucketFile(
                name=name,
                size=fupload.size,
                mime_type=fupload.mime_type,
                fileobj=fupload.to_fileobj(),
            )

            srlzr.obj.files.append(filebucket_file)


class FileBucketSerializer(Serializer, resource=FileBucket):
    archive = ArchiveAttr(read=None, write=ResourceScope.update)
    files = FilesAttr(read=DataScope.read, write=DataScope.write)
    tstamp = SColumn(read=ResourceScope.read, write=None)

    def deserialize(self):
        if self.data.files is not UNSET and self.data.archive is not UNSET:  # ty: ignore[unresolved-attribute]
            raise ValidationError("'files' and 'archive' attributes should not pass together.")
        super().deserialize()
