import asyncio
from datetime import timedelta
import os
import rich

from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from rich.progress import Progress

collected_tools = []

async def main():
    server_url = "http://localhost:8000"
    print("Initializing MCP session...")

    if "ANTHROPIC_API_KEY" not in os.environ:
        raise ValueError("Please set the ANTHROPIC_API_KEY environment variable.")
    # Keep MCP session open during LLM interaction
    async with streamablehttp_client(
        url=server_url,
        timeout=timedelta(seconds=60),
    ) as (read_stream, write_stream, get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            print("⚡ Starting session initialization...")
            await session.initialize()
            print("✨ Session initialization complete!")
            session_id = get_session_id()
            print(f"\nConnected to MCP server at {server_url} {session_id}")
            tools = await load_mcp_tools(session)
            print(f"Loaded {len(tools)} tools: {[tool.name for tool in tools]}")

            agent = create_react_agent("claude-3-7-sonnet-20250219", tools)
            total_events = 0

            def update_progress_callback(completed, total):
                percent = (completed / total) * 100 if total else 0
                progress.update(task, completed=completed)
                progress.console.print(f"[blue]Progress: {percent:.2f}%")

            user_prompt = input("What do you want to do with MySQL: ")
            messages = [HumanMessage(content=user_prompt)]
            with Progress() as progress:
                task = progress.add_task("[cyan]Processing events...", total=100)
                completed_events = 0
                total_expected_events = (
                    100  # Set this to the expected number of events if known
                )

                async for event in agent.astream_events({"messages": messages}):
                    total_events += 1
                    completed_events += 1
                    output = event.get("data", None)
                    if output is not None:
                        output_data : dict = output.get('output', '')
                        if output_data:
                            for output in output_data:
                                if isinstance(output, ToolMessage):
                                    rich.print(f"[bold yellow] Mr.MySQL: {output.content}[/bold yellow]")
                                elif isinstance(output, AIMessage):
                                    content_item = output.content[0]
                                    if isinstance(content_item, dict):
                                        content_dict: dict = content_item
                                        rich.print(f"[bold blue] I am your servant: {content_dict.get('text')}[/bold blue]")
                                    elif isinstance(content_item, str):
                                        rich.print(f"[bold blue] I am your servant: {content_item}[/bold blue]")
                                

                    update_progress_callback(completed_events, total_expected_events)
            update_progress_callback(100, 100)
            print(f"\n🎉 Completed processing {total_events} events.")


asyncio.run(main())
