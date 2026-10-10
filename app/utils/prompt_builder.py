from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.models.domain.weather_snapshot import WeatherSnapshot
from app.services.sensor_service import (
    LIGHT_LOW_LUX_THRESHOLD,
    LIGHT_NORMAL_LUX_UPPER_THRESHOLD,
    MOISTURE_THRESHOLD,
    TEMPERATURE_COMFORT_C_UPPER_THRESHOLD,
    TEMPERATURE_COOL_C_THRESHOLD,
)


@dataclass(frozen=True)
class PromptContext:
    snapshot: SensorSnapshot
    weather: WeatherSnapshot
    top_story: str


class DayPhase(Enum):
    SUNRISE = "sunrise"
    DAY = "day"
    SUNSET = "sunset"
    NIGHT = "night"


class ImagePromptBuilder:
    def build(
        self,
        now: datetime,
        context: PromptContext,
    ) -> str:

        # Introduction
        prompt = [
            (
                "Use the provided painting as the base image: a "
                "Van Gogh-style view across Zurich rooftops towards the "
                "Uetliberg, with a "
                "potted plant on the rooftop ledge on the right. Keep the "
                "composition, the swirling brushwork and the TV tower on the "
                "hill. Edit the scene to reflect the plant's environment."
            )
        ]

        # Image interior
        prompt.append(
            "Incorporate the following details about "
            "the plant's current state:"
        )
        prompt.append("#1: " + self.build_moisture_prompt(context.snapshot))
        prompt.append("#2: " + self.build_light_prompt(context.snapshot))
        prompt.append("#3: " + self.build_temperature_prompt(context.snapshot))
        prompt.append(
            "#4: " + self.build_time_of_day_prompt(now, context.weather)
        )

        # Image exterior
        prompt.append(
            "Incorporate the following information to update "
            "the sky and the hillside:"
        )

        prompt.append("#1: " + self.build_weather_overview(context.weather))
        prompt.append(
            "#2: Update the sky and the hillside "
            f"to incorporate this story: {context.top_story}. "
            "Do not use words. Be creative."
        )

        # Conclusion
        prompt.append(
            "Finally: Keep the man on the rooftop as he is "
            "and don't add any other people."
        )

        return " ".join(prompt)

    def build_moisture_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.moisture < MOISTURE_THRESHOLD:
            return "Make the potted plant wilt and its soil appear dry."

        return "Keep the potted plant healthy and its soil well hydrated."

    def build_light_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.light < LIGHT_LOW_LUX_THRESHOLD:
            return "Leave the potted plant in deep shadow."

        if snapshot.light < LIGHT_NORMAL_LUX_UPPER_THRESHOLD:
            return "Light the potted plant with soft, gentle light."

        return "Bathe the potted plant in strong, bright light."

    def build_temperature_prompt(self, snapshot: SensorSnapshot) -> str:
        if snapshot.temperature < TEMPERATURE_COOL_C_THRESHOLD:
            return "Add a cool, chilly atmosphere to the image."

        if snapshot.temperature <= TEMPERATURE_COMFORT_C_UPPER_THRESHOLD:
            return "Keep a neutral, comfortable atmosphere in the image."

        return "Add a warm, slightly hot atmosphere to the image."

    def build_weather_overview(self, weather: WeatherSnapshot) -> str:
        prompt = []
        prompt.append(
            f"The current weather: "
            f"{weather.weather_code.name.replace('_', ' ').lower()}."
        )
        prompt.append(f"The temperature outside is {weather.temperature}°C.")

        return " ".join(prompt)

    def build_time_of_day_prompt(
        self, now: datetime, weather_snapshot: WeatherSnapshot
    ) -> str:
        time_of_day = self._get_time_of_day(
            now, weather_snapshot.sunrise, weather_snapshot.sunset
        )
        return f"Make the scene look like it's {time_of_day.value}."

    def _get_time_of_day(
        self, now: datetime, sunrise: datetime, sunset: datetime
    ) -> DayPhase:
        hour = now.hour
        sunrise_hour = sunrise.hour
        sunset_hour = sunset.hour

        if sunrise_hour <= hour < sunrise_hour + 2:
            return DayPhase.SUNRISE
        elif sunrise_hour + 2 <= hour < sunset_hour:
            return DayPhase.DAY
        elif sunset_hour <= hour < sunset_hour + 2:
            return DayPhase.SUNSET
        else:
            return DayPhase.NIGHT
