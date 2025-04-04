from openai import OpenAI, AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import re, os, httpx, urllib3
from neo4j import GraphDatabase
from dotenv import load_dotenv

env_path = 'knowledgegraph/neo4j_creds.env'
load_dotenv(dotenv_path=env_path)

neo4j_config = {
    "NEO4J_URI":os.getenv("NEO4J_URI"),
    "NEO4J_USERNAME":os.getenv("NEO4J_USERNAME"),
    "NEO4J_PASSWORD":os.getenv("NEO4J_PASSWORD")
}

# First function in main: main -> process_prompt
def process_prompt(driver, user_prompt, max_tries,model_name):
    schema = fetch_entity_and_relationships(driver)  # written
    if(query_sanity_check(schema, user_prompt,model_name).lower() == "no"):
        print("Query not suitable. Please try again with a different query.")
        return None
    run_number = 1
    results = None
    invalid_query = ""
    while run_number <= max_tries:
        raw_query = generate_cypher_query_from_prompt(user_prompt, schema, run_number, invalid_query, model_name)
        candidate_query = extract_cypher_code(raw_query)
        print("\nGenerated Cypher Query:\n", candidate_query)
        if "error" in candidate_query.lower():
            invalid_query = invalid_query + "\n\n"
            run_number += 1
        else:
            results = run_query(candidate_query, driver)
        
        if results:
            break  # Exit the loop if results are found
        else:
            run_number += 1
            print(f"No results found. Attempting again... (Attempt {run_number})")
            invalid_query = invalid_query + "\n\n" + candidate_query
    
    print(generate_response_from_kg_results(user_prompt, candidate_query, results, schema,model_name))

# Nested call: main -> process prompt -> 1. fetch_entity_and_relationships
def fetch_entity_and_relationships(driver):
    query = '''
    MATCH (n)
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN DISTINCT labels(n) AS entityTypes,
                    keys(n) AS propertyKeys,
                    type(r) AS relationshipType,
                    labels(m) AS relatedEntityTypes
    '''
    schema = run_query(query,driver)
    return schema

# 1. Nested call: main -> process prompt -> 1. fetch_entity_and_relationships -> run query
# 2. Nested call: main -> process prompt -> run_query (to execute output query)
def run_query(query, driver):
    with driver.session() as session:
        result = session.run(query)
        rows = []
        for record in result:
            record_dict = dict(record)
            rows.append(record_dict)
    # print(rows)  # Print a new line
    print(f"Number of records returned: {len(rows)}")  # Print the number of records
    return rows

# 1. Nested call: main -> process prompt -> 2. query_sanity_check
def query_sanity_check(schema,user_prompt,model_name):
    messages =[
        {"role":"system","content":"You are a helpful, advanced language model that is well-versed with graph databases. Your primary goal is to help a user identify whether or not the query they are asking is feasible to answer or not."},
        {"role":"system","content":f"Refer: \n{schema}.\nTry your best to do a preliminary analysis of the request and determine based on the schema if this is a feasible question to try and answer using our graph database and querying. If any entities, properties or relationships appear, or seem to appear in the prompt, or any of the words closely associated with them appear, always permit the query to proceed. Be lenient with allowing queries to proceed."},
        {"role":"system","content":"Output: If you determine it is feasible to answer, then just return one word 'Yes' as a string. If you determine the answer is no, then just return the one word 'No' as a string "}
    ]
    messages.append(
        {"role":"system","content":f"Here is the user prompt: {user_prompt}."}
    )
    output = query_llm(model_name,messages)

    return output

