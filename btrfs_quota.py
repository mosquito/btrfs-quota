#!/usr/bin/env python3

import argparse
import shutil
from collections import defaultdict

import humanize
import re
from pathlib import Path
from subprocess import check_output, check_call
from texttable import Texttable as TexttableBase

parser = argparse.ArgumentParser()
parser.set_defaults(func=lambda _: parser.print_help())


class Texttable(TexttableBase):
    def order_by(self, *names, reverse=False):
        header_dict = {o: i for i, o in enumerate(self._header)}
        indecies = []

        for name in names:
            indecies.append(header_dict[name])

        self._rows = sorted(
            self._rows, key=lambda x: tuple(x[i] for i in indecies),
            reverse=reverse
        )


def parse_table(lines, sep='\t+'):
    exp = re.compile(sep)
    header = lines[0]
    payload = lines[2:]
    fields = exp.split(header)

    for line in payload:
        values = []
        for value in exp.split(line):
            if value == "---":
                value = None
            elif value.lower() == 'none':
                value = None
            elif value.endswith("KiB"):
                value = float(value.replace("KiB", "")) * 1024
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit():
                value = float(value)
            values.append(value)
        yield dict(filter(lambda x: x[0], zip(fields, values)))


def get_qgroups(path):
    output = check_output([
        "btrfs", "qgroup", "show", "-pcre",
        "--sort=-max_excl", "--kbytes", str(path)
    ]).decode().splitlines()
    return parse_table(output, sep=r'\s{1,}')


def get_subvolumes(path):
    output = check_output([
        'btrfs', 'subvolume', 'list', '-tpcg', str(path)
    ]).decode().splitlines()
    return parse_table(output)


def get_subvolume_info(path):
    output = check_output([
        "btrfs", "subvolume", "show", str(path)
    ]).decode().splitlines()

    subvolume = output[0].strip()
    info = {}

    for line in output[1:]:
        key, value = line.split(":", 1)
        info[key.strip()] = value.strip()

    return subvolume, info


def human_size(value):
    if value is None:
        return ''
    return humanize.naturalsize(int(value), binary=True, format="%.0f")


def get_info(path: Path):
    info = defaultdict(dict)

    for subvol in get_subvolumes(path):
        info["0/{}".format(subvol['ID'])].update(subvol)

    for qgroup in get_qgroups(path):
        info[qgroup['qgroupid']].update(qgroup)

    return dict(info)


def command_show(arguments):
    termsize = shutil.get_terminal_size((200, 20))
    table = Texttable(max_width=termsize.columns)
    table.set_deco(Texttable.HEADER)

    table.header([
        "SubvolID", "QGroup", "Excl", "Ref",
        "Max Excl", "Path"
    ])

    for qgroupid, value in get_info(arguments.path).items():
        table.add_row([
            value.get('ID'),
            value.get('qgroupid'),
            human_size(value.get('excl')),
            human_size(value.get('max_rfer')),
            human_size(value.get('max_excl')),
            value.get('path'),
        ])

    table.order_by(*arguments.order_by, reverse=arguments.reverse)
    print(table.draw())


def command_set(arguments):
    for path in arguments.path:
        name, subvol_info = get_subvolume_info(path)
        qgroup = "0/{}".format(subvol_info['Subvolume ID'])

        cmd_head = ["btrfs", "qgroup", "limit"]
        cmd_tail = [arguments.limit, qgroup, str(path.resolve())]

        if not arguments.exclusive or not arguments.compressed:
            arguments.referenced = True

        if arguments.referenced:
            check_call(cmd_head + cmd_tail)

        if arguments.compressed:
            check_call(cmd_head + ["-c"] + cmd_tail)

        if arguments.compressed:
            check_call(cmd_head + ["-e"] + cmd_tail)

    return 0


def path_parser(value: str) -> Path:
    path = Path(value)
    if not path.exists():
        raise argparse.ArgumentTypeError("Path %r doesn't exists" % path)

    return path


subparsers = parser.add_subparsers(help='sub-command help')
parser_info = subparsers.add_parser("show", help='show info')
parser_info.add_argument("-o", "--order-by", nargs="?", default=["Ref", "Excl"])
parser_info.add_argument("-R", "--reverse", action="store_true", default=False)
parser_info.add_argument("path", help="BTRFS mountpoint path", type=path_parser)
parser_info.set_defaults(func=command_show)

parser_set = subparsers.add_parser("set", help='set quota')
parser_set.add_argument("-e", "--exclusive", action="store_true")
parser_set.add_argument("-c", "--compressed", action="store_true")
parser_set.add_argument("-r", "--referenced", action="store_true")
parser_set.add_argument("limit", help="Quota limit")
parser_set.add_argument("path", help="BTRFS mountpoint path", type=path_parser,
                        nargs="+")
parser_set.set_defaults(func=command_set)


def main():
    arguments = parser.parse_args()
    result = arguments.func(arguments)

    if isinstance(result, int) and result >= 0:
        exit(result)


if __name__ == '__main__':
    main()

