/** @plugin */
import { route } from "@nextgisweb/pyramid/api";
import { gettext } from "@nextgisweb/pyramid/i18n";
import { registerResourceAction } from "@nextgisweb/resource/resource-section/registry";
import { hasExportPermission } from "@nextgisweb/resource/util/hasExportPermission";

import ExportIcon from "@nextgisweb/icon/material/download";

registerResourceAction(COMP_ID, {
  key: "export",
  icon: <ExportIcon />,
  label: gettext("Export"),
  menu: { order: 60, group: "resource" },
  attributes: [
    ["resource.has_permission", "data.read"],
    ["resource.has_permission", "data.write"],
  ],
  condition: (it) => {
    if (it.get("resource.cls") !== "file_bucket") {
      return false;
    }

    return hasExportPermission(it);
  },
  href: (it) => route("resource.export", it.id).url(),
});
