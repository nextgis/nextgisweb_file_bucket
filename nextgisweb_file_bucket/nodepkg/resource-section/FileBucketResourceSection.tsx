import { useMemo } from "react";

import { Table } from "@nextgisweb/gui/antd";
import type { TableColumnProps } from "@nextgisweb/gui/antd";
import { formatSize } from "@nextgisweb/gui/util";
import { assert } from "@nextgisweb/jsrealm/error";
import { routeURL } from "@nextgisweb/pyramid/api";
import { gettext } from "@nextgisweb/pyramid/i18n";
import type { ResourceSection } from "@nextgisweb/resource/resource-section";

export const FileBucketResourceSection: ResourceSection = ({
  resourceData,
}) => {
  const files = resourceData.file_bucket?.files;
  assert(files);

  type Record = (typeof files)[number];

  const columns = useMemo<TableColumnProps<Record>[]>(() => {
    return [
      {
        key: "name",
        title: gettext("Name"),
        dataIndex: "name",
        render: (value) => (
          <a
            target="_blank"
            href={routeURL("resource.file_download", {
              id: resourceData.resource.id,
              name: value,
            })}
          >
            {value}
          </a>
        ),
      },
      {
        key: "mime_type",
        title: gettext("MIME type"),
        dataIndex: "mime_type",
      },
      {
        key: "size",
        title: gettext("Size"),
        dataIndex: "size",
        align: "end",
        render: (value) => formatSize(value),
      },
    ];
  }, [resourceData]);

  return (
    <Table
      style={{ width: "100%" }}
      size="middle"
      card={true}
      columns={columns}
      dataSource={files}
      rowKey="name"
    />
  );
};

FileBucketResourceSection.displayName = "FileBucketResourceSection";
