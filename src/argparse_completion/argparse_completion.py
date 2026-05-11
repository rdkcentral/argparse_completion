#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import re
from typing import Dict, List, Mapping, MutableMapping, Optional, Sequence


def get_completion(parser: argparse.ArgumentParser) -> List[str]:
    """
    Return shell-completion candidates based on the environment.

    Currently supports:
      - _ARGPARSE_COMPLETE=complete_bash  -> bash-style completion list
    """
    mode = os.getenv("_ARGPARSE_COMPLETE")
    dispatch = {
        "complete_bash": _bash_completion,
    }
    handler = dispatch.get(mode)
    return handler(parser) if handler else []


# ---------------------------- completion (bash) ---------------------------- #

def _bash_completion(parser: argparse.ArgumentParser) -> List[str]:
    """
    Produce a flat list of completion candidates for bash.
    Looks at COMP_WORDS to infer the current token path.
    """
    args_dict = _introspect_parser(parser)
    comp_words = os.getenv("COMP_WORDS", "")
    # Remove the program name if present and split into tokens
    words: List[str] = re.sub(r'^.*{}\s'.format(parser.prog),"", comp_words).split()
    choice_tree = _choices_for_words(args_dict, words)
    return _flatten_choices(choice_tree)


def _flatten_choices(choice_tree: Mapping[str, dict]) -> List[str]:
    """
    Flatten the visible choices from the current node of the argument tree
    into a simple list suitable for shell completion.
    """
    out: List[str] = []
    # optionals: keys are the flags themselves
    optionals = choice_tree.get("optionals", {})
    if optionals:
        out.extend(optionals.keys())

    # positionals: each positional may have 'choices' (list-like)
    for positional in (choice_tree.get("positionals") or {}).values():
        out.extend(positional.get("choices", []) or [])

    # subcommands: each subparser choice is a key in 'choices'
    for sub in (choice_tree.get("subcommands") or {}).values():
        out.extend((sub.get("choices") or {}).keys())
    return out


# --------------------------- argument tree logic --------------------------- #

def _choices_for_words(args_dict: Dict, remaining: Sequence[str]) -> Dict:
    """
    Descend the argument tree based on the user-provided tokens (remaining),
    returning the node dict that should be used to suggest completions.

    The structure produced by _introspect_parser() is:
      {
        "optionals": { "--flag": {...}, "-f": {...}, ... },
        "positionals": { "NAME": {"choices": [...]}, ... },
        "subcommands": {
            "cmd": {
               "choices": { "sub": <sub-tree>, ... },
               ... (action metadata)
            }
        }
      }
    """
    if not remaining:
        args_dict.pop('optionals')
        return args_dict

    # If there are multiple tokens, try to walk down subcommands.
    if len(remaining) > 1 and "subcommands" in args_dict:
        subcmd_block = args_dict["subcommands"] or {}
        for idx, token in enumerate(remaining):
            for sub_name, subdef in subcmd_block.items():
                # token should match one of the available subparser keys
                sub_choices = (subdef.get("choices") or {})
                if token in sub_choices:
                    # Recurse into the matching sub-tree with remaining tail
                    return _choices_for_words(sub_choices[token], remaining[idx+1:])
        # No subcommand matched; fall back to evaluating last token only
        return _choices_for_words(args_dict, remaining[-1])

    # Single token: filter visible choices by prefix/containment rules
    token = remaining[-1]
    if token in args_dict.get("optionals",[]):
        narrowed = _choices_for_words(args_dict, remaining=[])
    else:
        narrowed = {
            "optionals": _filter_optionals(args_dict.get("optionals") or {}, token),
            "positionals": _filter_positionals(args_dict.get("positionals") or {}, token),
            "subcommands": _filter_subcommands(args_dict.get("subcommands") or {}, token),
        }

        # If a subcommand exactly matches the token, drill into that sub-tree
        for subdef in (args_dict.get("subcommands") or {}).values():
            choices = (subdef.get("choices") or {})
            if token in choices:
                remaining.remove(token)
                return _choices_for_words(choices[token], remaining)
    # If filters produced nothing, return the current node; else the narrowed view
    return narrowed


def _filter_optionals(optionals: Mapping[str, dict], token: str) -> Dict[str, dict]:
    """
    Keep flags whose string either contains token or equals it.
    """
    if not optionals or token == '':
        return {}
    return {
        opt: meta
        for opt, meta in optionals.items()
        if opt.startswith(token) and opt != token
    }


def _filter_positionals(positionals: Mapping[str, dict], token: str) -> Dict[str, dict]:
    """
    For each positional, narrow the 'choices' list by token containment/equality.
    Drop positionals that end up with no available choices.
    """
    if not positionals:
        return {}

    narrowed: Dict[str, dict] = {}
    for name, meta in positionals.items():
        choices = list(meta.get("choices") or [])
        if not choices:
            # If no explicit choices, this positional isn't helpful for completion filtering
            continue
        kept = [c for c in choices if (str(c).startswith(token)) and (token != str(c))]
        if kept:
            narrowed[name] = {**meta, "choices": kept}
    return narrowed


def _filter_subcommands(subcommands: Mapping[str, dict], token: str) -> Dict[str, dict]:
    """
    Within subcommands, each entry has 'choices' mapping to subparsers.
    Keep only subcommands whose key contains the token (or exact match).
    """
    if not subcommands:
        return {}

    narrowed: Dict[str, dict] = {}
    for dest, meta in subcommands.items():
        choices = dict(meta.get("choices") or {})
        if token in choices:
            # exact match always retained
            narrowed[dest] = {**meta, "choices": {token: choices[token]}}
            continue
        # partial match on subcommand names
        kept = {k: v for k, v in choices.items() if str(k).startswith(token)}
        if kept:
            narrowed[dest] = {**meta, "choices": kept}
    return narrowed


# ------------------------------ introspection ------------------------------ #

def _introspect_parser(parser: argparse.ArgumentParser) -> Dict:
    """
    Convert an argparse.ArgumentParser into a lightweight, serializable dictionary
    describing optionals, positionals, and subcommands + their choices.
    """
    p_dict = parser.__dict__.copy()
    optionals = p_dict.get("_optionals")
    positionals = p_dict.get("_positionals")
    subparsers = p_dict.get("_subparsers")

    out: Dict[str, dict] = {}
    if optionals:
        out["optionals"] = _collect_optionals(optionals)
    pos = _collect_positionals(positionals) if positionals else {}
    if pos:
        out["positionals"] = pos
    if subparsers:
        out["subcommands"] = _collect_subcommands(subparsers)
    return out


def _action_to_meta(action: argparse.Action) -> Dict:
    meta = {"help": action.help}
    if action.choices:
        meta["choices"] = action.choices
    return meta


def _collect_optionals(group: argparse._ArgumentGroup) -> Dict[str, dict]:
    args: Dict[str, dict] = {}
    for action in group._group_actions:
        for opt in action.option_strings:
            args[opt] = _action_to_meta(action)
    return args


def _collect_positionals(group: argparse._ArgumentGroup) -> Dict[str, dict]:
    args: Dict[str, dict] = {}
    for action in group._group_actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        args[action.dest] = _action_to_meta(action)
    return args


def _collect_subcommands(group: argparse._ArgumentGroup) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for action in group._group_actions:
        if isinstance(action, argparse._SubParsersAction):
            choices = {name: _introspect_parser(parser) for name, parser in action.choices.items()}
            meta = _action_to_meta(action)
            meta["choices"] = choices
            out[action.dest] = meta
    return out

