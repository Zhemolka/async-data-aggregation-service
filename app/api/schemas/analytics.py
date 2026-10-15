from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    total_successful_tasks: int
    total_urls_processed: int
    total_metrics_generated: int
