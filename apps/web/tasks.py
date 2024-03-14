from celery import shared_task


@shared_task
def process_court(state_code: str) -> bool:
    pass
    return True