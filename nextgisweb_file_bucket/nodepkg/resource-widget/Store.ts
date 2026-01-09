import { action, computed, observable } from "mobx";

import type {
    FileBucketCreate,
    FileBucketRead,
    FileBucketUpdate,
    FileUploadFileRead,
    FileUploadFileWrite,
} from "@nextgisweb/file-bucket/type/api";
import type { FileMeta } from "@nextgisweb/file-upload/file-uploader";
import type { FileUploadObject } from "@nextgisweb/file-upload/type/api";
import { gettext } from "@nextgisweb/pyramid/i18n";
import type { EditorStore } from "@nextgisweb/resource/type";

let idSeq = 0;

class ResourceFile {
    readonly id = ++idSeq;
    readonly name;
    readonly size: number;
    readonly mime_type: string;
    readonly file: FileUploadObject | null = null;

    constructor({
        name,
        size,
        mime_type,
        file,
    }: FileUploadFileRead & { file?: FileUploadObject }) {
        this.name = name;
        this.size = size;
        this.mime_type = mime_type;
        if (file) {
            this.file = file;
        }
    }
}

export type { ResourceFile };

export class Store implements EditorStore<
    FileBucketRead,
    FileBucketCreate,
    FileBucketUpdate
> {
    readonly identity = "file_bucket";

    @observable.shallow accessor files: ResourceFile[] = [];
    @observable.shallow accessor archive: FileUploadObject | null = null;
    @observable.ref accessor dirty = false;

    @action
    load(value: FileBucketRead) {
        if (value.files) {
            this.files = value.files.map((data) => new ResourceFile(data));
        }
        this.archive = null;
        this.dirty = false;
    }

    dump() {
        if (!this.dirty) return undefined;
        const result: FileBucketCreate | FileBucketUpdate = {};
        if (this.archive) {
            result.archive = this.archive;
        } else {
            const files = this.files.map(({ id, file, ...rest }) =>
                file ? { id: file.id, ...rest } : rest
            ) as FileUploadFileWrite[];
            result.files = files;
        }
        return result;
    }

    get isValid() {
        return true;
    }

    @action
    appendFiles(files: FileMeta[]): [boolean, null] {
        const updated = [...this.files];
        for (const file of files) {
            const { name, size, mime_type } = file;
            const existing = updated.find((c) => c.name === name);
            if (existing) updated.splice(updated.indexOf(existing), 1);
            updated.push(new ResourceFile({ name, size, mime_type, file }));
        }
        this.files = updated;
        this.dirty = true;
        return [true, null];
    }

    @action
    fromArchive(archive: FileUploadObject | null): [boolean, null | string] {
        const { name } = archive || {};
        if (name && !name.toLowerCase().endsWith(".zip")) {
            return [false, gettext("ZIP archive required")];
        }

        this.archive = archive;
        this.dirty = true;
        return [true, null];
    }

    // EdiTable

    @computed
    get rows() {
        return this.files;
    }

    @action
    deleteRow(row: ResourceFile) {
        this.files.splice(this.rows.indexOf(row), 1);
        this.dirty = true;
    }
}
