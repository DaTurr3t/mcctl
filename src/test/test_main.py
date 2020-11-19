# pylint: skip-file
import unittest
import inspect
from mcctl.__main__ import get_parser


def get_missing(unfiltered_kwargs, func):
    sig = inspect.signature(func)
    func_params = [param.name for param in sig.parameters.values(
    ) if param.kind == param.POSITIONAL_OR_KEYWORD]

    missing_params = []
    for func_param in func_params:
        if func_param not in unfiltered_kwargs.keys():
            missing_params.append(func_param)
    missing_kwargs = []
    for kwarg in unfiltered_kwargs.keys():
        if kwarg not in func_params:
            missing_kwargs.append(kwarg)
    return (missing_kwargs, missing_params)


class TestParserMappings(unittest.TestCase):
    param_base = ['verbose', 'func', 'err_template', 'elevation']
    parser = get_parser()

    def test_attach(self):
        args = self.parser.parse_args("attach testserver".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_config(self):
        args = self.parser.parse_args(
            "config testserver -p motd=TestServer".split())
        kwargs, params = get_missing(vars(args), args.func)
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_create(self):
        args = self.parser.parse_args(
            "create mcserver vanilla:latest -m 4G".split())
        kwargs, params = get_missing(vars(args), args.func)
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_exec(self):
        args = self.parser.parse_args("exec test say Testing...".split())
        kwargs_ok = ['pollrate', 'max_retries', 'max_flush_retries']
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, kwargs_ok)

    def test_export(self):
        args = self.parser.parse_args("export testserver".split())
        kwargs_ok = ['zip_path']
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, kwargs_ok)

    def test_inspect(self):
        args = self.parser.parse_args("inspect testserver -n 10".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_ls(self):
        args = self.parser.parse_args("ls".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_pull(self):
        args = self.parser.parse_args("pull vanilla:latest".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_rename(self):
        args = self.parser.parse_args("rename testserver testsrv".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_restart(self):
        args = self.parser.parse_args("restart testserver -m yeet".split())
        kwargs_ok = ['persistent']
        params_ok = []
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, kwargs_ok)

    def test_rm(self):
        args = self.parser.parse_args("rm testserver".split())
        kwargs_ok = ['confirm']
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, kwargs_ok)

    def test_rmj(self):
        args = self.parser.parse_args("create mcserver vanilla:1.16.2".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_start(self):
        args = self.parser.parse_args("start testserver".split())
        kwargs_ok = ['message']
        params_ok = []
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, kwargs_ok)

    def test_stop(self):
        args = self.parser.parse_args("stop testserver".split())
        params_ok = []
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_update(self):
        args = self.parser.parse_args(
            "update testserver vanilla:latest".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])

    def test_shell(self):
        args = self.parser.parse_args("shell testserver".split())
        params_ok = ["action"]
        params_ok.extend(self.param_base)
        kwargs, params = get_missing(vars(args), args.func)
        self.assertListEqual(sorted(kwargs), sorted(params_ok))
        self.assertListEqual(params, [])