# Nested call: main ->process prompt -> 2. generate_cypher_query_from_prompt
def generate_cypher_query_from_prompt(prompt, schema, run_number, invalid_query, model_name):
    
    messages = [
        {"role": "system", "content": "You are an advanced language model, expert at generating Cypher queries for a knowledge graph that encompasses various sectors, companies, raw materials, policies, regulations, and their interrelationships."},
        
        {"role": "system", "content": "Your primary function is to interpret user prompts and convert them into precise Cypher queries that accurately reflect the knowledge graph's structure."},
        
        {"role": "system", "content": "DO NOT create any new nodes, entities, relationships apart from the ones provided."},

        {"role": "system", "content": f"ONLY utilize the following node labels ('entityTypes'), their properties ('propertyKeys') and relationships ('relationshipType') which relate the entities to other entities ('relatedEntityTypes'): \n{schema}."},

        {"role": "system", "content": "Ideation and Exploration: 1. Decompose the user prompt into manageable steps. Identify words in the prompt that correspond to specific entities. Recognize variations in user language; map synonyms and related terms for clarity. Analyze each segment based on node labels, properties, and relationships. Investigate potential multi-hop chains formed by relationships and entities, decomposing the input as needed. Utilize both directed and undirected relationships for exploration, including undirected ones that may yield valuable insights. Reassemble the chunks to grasp the complete context as previously analyzed. 2. Understanding Relationships: Acknowledge the interconnected nature of entities within the knowledge graph. For instance, companies may be influenced by factors such as sourcing from countries and utilizing local raw materials. Consider all relevant relationships when formulating queries. 3. Multi-Hop Relationships: Recognize multi-hop relationships by tracing impacts through interconnected entities (e.g., from Mine to Country to Company to Raw Materials). If entities are identified in the prompt, explore their connections through the provided relationships. 4. General Context: Ensure that the system remains adaptable to various user inputs, maintaining clarity and coherence throughout the analysis process."},

        # {"role": "system","content": f"If you feel that after the previous step, there were no significant mappings, refer to {run_query(query,driver)}, and check for any matches in the information, if there is still nothing, end here. If there is something which you can use, proceed to query generation.  7. Termination: Ensure to the best of your ability that none of the queries end up being infinite queries. If you suspect that it may become infinite, cap it at 200 hops."},

        {"role": "system","content": "Query Generation: 1. Construct a Cypher query that encompasses all relevant entities and relationships derived from the user's prompt. Ensure correct case sensitivity for entity names and relationship types, and utilize distinct variable names to prevent conflicts. 2. Naming Conventions: Apply PascalCase for entity labels (e.g., `Company`, `Country`, `Mine`) and uppercase for relationship types (e.g., `HAS_COMPANY`, `IMPACTED_BY`). 3. Case Sensitivity: Ensure that case variations (e.g., 'microsoft' vs. 'Microsoft') do not result in blank queries if the entity exists. 4. Handling Missing Data: If no relevant entities or relationships are identified, return 'No entries to display.' For errors, return 'Error.' 5. Complex Queries: For prompts involving multiple conditions or attributes, ensure the generated query accurately reflects all specified criteria. 6. Duplicate Handling: Ensure that returned results are free of duplicates, especially when multiple companies are affected by the same factors."},

        {"role": "system", "content": "5. Output Format: Provide the response as a directly executable Cypher query string. Do not return anything which is not part of the cypher query. For errors or no entries returned, return the response in the previously mentioned standardized format."},
    ]
    messages.append(
        {"role": "user", "content": f"Generate a Cypher query for this user prompt: {prompt}. If run number =1, ignore the rest of this prompt. If {run_number} > 1, there was an error when I provided you with user prompt to generate a Cypher query in the the previous attempt. Since these did not achieve the goal, take them into consideration and avoid making the same mistakes, and modify your approach appropriately. Here is everything you have already tried so far in your previous attempts:{invalid_query}"}
    )

    output = query_llm(model_name,messages)

    return output
        
# Nested call: main -> process_prompt -> generate_response_from_kg_results
def generate_response_from_kg_results(user_prompt, candidate_query, results, schema,model_name):
    messages = [
        {"role": "system", "content": "You are an advanced language model which is an expert at generating insights from various sectors, companies, raw materials, policies, regulations, and their interrelationships."},
        
        {"role": "system", "content": "Your primary function is to read the user's prompt, understand the cypher query generated, reference it to the schema to answer the user's question as best as you can, and try to capture the business understanding for why a particular question was asked. The answer should be clear, concise and to the point. It should also explain the output of the cypher query to the user. All this should be in no more than 60 words."},
    ]
    messages.append(
        {"role": "user", "content": f"My prompt was: {user_prompt}. \n The generated query was: {candidate_query}.\n The results of executing the query were: {results}.\n The schema of the knowledge graph was as follows:\n {schema}. Now explain to me what this means and."},
    )

    output = query_llm(model_name,messages)

    return output

