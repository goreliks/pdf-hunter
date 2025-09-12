from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


# LLMs
static_analysis_triage_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)

static_analysis_investigator_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)

static_analysis_graph_merger_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)

static_analysis_reviewer_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)

static_analysis_finalizer_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)


visual_analysis_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)

link_analysis_investigator_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)
link_analysis_analyst_llm = init_chat_model("openai:gpt-4.1", temperature=0.0)
