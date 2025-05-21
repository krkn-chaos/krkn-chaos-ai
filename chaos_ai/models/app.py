from pydantic import BaseModel
import datetime


class CommandRunResult(BaseModel):
    cmd: str
    log: str
    returncode: int
    start_time: datetime.datetime
    end_time: datetime.datetime
