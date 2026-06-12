import sys
sys.path.insert(0, 'codebase')

from src.tools.finance_tools import FINANCE_TOOLS
from src.agent.agent import ReActAgent
from src.api.main import get_llm_provider

llm_provider = get_llm_provider()

agent = ReActAgent(
    llm=llm_provider,
    tools=FINANCE_TOOLS,
    max_steps=6,
)

question = """
 Số dư hiện tại của tôi là bao nhiêu?
"""

result = agent.run(question)
# print(result["answer"])