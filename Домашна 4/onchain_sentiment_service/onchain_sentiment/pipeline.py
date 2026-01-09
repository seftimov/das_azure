from .utils.create_tables import main as create_tables
from .utils.onchain_metrics import main as onchain_metrics
from .utils.sentiment1 import main as sentiment1
from .utils.sentiment2 import main as sentiment2
from .utils.nlp import main as nlp_main
from .utils.onchain_merge import main as onchain_merge
from .utils.onchain_sentiment_merge import main as sentiment_merge


def run_pipeline():
    create_tables()
    onchain_metrics()
    sentiment1()
    sentiment2()
    nlp_main()
    onchain_merge()
    sentiment_merge()
    return "Pipeline complete"
