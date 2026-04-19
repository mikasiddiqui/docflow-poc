import azure.functions as func

from src.config import load_settings
from src.graph_client import GraphClient
from src.pipeline import configure_logging
from src.state_store import create_state_store
from src.trigger_service import poll_and_process_new_pdfs


app = func.FunctionApp()


@app.function_name(name="docflow_timer")
@app.timer_trigger(
    schedule="%DOCFLOW_POLL_SCHEDULE%",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def docflow_timer(timer: func.TimerRequest) -> None:
    settings = load_settings()
    logger = configure_logging(settings, logger_name="docflow.timer")
    graph_client = GraphClient(settings.graph, logger=logger)
    state_store = create_state_store(settings, logger=logger)

    if timer.past_due:
        logger.warning("Timer trigger fired after its scheduled time.")

    summary = poll_and_process_new_pdfs(
        settings=settings,
        graph_client=graph_client,
        state_store=state_store,
        logger=logger,
    )
    logger.info("Timer run summary: %s", summary)