# Nested call: main ->process prompt -> 2. generate_cypher_query_from_prompt -> query_llm ->  query_gpt_35
def query_gpt_35(messages):
    azure_35_config = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"), 
        "AZURE_OPENAI_MODEL_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"),
        "AZURE_OPENAI_MODEL_NAME": os.getenv("AZURE_OPENAI_MODEL_NAME"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"), 
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION")
    }
    # Initialize Azure OpenAI client
    client_remote_35 = AzureOpenAI(
        azure_endpoint=azure_35_config["AZURE_OPENAI_ENDPOINT"],
        api_key=azure_35_config["AZURE_OPENAI_API_KEY"],
        api_version=azure_35_config["AZURE_OPENAI_API_VERSION"]
    )
    response = client_remote_35.chat.completions.create(
        model=azure_35_config["AZURE_OPENAI_MODEL_NAME"],
        messages=messages
    )
    return response.choices[0].message.content.strip()

# Nested call: main ->process prompt -> 2. generate_cypher_query_from_prompt -> query_llm ->  query_gpt_4o
def query_gpt_4o(messages):
    azure_4o_config = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT_4o"), 
        "AZURE_OPENAI_MODEL_NAME": os.getenv("AZURE_OPENAI_MODEL_NAME_4o"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY_4o")
    }
    client = ChatCompletionsClient(
        endpoint=azure_4o_config["AZURE_OPENAI_ENDPOINT"],
        credential=AzureKeyCredential(azure_4o_config["AZURE_OPENAI_API_KEY"]),
    )
    # Create a list to hold the message instances
    all_messages = []

    # Loop through the input messages and create the appropriate instances
    for message in messages:
        if message["role"] == "system":
            all_messages.append(SystemMessage(content=message["content"]))
        elif message["role"] == "user":
            all_messages.append(UserMessage(content=message["content"]))

    response = client.complete(
        messages=all_messages,
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=azure_4o_config["AZURE_OPENAI_MODEL_NAME"]
    )
    return response.choices[0].message.content.strip()

# Nested call: main ->process prompt -> 2. generate_cypher_query_from_prompt -> query_llm -> query_openai_model
def query_openai_model(messages):
    openai_config = {
        "OPENAI_API_KEY":os.getenv("OPENAI_API_KEY")
    }
    # Configure OpenAI client with SSL verification disabled
    client = OpenAI(
        api_key=openai_config["OPENAI_API_KEY"],
        http_client = httpx.Client(verify=False)
    )
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Make your API call
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )
    
    return completion.choices[0].message.content

def query_llm(model_name,messages):
    if model_name.lower() == 'gpt-35-turbo':
        return query_gpt_35(messages)
    elif model_name.lower() == 'gpt-4o':
        return query_gpt_4o(messages)
    elif model_name.lower() == 'openai':
        return query_gpt_4o(messages)
    else:
        return query_gpt_35(messages)

# Nested call: main ->process prompt -> 3. extract_cypher_code
def extract_cypher_code(text):
    # Match code blocks starting with ``` or ```cypher and extract the inner text
    match = re.search(r"```(?:cypher)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()  # Return the inner text without backticks
    elif (text == "No entries to display."):
        return "error"
    return text.strip()  # Return None if no match is found

# Runs first
def main():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(neo4j_config["NEO4J_URI"], auth=(neo4j_config["NEO4J_USERNAME"], neo4j_config["NEO4J_PASSWORD"]))
    print("Connected to instance!")
    max_tries = 10
    model_name = 'gpt-35'
    try:
        user_prompt = input("\nPlease enter your question: ").strip()
        process_prompt(driver, user_prompt, max_tries,model_name)
    finally:
        driver.close()
        print("\nClosed Neo4j connection.")

if __name__ == '__main__':
    main()