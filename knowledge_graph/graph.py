import os
import pymupdf
from reaia.utils.neo4j_driver import get_neo4j_driver
import tempfile
import webbrowser
from pyvis.network import Network
from IPython.core.display_functions import display
from dotenv import load_dotenv, find_dotenv
from yfiles_jupyter_graphs import GraphWidget
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_community.vectorstores import Neo4jVector
from langchain_community.graphs import Neo4jGraph
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
from langchain.text_splitter import TokenTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from ipywidgets.embed import embed_minimal_html

# load the environment
load_dotenv(find_dotenv(), override=True)

# setup env:
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
os.environ["NEO4J_URI"] = os.getenv('NEO4J_URI')
os.environ["NEO4J_USERNAME"] = os.getenv('NEO4J_USERNAME')
os.environ["NEO4J_PASSWORD"] = os.getenv('NEO4J_PASSWORD')

# Initializing The Graph
graph = Neo4jGraph()
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0125")
embedding_llm = OpenAIEmbeddings()
llm_transformer = LLMGraphTransformer(llm=llm)

# Initialize the Uploads and Output directory
Uploader = 'downloads'
os.makedirs(Uploader, exist_ok=True)


# load the document and extract the content
def load_document():
    # if upload == 'yes':
    documents = []
    print('Loading the Documents!!!')
    # Load and process PDF and DOCX files
    for filename in os.listdir(Uploader):
        filepath = os.path.join(Uploader, filename)
        if filename.endswith('.pdf'):
            loader = PyMuPDFLoader(filepath)
        elif filename.endswith('.docx'):
            loader = Docx2txtLoader(filepath)
        else:
            continue  # Skip files that aren't PDF or DOCX
        documents.extend(loader.load())
    print("Documents  Loaded!!!")
    print(documents[:2])
    return documents


def chunk_documents(raw_documents):
    # Split the raw documents into chunks of 1000 words each
    text_splitter = TokenTextSplitter(chunk_size=1536, chunk_overlap=250)
    documents = text_splitter.split_documents(raw_documents)
    return documents


def graphstore(documents):
    # Convert the documents into graphs using the Graph2Vec model
    print("Converting to graph from document:")
    graph_documents = llm_transformer.convert_to_graph_documents(documents)
    print(f"Converted to graph document: {graph_documents}")
    # graph_documents = llm_transformer.convert_to_graph_documents(documents)
    print("loading the graphs into the graph database...!!")
    graph.add_graph_documents(
        graph_documents,
        baseEntityLabel=True,
        include_source=True
    )
    print("Graphs are Stored:", graph_documents)
    return graph_documents


def showGraph(cypher: str):
    # Create a Neo4j session to run the Cypher query
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Execute the Cypher query to retrieve nodes and relationships
        result = session.run(cypher)

        # Initialize a Network graph object from pyvis
        net = Network(notebook=True, height="800px", width="100%", directed=True)

        # Process nodes and relationships
        for record in result:
            # Extract node and relationship details
            source = record["s"]
            target = record["t"]
            relation = record["r"]

            # Extract 'id' property for meaningful labels
            source_label = source.get("name") or source.get("title") or source["id"]
            target_label = target.get("name") or target.get("title") or target["id"]
            relation_label = relation.type

            # Only show 'id' in the hover title
            source_id = source["id"]
            target_id = target["id"]

            # Add nodes with the 'id' property as the hover title
            net.add_node(source.id, label=source_label, title=source_id)
            net.add_node(target.id, label=target_label, title=target_id)

            # Add edges with relationship type as the title
            net.add_edge(source.id, target.id, title=relation_label, label=relation_label)

    # Save and open the graph in a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.show(tmpfile.name)
        webbrowser.open("file://" + tmpfile.name)


def create_graph():
    try:
        raw_document = load_document()
        print("document loaded")
        chunks = chunk_documents(raw_document)
        print("document chunked")
        graphs = graphstore(chunks)
        print("graphs loaded")
        # default_cypher = "MATCH (s)-[r:MENTIONS]->(t) RETURN s, r, t LIMIT 50"
        # print("Displaying graph...")
        # showGraph(default_cypher)
        return "graph is loaded"
    except ValueError as e:
        raise ValueError(f"graph is not loaded: {e}")


# def getGraph():
#     cypher = "MATCH (s)-[r:!MENTIONS]->(t) RETURN s,r,t LIMIT 200"
#     driver = get_neo4j_driver()
#     output_html_file = "client\public\knowledge_graph.html"
    
#     with driver.session() as session:
#         # Generate the GraphWidget from the Cypher query result
#         widget = GraphWidget(graph=session.run(cypher).graph())
#         widget.node_label_mapping = 'id'
        
#         # Export widget to HTML file
#         embed_minimal_html(output_html_file, views=[widget], title="Graph Widget")
#         print(f"Graph widget saved as HTML at {output_html_file}")
#         return f"Graph widget saved as HTML at {output_html_file}"
