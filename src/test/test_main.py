# pylint: skip-file
import unittest
import inspect
from mcctl.__main__ import get_parser


def get_missing(unfiltered_kwargs, func):
    sig = inspect.signature(func)
    filter_keys = [param.name for param in sig.parameters.values(
    ) if param.kind == param.POSITIONAL_OR_KEYWORD]

    filtered_keys = []
    for filter_key in filter_keys:
        try:
            param = unfiltered_kwargs[filter_key]
        except KeyError:
            filtered_keys.append(filter_key)
    return filtered_keys


class TestParserMappings(unittest.TestCase):

    parser = get_parser()

    def test_attach(self):
        args = self.parser.parse_args("attach testserver".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_config(self):
        args = self.parser.parse_args(
            "config testserver -p motd=TestServer".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_create(self):
        args = self.parser.parse_args(
            "create mcserver vanilla:latest -m 4G".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_exec(self):
        args = self.parser.parse_args("exec test say Testing...".split())
        ok = ['pollrate', 'max_retries', 'max_flush_retries']
        self.assertListEqual(get_missing(vars(args), args.func), ok)

    def test_export(self):
        args = self.parser.parse_args("export testserver".split())
        ok = ['zip_path']
        self.assertListEqual(get_missing(vars(args), args.func), ok)

    def test_inspect(self):
        args = self.parser.parse_args("inspect testserver -n 10".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_ls(self):
        args = self.parser.parse_args("ls".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_pull(self):
        args = self.parser.parse_args("pull vanilla:latest".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_rename(self):
        args = self.parser.parse_args("rename testserver testsrv".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_restart(self):
        args = self.parser.parse_args("restart testserver -m yeet".split())
        ok = ['persistent']
        self.assertListEqual(get_missing(vars(args), args.func), ok)

    def test_rm(self):
        args = self.parser.parse_args("rm testserver".split())
        ok=['confirm']
        self.assertListEqual(get_missing(vars(args), args.func), ok)

    def test_rmj(self):
        args = self.parser.parse_args("create mcserver vanilla:1.16.2".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_start(self):
        args = self.parser.parse_args("start testserver".split())
        ok = ['reason']
        self.assertListEqual(get_missing(vars(args), args.func), ok)

    def test_stop(self):
        args = self.parser.parse_args("stop testserver".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_update(self):
        args = self.parser.parse_args(
            "update testserver vanilla:latest".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])

    def test_shell(self):
        args = self.parser.parse_args("shell testserver".split())
        self.assertListEqual(get_missing(vars(args), args.func), [])
