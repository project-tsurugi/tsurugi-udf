import os
import sys
import json

from udf_plugin_viewer.descriptors import (
    ServiceDescriptor,
    FunctionDescriptor,
    RecordDescriptor,
    ColumnDescriptor,
)
from . import udf_plugin


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <path_to_plugin.so>")
        sys.exit(1)

    path = sys.argv[1]
    services = udf_plugin.load_plugin(path)
    json_output = json.dumps(services, indent=2)
    print(json_output)
