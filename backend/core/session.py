import json
from typing import List, Dict, Optional
from core.llm import LLMClient
from core.server import Server
from vector_stores.base import VectorStore
import asyncio
import logging


class ChatSession:
    """
    Orchestrates the interaction between user, LLM, and tools.
    """

    def __init__(self, servers: List[Server], llm_client: LLMClient, vector_store: Optional[VectorStore] = None) -> None:
        self.servers = servers
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.messages: List[Dict[str, str]] = []
        self.system_message: str = ""

    async def initialize(self) -> None:
        """Initialize all servers and generate the system prompt with tools."""
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logging.error(f"Failed to initialize server: {e}")
                await self.cleanup_servers()
                return

        all_tools = []
        for server in self.servers:
            tools = await server.list_tools()
            all_tools.extend(tools)

        tools_description = "\n".join(
            [tool.format_for_llm() for tool in all_tools])

        self.system_message = f"""You are a helpful assistant with access to these tools:

{tools_description}

Choose the appropriate tool based on the user's question. If no tool is needed, reply directly.

IMPORTANT: You MUST respond with ONLY a valid JSON object when calling a tool.
Never respond in plain text if a tool can be used.
DO NOT include any explanation, comments, or natural language before or after the JSON.
Your response must begin with '{' and end with '}'. Use the format below:
{{
    "tool": "tool-name",
    "arguments": {{
        "argument-name": "value"
    }}
}}

When constructing tool arguments:
- Normalize input values when needed. For example, lowercase usernames or trim extra whitespace.
- Do not include arguments unless you are confident they are required by the tool.

After receiving a tool's result:
1. If the result contains an error message, explain to the user what went wrong and how they might fix it (e.g., correcting a username or asking a different question).
2. Transform the raw data into a natural, conversational response
3. Keep responses concise but informative
4. Focus on the most relevant information
5. Use appropriate context from the user's question
6. Avoid simply repeating the raw data

IMPORTANT: Never return tool call JSON to the user. Only use tool call JSON when explicitly prompted by the system to do so. All other responses should be natural, helpful replies to the user.

Please use only the tools that are explicitly defined above."""

        self.messages = [{"role": "system", "content": self.system_message}]

    async def chat_once(self, user_input: str):
        if self.vector_store:
            try:
                docs = self.vector_store.query(user_input)
                if docs:
                    context = "\n\n".join(doc.get("text", "") for doc in docs)
                    self.messages.append({
                        "role": "system",
                        "content": f"The following context may help you answer the user's question:\n{context}"
                    })
            except Exception as e:
                logging.warning(f"Vector store query failed: {e}")

        self.messages.append({"role": "user", "content": user_input})
        logging.info("Getting LLM response...")
        first_response = self.llm_client.get_response(self.messages)
        logging.info("Raw LLM response: %s", first_response)

        self.messages.append({"role": "assistant", "content": first_response})
        yield first_response

        while True:
            follow_up_prompt = {
                "role": "system",
                "content": (
                    "If a tool should now be called based on the previous message, "
                    "respond ONLY with a JSON object like:\n"
                    '{ "tool": "tool-name", "arguments": { "arg1": "value1" } }\n\n'
                    "Otherwise, respond with null."
                )
            }

            follow_up_messages = self.messages + [follow_up_prompt]
            tool_call_raw = self.llm_client.get_response(follow_up_messages)
            logging.info("Tool call response: %s", tool_call_raw)

            try:
                tool_call = json.loads(tool_call_raw)
                if tool_call is None or not isinstance(tool_call, dict):
                    logging.info("No more tool calls required.")
                    break

                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("arguments", {})
                logging.info(
                    f"Calling tool {tool_name} with arguments {tool_args}")

                for server in self.servers:
                    tools = await server.list_tools()
                    if any(t.name == tool_name for t in tools):
                        try:
                            result = await server.execute_tool(tool_name, tool_args)
                            self.messages.append({
                                "role": "system",
                                "content": f"Tool execution result: {result}"
                            })

                            assistant_response = self.llm_client.get_response(
                                self.messages)
                            self.messages.append({
                                "role": "assistant",
                                "content": assistant_response
                            })

                            yield assistant_response
                            break
                        except Exception as e:
                            error_message = f"Error calling tool {tool_name}: {str(e)}"
                            logging.warning(error_message)
                            self.messages.append(
                                {"role": "system", "content": error_message})
            except json.JSONDecodeError:
                logging.warning("Tool call response was not valid JSON.")
                break

    async def process_llm_response(self, llm_response: str) -> str:
        try:
            logging.info("LLM response (pre-parse): %s", llm_response)
            tool_call = json.loads(llm_response)
            logging.info("LLM parsed as JSON: %s", tool_call)

            if "tool" in tool_call and "arguments" in tool_call:
                logging.info(f"Executing tool: {tool_call['tool']}")
                logging.info(f"With arguments: {tool_call['arguments']}")

                for server in self.servers:
                    tools = await server.list_tools()
                    if any(tool.name == tool_call["tool"] for tool in tools):
                        try:
                            result = await server.execute_tool(tool_call["tool"], tool_call["arguments"])
                            if isinstance(result, dict) and 'progress' in result:
                                progress = result['progress']
                                total = result['total']
                                logging.info(
                                    f"Progress: {progress}/{total} ({(progress/total)*100:.1f}%)")
                            return f"Tool execution result: {result}"
                        except Exception as e:
                            error_msg = f"Error executing tool: {str(e)}"
                            logging.error(error_msg)
                            return error_msg

                return f"No server found with tool: {tool_call['tool']}"
            return llm_response
        except json.JSONDecodeError as e:
            logging.warning(
                "LLM response is not JSON. Returning raw text. Error: %s", e)
            return llm_response

    async def cleanup_servers(self) -> None:
        """Clean up all servers properly."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logging.warning(f"Warning during final cleanup: {e}")
