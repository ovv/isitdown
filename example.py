import isitdown
import logging

logging.basicConfig(level=logging.INFO)


def main():
    checks = [
        isitdown.checks.StatusCodeHTTPCheck(url="https://github.com"),
        isitdown.checks.StdoutSSHCommandCheck(
            command="systemctl status haproxy",
            host="foo.bar",
            username="root",
            expected_regex="active \(running\)",
        )
    ]

    app = isitdown.isitdown(*checks)
    app.start(print=False)


if __name__ == "__main__":
    main()
