import os
import openai
import sqlite3
from termcolor import colored
from tenacity import retry, wait_random_exponential, stop_after_attempt

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"
DATABASE = "countries_database.sqlite"
USER_MESSAGE = "Top 10 matches with most goals"

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, model=MODEL):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=functions,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        raise e


class Conversation:
    def __init__(self):
        self.conversation_history = []

    def add_message(self, role, content):
        message = {"role": role, "content": content}
        self.conversation_history.append(message)

    def display_conversation(self, detailed=False):
        role_to_color = {
            "system": "red",
            "user": "green",
            "assistant": "blue",
            "function": "magenta",
        }
        for message in self.conversation_history:
            print(
                colored(
                    f"{message['role']}: {message['content']}\n\n",
                    role_to_color[message["role"]],
                )
            )


database_schema_string = """
Table: countries
Columns: Country, Region, Population, Area (sq. mi.), Pop. Density (per sq. mi.), Coastline (coast/area ratio), Net migration, Infant mortality (per 1000 births), GDP ($ per capita), ,Literacy (%), Phones (per 1000),  Arable (%), Crops (%), Other (%), Climate, Birthrate, Deathrate, Agriculture, Industry, Service

"""

functions = [
    {
        "name": "ask_database",
        "description": "Generate a SQL query to fetch data from the soccer database.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": f"""
                        SQL query extracting info to answer the user's question.
                        Use the following database schema:
                        {database_schema_string}
                        Return the SQL query as plain text.
                    """,
                }
            },
            "required": ["query"],
        },
    }
]


def ask_database(conn, query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"SQL Error: {e}")
        raise


def chat_completion_with_function_execution(messages, functions=None):

    try:
        response = chat_completion_request(messages, functions)
        full_message = response["choices"][0]
        if full_message.get("finish_reason") == "function_call":
            return call_function(messages, full_message)
        else:
            return response
    except Exception as e:
        print("Chat completion failed:", e)
        return {"error": str(e)}

def call_function(messages, full_message):

    if "function_call" in full_message["message"]:
        function_call = full_message["message"]["function_call"]
        if function_call["name"] == "ask_database":
            query = eval(function_call["arguments"])
            print(f"Generated query: {query['query']}")

            try:
                results = ask_database(conn, query["query"])
            except Exception as e:
                print("Error in query execution:", e)
                messages.append(
                    {
                        "role": "system",
                        "content": f"""
                            Query: {query['query']}
                            Error: {e}
                            Please provide a corrected SQL query in plain text.
                        """,
                    }
                )
                response = chat_completion_request(messages, model=MODEL)
                fixed_query = response["choices"][0]["message"]["content"]
                print(f"Fixed query: {fixed_query}")
                results = ask_database(conn, fixed_query)

            messages.append(
                {"role": "function", "name": "ask_database", "content": str(results)}
            )
            return chat_completion_request(messages)
    raise Exception("Function not found!")

if __name__ == "__main__":

    conn = sqlite3.connect(DATABASE)


    while True:
        conversation = Conversation()
        agent_system_message = f"""
        You are DatabaseGPT, a helpful assistant that answers questions using the soccer database.
        Use the following schema for SQL queries:
        {database_schema_string}
        """
        conversation.add_message("system", agent_system_message)

        # Prompt the user for input
        USER_MESSAGE = input(colored("Enter your task (e.g., 'Top 10 countries by population ') or type 'exit' to quit: ", "yellow")).strip()

        if USER_MESSAGE.lower() == "exit":
            print(colored("Goodbye!", "blue"))
            break

        conversation.add_message("user", USER_MESSAGE)

        response = chat_completion_with_function_execution(
            conversation.conversation_history, functions=functions
        )

        try:
            assistant_message = response["choices"][0]["message"]["content"]
            conversation.add_message("assistant", assistant_message)
            print(colored(assistant_message, "green"))  # Display assistant's valid response in green
        except Exception as e:
            error_message = f"Error in response parsing: {e}"
            print(colored(error_message, "red"))  # Display error messages in red

        conversation.display_conversation(detailed=True)

