# argparse\_completion

`argparse_completion` is a tiny helper library for adding tab-completion to Python CLIs built with `argparse`.

> *Currently only bash tab-completion is supported.*
> *This library has only been tested with Python 3.10 and may not support newer versions*

It works by:

1.  Having your Python CLI detect when it’s being invoked for completion (via an env var).
2.  Returning a newline-delimited list of completion candidates.
3.  Letting a small Bash function feed the current shell state (`COMP_WORDS`, `COMP_CWORD`) into your program and use its output as completions.

***

## Features

*   ✅ Works with standard `argparse.ArgumentParser`.
*   ✅ Simple “completion mode” triggered via an environment variable.
*   ✅ Bash completion wrapper script included in the example.
*   ✅ Supports completing subcommands / options / choices (as your completion engine implements).

***

## Installation

```bash
pip install argparse_completion
```

***

## Usage

Below is a complete usage guide based on the attached examples.

### 1) Add completion support to your Python CLI

Your CLI should:

*   Create an `ArgumentParser` whose `prog` matches the command name you’ll complete for (the example uses `example_argparse_app.py`).
*   When the `_ARGPARSE_COMPLETE` environment variable is set, call `argparse_completion.get_completion(parser)` and print candidates one-per-line, then exit.

**[Example python app code](`examples/example_argparse_app.py`)**

Key points from the example:

*   Completion mode is triggered purely by checking `os.getenv('_ARGPARSE_COMPLETE')`.
*   The completion candidates are printed as newline-separated strings (`'\n'.join(...)`). 
*   The positional argument `message` defines explicit `choices=['hello', 'goodbye']`, which is ideal for completion.

***

### 2) Add a Bash completion function

The Bash side:

*   Captures the current completion context from Bash (`COMP_WORDS`, `COMP_CWORD`)
*   Invokes your program with `_ARGPARSE_COMPLETE=complete_bash`
*   Reads the program output into `COMPREPLY`

**[Example bash completion script](`examples/example_bash_completion.sh`)**

What matters here:
*   Bash passes **all current tokens** via `COMP_WORDS="${COMP_WORDS[*]}"` and the **cursor index** via `COMP_CWORD=$COMP_CWORD`.
*   `_ARGPARSE_COMPLETE=complete_bash` tells your Python program to run in completion mode (your Python checks `_ARGPARSE_COMPLETE` exists).
*   `complete -F _argparse_completion example_argparse_app.py` registers completion for the command.

***

### 3) Enable completion in your shell

#### Option A: Source manually (quick test)

```bash
source ./example_bash_completion.sh
```

Then try:

```bash
./example_argparse_app.py <TAB>
./example_argparse_app.py --<TAB>
./example_argparse_app.py he<TAB>
```

Given the example parser, you should see completion candidates like:

* `--upper`
* `hello`
*`goodbye`

#### Option B: Enable permanently

Add to your `~/.bashrc` or `~/.bash_profile`:

```bash
source /path/to/example_bash_completion.sh
```

Reload:

```bash
source ~/.bashrc
```

***

## Expected CLI behavior

When **not** in completion mode, your program should behave normally:

```bash
./example_argparse_app.py hello
./example_argparse_app.py goodbye --upper
```

When in **completion mode**, your program should print a list of possible completions and exit:

```bash
env COMP_WORDS="example_argparse_app.py " COMP_CWORD=1 _ARGPARSE_COMPLETE=complete_bash \
  ./example_argparse_app.py
```

***

## [License](LICENSE)

***

## [Contributing](CONTRIBUTING.md)

