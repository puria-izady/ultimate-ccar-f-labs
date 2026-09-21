"""labkit.source, the slicer the hybrid split rests on.

If a decorated tool cannot be lifted out of a file *with its description*, the
notebooks cannot show their primitives, so this is checked against both decorator
forms the labs use.
"""

import textwrap

import pytest

from labkit.source import source, tool_specs

SDK_STYLE = '''
"""A module in the shape lab 2 and lab 3 use."""
from claude_agent_sdk import create_sdk_mcp_server, tool

LIMIT = 500.0

# Why this looks the way it does.
FLAKY = {"ORD-0009"}


def helper(value):
    return value


@tool(
    "get_customer",
    "Verify who you are talking to. Do not use it to search for an order.",
    {"identifier": str},
)
async def get_customer(args):
    return args


server = create_sdk_mcp_server(name="support", version="1.0.0", tools=[get_customer])
'''

FASTMCP_STYLE = '''
"""A module in the shape lab 1 uses."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("devtools")


@mcp.tool(description="Look things up.")
def lookup(query: str) -> dict:
    return {"query": query}


@mcp.tool(description=(
    "Search the ticket queue by free text. "
    "Do not use it for documentation or source code."
))
def search_tickets(query: str) -> dict:
    return {"query": query}
'''


@pytest.fixture
def sdk_module(tmp_path):
    path = tmp_path / "tools.py"
    path.write_text(textwrap.dedent(SDK_STYLE).lstrip())
    return path


@pytest.fixture
def fastmcp_module(tmp_path):
    path = tmp_path / "devtools_server.py"
    path.write_text(textwrap.dedent(FASTMCP_STYLE).lstrip())
    return path


def test_slicing_a_tool_keeps_its_decorator_and_description(sdk_module):
    sliced = source(sdk_module, "get_customer")
    assert sliced.startswith('@tool(')
    assert "Verify who you are talking to" in sliced, "the description is half the lesson"
    assert "async def get_customer" in sliced
    assert "def helper" not in sliced


def test_names_come_back_in_file_order_not_argument_order(sdk_module):
    sliced = source(sdk_module, "get_customer", "LIMIT")
    assert sliced.splitlines()[0] == "LIMIT = 500.0"


def test_a_comment_sitting_on_a_definition_comes_with_it(sdk_module):
    assert source(sdk_module, "FLAKY").startswith("# Why this looks the way it does.")
    assert "#" not in source(sdk_module, "FLAKY", comments=False)


def test_a_missing_name_says_so(sdk_module):
    with pytest.raises(KeyError, match="nonexistent"):
        source(sdk_module, "nonexistent")


def test_no_names_returns_the_whole_file(sdk_module):
    assert source(sdk_module).splitlines()[0].startswith('"""')


def test_tool_specs_reads_both_decorator_forms_without_importing(sdk_module, fastmcp_module):
    sdk = tool_specs(sdk_module)
    assert [(spec.server, spec.name) for spec in sdk] == [("support", "get_customer")]

    fast = tool_specs(fastmcp_module)
    assert [spec.name for spec in fast] == ["lookup", "search_tickets"]
    assert fast[0].server == "devtools"
    assert fast[0].description == "Look things up."
    # Implicitly concatenated literals arrive as one string, which is what makes the
    # long rewritten descriptions in lab 1 readable in a table.
    assert fast[1].description.startswith("Search the ticket queue")
    assert fast[1].description.endswith("source code.")


def test_a_function_slices_itself_but_a_module_gives_the_whole_file():
    """show_source(some_function) should show that function, not its module."""
    from labkit import extract
    from labkit.extract import forced_call

    assert source(forced_call).startswith("def forced_call(")
    assert "def show_record" not in source(forced_call)
    assert source(extract).startswith('"""The Claude API')
