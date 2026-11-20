"""Console entry point required by the browser native-messaging protocol."""

from browser_bridge import run_native_host


if __name__ == "__main__":
    run_native_host()
