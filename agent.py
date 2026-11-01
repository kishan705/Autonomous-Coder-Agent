import os
import subprocess
import json
import lancedb
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage

WORKSPACE_DIR = "./workspace"


def reset_workspace():
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)
    
    with open(os.path.join(WORKSPACE_DIR, "database.py"), "w") as f:
        f.write('''def get_user(user_id: int):
    if not isinstance(user_id, int):
        raise TypeError("Database Error: user_id must be an integer!")
    return {"id": user_id, "name": "Alice"}
''')

    with open(os.path.join(WORKSPACE_DIR, "server.py"), "w") as f:
        f.write('''from database import get_user

def fetch_route(req_id: str):
    #BUG: Passing a string directly to the database without casting to int()
    return get_user(req_id)
''')

    with open(os.path.join(WORKSPACE_DIR, "test_server.py"), "w") as f:
        f.write('''import server

def test_fetch():
    response = server.fetch_route("123")
    assert response == {"id": 123, "name": "Alice"}
''')

@tool
def read_file(filename: str) -> str:
    """Reads a file from the workspace."""
    filepath = os.path.join(WORKSPACE_DIR, filename.strip())
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File {filename} not found."

@tool
def write_file(filename: str, content: str) -> str:
    """Overwrites a file in the workspace with new code."""
    filepath = os.path.join(WORKSPACE_DIR, filename.strip())
    with open(filepath, "w") as f:
        f.write(content)
    return f"Successfully updated {filename}"

@tool
def run_tests() -> str:
    """Runs pytest on the workspace and returns the terminal output."""
    print("\n[Agent Sandbox] Running pytest...")
    result = subprocess.run(["pytest", WORKSPACE_DIR], capture_output=True, text=True)
    if result.returncode == 0:
        return "Tests PASSED!\n" + result.stdout
    return "Tests FAILED. Error log:\n" + result.stdout + "\n" + result.stderr


embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = lancedb.connect("./lancedb_data")

def index_workspace():
    print("[System] Indexing workspace files into vector database...")
    data = []
    for f in os.listdir(WORKSPACE_DIR):
        if f.endswith(".py"):
            filepath = os.path.join(WORKSPACE_DIR, f)
            with open(filepath, "r") as file:
                content = file.read()
            vector = embeddings.embed_query(content)
            data.append({"filename": f, "content": content, "vector": vector})
    
    if "codebase" in db.table_names():
        db.drop_table("codebase")
    if data:
        db.create_table("codebase", data=data)
        print("[System] Indexing complete.")

@tool
def search_codebase(query: str) -> str:
    """Searches the LanceDB vector database for relevant code files."""
    print(f"\n[Agent RAG] Searching codebase for: {query}")
    try:
        table = db.open_table("codebase")
        query_vector = embeddings.embed_query(query)
        results = table.search(query_vector).limit(2).to_list()
        context = ""
        for res in results:
            context += f"--- {res['filename']} ---\n{res['content']}\n\n"
        return context
    except Exception as e:
        return f"Error searching database: {str(e)}"

tools_map = {
    "search_codebase": search_codebase,
    "read_file": read_file,
    "write_file": write_file,
    "run_tests": run_tests
}
tools_list = list(tools_map.values())

def extract_first_json_call(text):
    brace_count = 0
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start != -1:
                json_str = text[start:i+1]
                try:
                    obj = json.loads(json_str)
                    if "name" in obj:
                        return obj
                except Exception:
                    pass
                start = -1
    return None


if __name__ == "__main__":
    reset_workspace()
    index_workspace()

    llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)
    llm_with_tools = llm.bind_tools(tools_list)

    print("\n🚀 Starting Step-by-Step Local Autonomous Coder Agent...")
    
    messages = [
        HumanMessage(content="""You are an autonomous AI Software Engineer fixing bugs in the workspace.
        You have access to tools: search_codebase, read_file, write_file, run_tests.
        
        CRITICAL RULE: Call ONLY ONE tool at a time. Wait for the result before calling the next tool.
        
        Task: The fetch_route endpoint in server.py passes a string instead of an int to database.get_user().
        Step 1: Use read_file to inspect server.py.
        Step 2: Use write_file to update server.py with this exact code:
        from database import get_user

        def fetch_route(req_id: str):
            return get_user(int(req_id))
            
        Step 3: Use run_tests to verify tests pass.""")
    ]

    for turn in range(6):
        print(f"\n--- Turn {turn + 1} ---")
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        content = response.content if response.content else ""
        print(f"[Agent Thought]: {content}")

        tool_executed = False

        if hasattr(response, 'tool_calls') and response.tool_calls:
            tc = response.tool_calls[0] 
            t_name = tc['name']
            t_args = tc['args']
            print(f"[Agent Action]: Executing '{t_name}' with {t_args}")
            if t_name in tools_map:
                res = tools_map[t_name].invoke(t_args)
                print(f"[Tool Output]:\n{res}")
                messages.append(ToolMessage(content=str(res), tool_call_id=tc.get('id', 'call_1')))
                tool_executed = True

        if not tool_executed:
            json_data = extract_first_json_call(content)
            if json_data:
                t_name = json_data.get("name")
                t_args = json_data.get("arguments", {})
                print(f"[Agent Action (Parsed)]: Executing '{t_name}' with {t_args}")
                if t_name in tools_map:
                    res = tools_map[t_name].invoke(t_args)
                    print(f"[Tool Output]:\n{res}")
                    messages.append(ToolMessage(content=f"Tool {t_name} output:\n{res}", tool_call_id="text_fallback"))
                    tool_executed = True

        if not tool_executed:
            print("[Agent]: Prompting model to proceed...")
            messages.append(HumanMessage(content="Good. Now proceed to the next step using your tools (read_file, write_file, or run_tests)."))
        else:
            # Check if tests passed
            if "Tests PASSED!" in str(locals().get('res', '')):
                print("\n🎉 SUCCESS: Agent successfully fixed the bug and tests passed!")
                break