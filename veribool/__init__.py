import code
from argparse import ArgumentParser

import veribool
import veribool.compiler as vc
import veribool.verifier as vv

__description = "Verify various properties of boolean expressions using a concise DSL."


def gen_truth_table(args):
    print(*vv.generate_truth_table(args.expr), sep="\n")


def diff_exprs(args):
    divergence = vv.find_divergence(args.expr1, args.expr2)
    if divergence is None:
        exit(0)
    print(divergence)
    exit(2)


def compile_expr(args):
    vc.set_dbg(True)
    vnames, fn = vc.full_compile(args.expr)
    if not args.interactive:
        return
    code.interact(local={"vnames": vnames, "fn": fn, "veribool": veribool})


def main():
    parser = ArgumentParser(description=__description)
    subparsers = parser.add_subparsers()

    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")

    truth_parser = subparsers.add_parser("truth", help="generate truth table")
    truth_parser.add_argument("expr", type=str, help="boolean expression")
    truth_parser.set_defaults(func=gen_truth_table)

    diff_parser = subparsers.add_parser(
        "diff", help="find inputs where two expressions differ"
    )
    diff_parser.add_argument("expr1")
    diff_parser.add_argument("expr2")
    diff_parser.set_defaults(func=diff_exprs)

    cmp_parser = subparsers.add_parser("compile", help="compile expression to python")
    cmp_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="launch shell afterwards (run dir())",
    )
    cmp_parser.add_argument("expr")
    cmp_parser.set_defaults(func=compile_expr)

    args = parser.parse_args()
    if "func" not in args:
        parser.print_help()
        exit(1)

    vc.set_dbg(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
