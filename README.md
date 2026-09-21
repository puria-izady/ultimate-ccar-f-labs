# Labs: Ultimate Claude Certified Architect, Foundations (CCAR-F)

These are the hands-on labs for our CCAR-F preparation course. We are Frank Kane and Puria
Izady, and this repository holds everything you run alongside the videos: six labs, nine
notebooks, and the project fixtures they work on.

Each lab builds one of the architectures from the course, a cell at a time. They are guided
demonstrations rather than exercises, so there is nothing to fill in and no solution file to
peek at. We walk through the cells in the video and explain what each block does; you run the
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

| Folder | Lab | Run it after | What it needs |
|---|---|---|---|
| `lab_01/` | Developer productivity toolset, part A | Chapter 5 | nothing |
| `lab_01/` | Developer productivity toolset, part B | Chapter 7 | subscription or key |
| `lab_02/` | Multi-agent research system | Chapter 10 | subscription or key |
| `lab_03/` | Customer support resolution agent, part A | Chapter 10 | nothing |
| `lab_03/` | Customer support resolution agent, part B | Chapter 10 | subscription or key |
| `lab_04/` | Claude Code for continuous integration | Chapter 14 | a GitHub account |
| `lab_05/` | Structured extraction pipeline | Chapter 16 | a key, and only a key |
| `lab_06/` | Code generation in a real project, parts A and B | Chapter 19 | Claude Code signed in |

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

**Lab 6** is two notebooks, and not one cell of either calls a model. The project it works on,
`lab_06/mycorp/`, is checked in beside the notebooks so you can read it first. The first cell
copies it into a working directory and gives that copy a git history. Everything the model
does happens in a terminal, in `claude`, using the prompts the notebooks hold. So this is the
lab that wants Claude Code signed in rather than a key in `.env`.

## What it costs

About **$1.25 across all six labs**, and every run is capped so it cannot surprise you. Each
Agent SDK run sets `max_turns` and `max_budget_usd`; each Claude API call sets `model` and
`max_tokens`. Lab 6 is the largest at roughly $0.30, because interactive sessions accumulate
context in a way that single calls do not.

On a Claude subscription, five of the six labs cost you nothing beyond what you already pay.
Only Lab 5 needs API billing, and it is the cheapest of the set.

## Where the code lives

A notebook cell should hold the thing the lab is teaching and not much else. So the
primitives are in the cells: the MCP servers, the tool and agent definitions, the hooks, the
run options, the schemas. Everything around them lives in a module you can open beside the
notebook.

| Where | What is in it |
|---|---|
| `labkit/` | Shared plumbing. Finding the workspace and the credential, running an agent and collecting what it did, printing a result, calling a hook or a tool offline. Nothing in it is a lesson. |
| `lab_0N/fixtures.py`, `corpus.py`, `documents.py` | The data a lab serves. Worth reading once; not worth a hundred lines of a notebook. |
| `lab_01/servers/` | The five MCP servers, as real Python. The notebook stages them into `workspace/` and shows you the parts that matter. |
| `lab_03/support/` | The four support tools and the four hooks. |
| `lab_02/research_tools.py`, `lab_06/mycorp_lab.py` | The same idea, for those two labs. |

You are meant to open these. `labkit.show_source(...)` in a notebook renders one definition
out of one of them, so the cell shows you the tool you are about to call rather than the
hundred lines around it. But the file is right there, and editing it and restarting the
kernel is a good way to break things on purpose.

`uv sync` installs this repository into its own environment, which is what lets every
notebook write `import labkit` from its own folder with no path juggling in a cell. If you
pull a change to `labkit/` it takes effect on the next kernel restart; there is nothing to
reinstall.

## Working directories, and rerunning a lab

Labs 1, 3, 5 and 6 write a `workspace/` directory beside their notebook, and Lab 2 writes an
`out/` directory in the same way. Those directories are created by notebook cells, never by
us, and they are deliberately left out of git. So if a lab gets into a state you do not like,
delete its `workspace/` or `out/` folder and run the notebook from the top. That is always
safe, and it is the fastest way to get back to a clean start.

Two things follow from this. Part B of a two-part lab expects part A to have run, because it
uses the workspace part A wrote. And nothing you find inside a `workspace/` is the original:
the labs copy their servers and their data in from the checked-in files beside the notebook,
so an edit you make in there is replaced the next time the first cell runs. Edit the
checked-in file if you want the change to stick. `lab_06/mycorp/` works the same way.

The notebooks are committed unexecuted, with no saved outputs. If you want to reset one after
running it, `git checkout` the notebook.

## The diagrams

`diagrams/` holds the architecture diagram for each lab, the same ones we put on screen in the
course. Open the diagram for a lab before you start it. The notebooks build exactly what the
diagram shows, in the order it shows, and having it beside you makes the cells much easier to
follow.

## If something goes wrong

The first cell of every lab checks your setup and tells you what it found, so start by reading
its output. Most problems we see are one of three things: `uv sync` not run yet, a `.env` that
was never copied from `.env.example`, or a notebook started from the wrong directory. Each lab
expects to run from its own folder, which is what Jupyter does by default when you open the
notebook from this repository.

If a lab still will not run, tell us in the course Q&A with the output of that first cell, and
we will pick it up there.

Frank and Puria
