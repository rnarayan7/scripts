#!/opt/homebrew/bin/python3

import argparse
import os.path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import structlog
import logging
import humanize
from tabulate import tabulate

SOURCE_DIRNAME = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(SOURCE_DIRNAME, "config.json")
DATA_DIR = os.path.join(SOURCE_DIRNAME, "data")

logger = structlog.get_logger(__name__)


def read_file(path: str) -> Dict:
    """Read a file."""
    with open(path, "r") as f:
        return json.load(f)


class Pomodoro:
    """Class for tracking Pomodoro work sessions."""

    activity: str
    time: datetime
    path: str
    data: Dict[str, Any]

    def __init__(self, time: datetime, activity: Optional[str]) -> None:
        """
        Initialize the Pomodoro class.

        :param activity: Type of activity being done.
        :param time: Time for the session log.
        """
        self.time = time
        self.path = os.path.join(DATA_DIR, f"{time.date().isoformat()}.json")
        self.data = (
            read_file(self.path)
            if os.path.exists(self.path)
            else {"date": time.date().isoformat()}
        )
        self.date = self.data["date"]
        self.activity_log = self.data.get("activities", {})
        self.activity = activity
        self.logger = logger.bind(
            date=humanize.naturaldate(self.time), time=humanize.naturaltime(self.time)
        )
        if self.activity:
            self.logger.bind(activity=self.activity)

    def start(self) -> None:
        """Start a session."""
        if (
            self.activity in self.activity_log
            and self.activity_log[self.activity][-1]["action"] != "stop"
        ):
            self.logger.warning(
                "Session in-progress", session=self.activity_log[self.activity][-1]
            )
            return
        self._add_action("start")

    def stop(self) -> None:
        """Stop a session."""
        if (
            self.activity not in self.activity_log
            or self.activity_log[self.activity][-1]["action"] != "start"
        ):
            self.logger.warning("No active session found for this activity.")
            return
        self._add_action("stop")

    def recap(self) -> None:
        """Recap the day."""
        self.logger.info("Recapping the day.")
        recap_table = []
        for activity in self.activity_log:
            actions = self.activity_log[activity]
            num_finished_sessions = len(actions) // 2
            num_unfinished_sessions = len(actions) % 2
            total_time = timedelta(0)
            for session in range(num_finished_sessions):
                start_time = datetime.fromisoformat(actions[session * 2]["time"])
                end_time = datetime.fromisoformat(actions[session * 2 + 1]["time"])
                total_time += end_time - start_time
            if num_unfinished_sessions:
                start_time = datetime.fromisoformat(actions[-1]["time"])
                total_time += self.time - start_time
            recap_table.append(
                [
                    activity,
                    humanize.precisedelta(total_time),
                    num_finished_sessions,
                    num_unfinished_sessions,
                ]
            )
        print(
            tabulate(
                recap_table,
                headers=[
                    "Activity",
                    "Total Time",
                    "Finished Sessions",
                    "Ongoing Sessions",
                ],
                tablefmt="fancy_grid",
            )
        )
        self.logger.info("Recap complete.")

    def _add_action(self, action: str) -> None:
        """
        Add an action to the session log.

        :param action: Name of the action to add to the session log.
        """
        self.logger.debug("Adding action.", action=action)
        new_action = {"action": action, "time": self.time.isoformat()}
        self.logger.info(
            "This will add the following action. Are you sure you want to continue?",
            action=action,
        )
        if (
            self.activity in self.activity_log
            and self.activity_log[self.activity][-1] == new_action
        ):
            self.logger.warning(
                "This action is a duplicate of the last action. Skipping.",
                action=action,
                last_action=self.activity_log[self.activity][-1],
            )
        elif self.activity not in self.activity_log:
            self.activity_log[self.activity] = []
        if self._get_approval():
            self.activity_log[self.activity].append(new_action)
            self._write_update()
            self.logger.debug("Added action.", action=action, filepath=self.path)
        else:
            self.logger.debug("Skipping action.")

    def show(self) -> None:
        """Show the session log."""
        self.logger.debug("Showing actions.")
        if self.activity not in self.activity_log:
            self.logger.warning("No actions found for this activity.")
            return
        print(json.dumps(self.activity_log[self.activity], indent=4, sort_keys=False))
        self.logger.debug("Showed actions.")

    @staticmethod
    def _get_approval():
        """
        Get approval from the user.

        :return: Boolean indicating whether the user approved the action.
        """
        return input("Type 'y' to continue: ") == "y"

    def _write_update(self) -> None:
        """Write an update to the session log."""
        self.logger.debug("Writing file.", path=self.path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4, sort_keys=False)
        self.logger.debug("Wrote to file.", path=self.path)


def add_time_subparser(parser: argparse.ArgumentParser) -> None:
    """Add a time subparser to the parser."""
    parser.add_argument(
        "--time",
        type=str,
        help="Time in format HH:MM{AM|PM}",
        default="",
    )


def add_date_subparser(parser: argparse.ArgumentParser) -> None:
    """Add a date subparser to the parser."""
    parser.add_argument(
        "--date",
        type=str,
        help="Date in format MM-DD-YY",
        default="",
    )


def add_activity_subparser(parser: argparse.ArgumentParser, config) -> None:
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
    subparsers = parser.add_subparsers(
        title="subcommands", dest="command", required=True
    )
    start_parser = subparsers.add_parser("start", help="Start a pomodoro session")
    add_time_subparser(start_parser)
    add_date_subparser(start_parser)
    add_activity_subparser(start_parser, config)
    stop_parser = subparsers.add_parser("stop", help="Stop a pomodoro session")
    add_time_subparser(stop_parser)
    add_date_subparser(stop_parser)
    add_activity_subparser(stop_parser, config)
    show_parser = subparsers.add_parser("show", help="Show pomodoro sessions")
    add_date_subparser(show_parser)
    add_activity_subparser(show_parser, config)
    recap_parser = subparsers.add_parser("recap", help="Recap pomodoro sessions")
    add_date_subparser(recap_parser)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def merge_times(time: str, date: str) -> datetime:
    """
    Merge the time and date into a datetime object.

    :param time: Time string in format HH:MM{AM|PM}.
    :param date: Date string in format MM-DD-YY.
    :return: Datetime object.
    """
    if not time and not date:
        return datetime.now().replace(second=0, microsecond=0)
    elif not time:
        return datetime.strptime(date, "%m-%d-%y")
    elif not date:
        return datetime.strptime(time, "%I:%M%p").replace(
            year=datetime.now().year, month=datetime.now().month, day=datetime.now().day
        )
    return datetime.strptime(f"{date} {time}", "%m-%d-%y %I:%M%p")


if __name__ == "__main__":
    """Main function."""
    args = parse_args(read_file(CONFIG_PATH))
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if args.debug else logging.INFO
        ),
    )
    pomodoro = Pomodoro(
        time=merge_times(
            args.time if "time" in args else None, args.date if "date" in args else None
        ),
        activity=args.activity if "activity" in args else None,
    )
    if args.command == "start":
        pomodoro.start()
    elif args.command == "stop":
        pomodoro.stop()
    elif args.command == "show":
        pomodoro.show()
    elif args.command == "recap":
        pomodoro.recap()
