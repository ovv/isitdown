import logging
import isitdown

logging.basicConfig(level=logging.INFO)


def main():

    logging_notifier = isitdown.notifiers.LoggingNotifier(notify_after=(1, 3, 5))

    checks = [
        isitdown.checks.StatusCodeHTTPCheck(
            url="https://github.com", startup_delay=10, check_interval=20
        ),
        isitdown.checks.StdoutSSHCommandCheck(
            command="systemctl status haproxy",
            host="foo.bar",
            username="root",
            expected_regex="active \(running\)",
        ),
        # Failure example with backoff
        isitdown.checks.StatusCodeHTTPCheck(
            url="https://foo.bar", check_interval=2, notifiers=(logging_notifier,)
        ),
    ]

    app = isitdown.isitdown(*checks)
    app.start(print=False)


if __name__ == "__main__":
    main()
