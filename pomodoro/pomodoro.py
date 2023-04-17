#!/usr/bin/env /usr/local/bin/python3

import argparse
import os.path
from datetime import datetime
from typing import Dict, Any
import json
import structlog

SOURCE_DIRNAME = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(SOURCE_DIRNAME, "config.json")
DATA_DIR = os.path.join(SOURCE_DIRNAME, "data")

logger = structlog.get_logger(__name__)


class Pomodoro:
    """Class for tracking Pomodoro work sessions."""

    work: str
    time: datetime
    path: str
    actions: Dict[str, Any]

    def __init__(self, work: str, time: datetime) -> None:
        """
        Initialize the Pomodoro class.

        :param work: Type of work being done.
        :param time: Time for the session log.
        """
        self.time = time
        self.work = work
        self.path = os.path.join(DATA_DIR, f"{time.date().isoformat()}.json")
        self.data = (
            self._read_file(self.path)
            if os.path.exists(self.path)
            else {"date": time.date().isoformat()}
        )

    def start(self) -> None:
        """Start a work session."""
        self._add_action("start")

    def stop(self) -> None:
        """Stop a work session."""
        if self.work not in self.data or self.data[self.work][-1]["action"] != "start":
            raise ValueError("Cannot stop work that has not been started.")
        self._add_action("stop")

    def _add_action(self, action: str) -> None:
        """
        Add an action to the session log.

        :param action: Name of the action to add to the session log.
        """
        logger.info("Adding action.", action=action, work=self.work, time=self.time)
        new_action = {"action": action, "time": self.time.isoformat()}
        logger.info(
            "This will add the following action. Are you sure you want to continue?",
            action=action,
            work=self.work,
            time=self.time,
        )
        if self.data[self.work] and self.data[self.work][-1] == new_action:
            raise ValueError("Action already exists.")
        if self._get_approval():
            self.data[self.work].append(new_action)
            self._write_update()
            logger.info(
                "Added action.",
                action=action,
                work=self.work,
                time=self.time,
                filepath=self.path,
            )
        else:
            logger.info("Skipping action.")

    def show(self) -> None:
        """Show the session log."""
        logger.info("Showing actions.", work=self.work, time=self.time)
        print(json.dumps(self.data[self.work], indent=4))
        logger.info("Showed actions.", work=self.work, time=self.time)

    @staticmethod
    def _get_approval():
        """
        Get approval from the user.

        :return: Boolean indicating whether the user approved the action.
        """
        return input("Type 'y' to continue: ") == "y"

    @staticmethod
    def _read_file(path: str) -> Dict:
        """Read a file."""
        logger.info("Reading file.", path=path)
        with open(path, "r") as f:
            return json.load(f)

    def _write_update(self) -> None:
        """Write an update to the session log."""
        logger.info("Writing file.", path=self.path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f)
        logger.info("Wrote to file.", path=self.path)


def read_config(path: str = CONFIG_PATH) -> Dict:
    """Read the config file."""
    with open(path, "r") as f:
        return json.load(f)


def add_time_subparser(parser: argparse.ArgumentParser) -> None:
    """Add a time subparser to the parser."""
    parser.add_argument(
        "--time",
        type=str,
        help="Time in format HH:MM{AM|PM}",
        default=datetime.now().strftime("%I:%M%p"),
    )


def add_date_subparser(parser: argparse.ArgumentParser) -> None:
    """Add a date subparser to the parser."""
    parser.add_argument(
        "--date",
        type=str,
        help="Date in format MM-DD-YY",
        default=datetime.now().strftime("%m-%d-%y"),
    )


def add_activity_subparser(parser: argparse.ArgumentParser, config: Dict) -> None:
    """Add an activity subparser to the parser."""
    parser.add_argument(
        "activity",
        type=str,
        help="Activity for the pomodoro session",
        choices=config["activities"],
    )


def parse_args(config: Dict) -> argparse.Namespace:
    """
    Parse the command line arguments.

    :param config: Configuration dictionary.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    start_parser = subparsers.add_parser("start", help="Start a pomodoro session")
    add_time_subparser(start_parser)
    stop_parser = subparsers.add_parser("stop", help="Stop a pomodoro session")
    add_time_subparser(stop_parser)
    show_parser = subparsers.add_parser("show", help="Show pomodoro sessions")
    add_date_subparser(show_parser)
    add_activity_subparser(start_parser, config)
    add_activity_subparser(stop_parser, config)
    add_activity_subparser(show_parser, config)
    return parser.parse_args()


if __name__ == "__main__":
    """Main function."""
    args = parse_args(read_config())
    pomodoro = Pomodoro(args.activity, args.time or args.date)
    if args.command == "start":
        pomodoro.start()
    elif args.command == "stop":
        pomodoro.stop()
    elif args.command == "show":
        pomodoro.show()
