# VeriBool

Verify properties of boolean expressions using a concise DSL.

<p align="center">
<img src="./assets/logo.webp" alt="logo" />
</p>

> I _know_ you just want to press that button

## Installation

```shell
python3 -m pip install veribool
```

## Usage

```
# directly compile the expression to a python lambda expression
# add the -i/--interactive flag to drop into a python interpreter with
# fn = <the boolean expression as a lambda>
$: veribool compile "x'y' + x'z + xyz"
lambda x, y, z, **_kwargs: (((not x) and (not y)) or (((not x) and z) or (x and y and z)))

# find a diverging input for two boolean expressions
$: veribool diff "x xnor (yz)" "x'y' + x'z + xyz"
[0, 1, 0] - True vs False

# $? == 0 if expressions match
$: veribool diff "x xnor (yz)" "x'y' + x'z' + xyz" && echo equal
equal

# generate truth table
$: veribool truth "x xnor (yz)"
[0, 0, 0] - True
[0, 0, 1] - True
[0, 1, 0] - True
[0, 1, 1] - False
[1, 0, 0] - False
[1, 0, 1] - False
[1, 1, 0] - False
[1, 1, 1] - True
```

### DSL

This project implements a compiler for a boolean expression DSL closely modeling mathematical
boolean algebra notation.

Rules:
* each variable is 1 case-sensitive alphabetical character
* parenthesis exist
* `x'` is the complement of `x`
* `xy` is the `and` of `x` and `y`
* `x + y` is the `or` of `x` and `y`
* `x ^ y` and `x xor y` are the `xor` of `x` and `y`
* `x xnor y` is the `xnor` of `x` and `y`
* order of operations is: `parenthesis`, `not`, `and` followed by the rest of the operators

## Roadmap

- [ ] use z3 as a backend
- [ ] add some basic simplifications
- [ ] output to verilog / other languages


## Developers

Developed by [Ronak Badhe](https://github.com/r2dev2)
