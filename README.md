# Labs: Ultimate Claude Certified Architect, Foundations (CCAR-F)

These are the hands-on labs for our CCAR-F preparation course by Frank Kane and Puria
Izady. 

Each lab builds one of the architectures from the course with guided Jupyter Notebooks. We walk through the cells in the video and explain what each block does; you run the
same cells yourself afterwards, change them, and break them on purpose. That last part is
where most of the learning happens, and it is why we hand you the whole environment rather
than a transcript.

## Setup, once

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.10 or
newer. From the root of this repository:

```bash
uv sync
```

```bash
cp .env.example .env
```

Open `.env` and read the notes at the top of it before you fill anything in, because you have
a choice to make there. Then start Jupyter:

```bash
uv run jupyter lab
```

One environment serves every lab, and one `.env` at the root of this repository serves every
notebook. You set your credential once.

## Which credential you need

The Agent SDK runs the `claude` binary rather than calling the API itself, so it takes
whichever credential that binary takes. That gives you two ways in, and we have deliberately
kept both open.

On a **Claude Pro, Max, Team or Enterprise subscription**, leave both credential lines in
`.env` blank and run `claude` once to sign in. The Agent SDK labs then run on your
subscription and cost you nothing beyond it.

On **API billing**, put a key from the Claude Console in `ANTHROPIC_API_KEY`. A key outranks a
subscription login, so blank that line out again if you want to switch back. Either way, the
first cell of every lab prints which credential it found, so you are never guessing.

Lab 5 is the one exception, and it needs a key whichever route you take. It calls the Claude
API directly, and a subscription authenticates the `claude` binary rather than the API.

## The labs

| Folder | Lab | What it needs |
|---|---|---|
| `lab_01/` | Developer productivity toolset, part A | nothing |
| `lab_01/` | Developer productivity toolset, part B | subscription or key |
| `lab_02/` | Multi-agent research system | subscription or key |
| `lab_03/` | Customer support resolution agent, part A | nothing |
| `lab_03/` | Customer support resolution agent, part B | subscription or key |
| `lab_04/` | Claude Code for continuous integration | a GitHub account |
| `lab_05/` | Structured extraction pipeline | a key, and only a key |
| `lab_06/` | Code generation in a real project | Claude Code signed in |

Run them in order, and run each one after the chapter in the column above. The labs assume the
ideas from that chapter, and Lab 1 in particular is split across two chapters on purpose: part
A builds an MCP server long before you have met the Agent SDK, and part B comes back to it
once you have.

**Lab 1** makes no API calls at all in part A. You build an MCP server and wire it into Claude
Code, and the proof is a terminal session rather than a Python call.

**Lab 2** is one notebook and two stages. A research agent fans out to four searchers at once,
two fields over two channels, and its findings are then chained into a formatter agent that
writes the report. Its first four sections make no API call, so the server, the tool calls and
the roster can be rerun as often as you like before you spend anything.

**Lab 4** is one notebook with no code cells in it at all. Every step is a command in a
terminal or a button on GitHub. You take your own copy of our `tictactoe` template, ask Claude
Code for a change on a branch, install the reviewing action, and open the pull request that
sets it off. The review configuration ships with the template, so there is nothing to copy
across. The spend lands in your own repository rather than in a cell.

**Lab 5** is the only lab that uses the Claude API rather than the Agent SDK, which is also
why it is the only one that insists on a key. Every section calls the API, but the calls are
single turns over documents of a dozen lines, and a full run measures under two pence.

**Lab 6** is one notebook, and not one cell of it calls a model. The project it works on,
`lab_06/mycorp/`, is checked in beside the notebook so you can read it first. The first cell
copies it into a working directory and gives that copy a git history. Everything the model
does happens in a terminal, in `claude`, using the prompts the notebook holds, in one session
that runs from section 4 to the end. So this is the lab that wants Claude Code signed in
rather than a key in `.env`. It is also the one lab whose project ships a
`.claude/settings.json`, because a demonstration that stops for a permission dialog in front
of every edit is a demonstration about permission dialogs.


## If something goes wrong

The first cell of every lab checks your setup and tells you what it found, so start by reading
its output. Most problems we see are one of three things: `uv sync` not run yet, a `.env` that
was never copied from `.env.example`, or a notebook started from the wrong directory. Each lab
expects to run from its own folder, which is what Jupyter does by default when you open the
notebook from this repository.

If a lab still will not run, tell us in the course Q&A with the output of that first cell, and we will pick it up there.
