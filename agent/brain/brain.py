import argparse
import ctypes as C
import errno
import json
import os
from pathlib import Path
import sys
import urllib.request


class CoreInfo(C.Structure):
    _fields_ = [
        ("pid", C.c_int64),
        ("cpus", C.c_int32),
        ("page_size", C.c_int32),
        ("host", C.c_char * 256),
    ]


def error_text(code):
    if sys.platform == "win32":
        return C.FormatError(code)
    return os.strerror(code)


def load_core(path):
    core = C.CDLL(str(path.resolve()))
    core.core_get_info.argtypes = [C.POINTER(CoreInfo)]
    core.core_get_info.restype = C.c_int
    return core


def get_info(core):
    info = CoreInfo()
    error = core.core_get_info(C.byref(info))
    if error:
        raise OSError(error, error_text(error))
    return {
        "event": "agent_started",
        "os": sys.platform,
        "pid": info.pid,
        "cpus": info.cpus,
        "page_size": info.page_size,
        "host": info.host.decode("utf-8", errors="replace"),
    }


def send(message, url):
    data = json.dumps(message, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.status, response.read().decode("utf-8")


def main():
    lib_names = {
        "win32": "sentry_core.dll",
        "darwin": "libsentry_core.dylib",
    }
    name = lib_names.get(sys.platform, "libsentry_core.so")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "core" / name,
    )
    parser.add_argument("--check-null", action="store_true")
    parser.add_argument("--layout", action="store_true")
    parser.add_argument("url", nargs="?", help="URL вебхука n8n для отправки JSON")
    args = parser.parse_args()

    core = load_core(args.library)

    if args.check_null:
        error = core.core_get_info(None)
        print(f"NULL: {error} ({error_text(error)})")
        expected = 87 if sys.platform == "win32" else errno.EINVAL
        return 0 if error == expected else 1

    if args.layout:
        offsets = [getattr(CoreInfo, field).offset for field, _ in CoreInfo._fields_]
        print(f"sizeof: {C.sizeof(CoreInfo)}, offsets: {' '.join(map(str, offsets))}")
        return 0

    message = get_info(core)
    print(json.dumps(message, ensure_ascii=False, indent=2))

    if args.url:
        status, body = send(message, args.url)
        print("n8n:", status, body)

    return 0


if __name__ == "__main__":
    sys.exit(main())
