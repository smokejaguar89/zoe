from pydantic import BaseModel, ConfigDict


class GetSensorDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    light: float
    temperature: float
    humidity: float
    moisture: float
    pressure: float
