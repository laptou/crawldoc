# `crawldoc`

This is a simple Python script that I wrote that crawls the Rust documentation
for a given crate and converts it into Markdown files. These Markdown files are
useful to provide as context to an AI so that it can try to write more valid
Rust code.

# Setup

`uv install`

# Usage

`python crawldoc.py <crate_name>`

The Markdown files will be placed into `./output/crate_name`.
