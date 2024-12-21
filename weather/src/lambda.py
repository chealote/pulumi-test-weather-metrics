import requests
import os
import json
import boto3
import re

cw = boto3.client("cloudwatch")

def _get_metric_data(temp, unit, location):
    return [
        {
            "MetricName": "weather",
            "Value": int(temp[0]),
            "Dimensions": [{
                "Name": "unit",
                "Value": unit[0],
            }, {
                "Name": "location",
                "Value": location,
            }],
        }
    ]

def handler(event, context):
    if event is None or context is None:
        return {
            "status": 400,
            "body": "body or context are None, maybe because I'm testing this locally and forgot that these should be assigned a value, which aws does automatically when invoking the function",
        }

    print("event=", event)
    print("context=", context)

    location = None
    if "location" in event:
        location = event["location"]
    if location is None and  "LOCATION" in os.environ:
        location = os.environ["LOCATION"]
    if location is None:
        return {
            "status": 400,
            "body": "don't know the location",
        }

    base_url = f"https://wttr.in/{location}"

    try:
        response = requests.get(base_url, params={"format": "%C %t"})
        response.raise_for_status()
    except Exception as e:
        return {
            "status": 502,
            "body": "failed fetching weather data: " + str(e),
        }

    temp = re.findall("[0-9]+", response.text)
    unit = re.findall("[FC]", response.text)
    if len(temp) == 0 or len(unit) == 0:
        return {
            "status": 502,
            "body": "bad response from weather API: " + response.text
        }

    try:
        cw.put_metric_data(
            MetricData = _get_metric_data(temp[0], unit[0], location),
            Namespace = "Weather")

        return {
            "statusCode": 200,
            "body": json.dumps(response.text),
        }
    except Exception as e:
        print(f"ERROR: Unable to fetch weather data. {e}")
        return {
            "status": 500,
            "body": str(e),
        }

if __name__ == "__main__":
    weather = handler({"location": "mock+location"}, {})
    print(weather)
