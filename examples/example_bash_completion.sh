#!/usr/bin/env bash

function _argparse_completion()
{
	local IFS='
	'
	COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
					COMP_CWORD=$COMP_CWORD \
					_ARGPARSE_COMPLETE=complete_bash $1 ) )
	return 0
}
echo "${COMP_WORDS[*]}"
complete -o default -F _argparse_completion example_argparse_app.py
