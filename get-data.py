# 5bread = 5B Rewind's Easy API Decoder

# Fun Fact 2026/11/03: Half of all fullgame runs
# were performed before 2026/02/17,
# The other half after. That's very very recent!

import json
from urllib.request import Request, urlopen

# RUN API: https://www.speedrun.com/api/v1/runs?game=v1p527d8&max=200
# USER API: https://www.speedrun.com/api/v1/users/{id}

API_URL = "https://www.speedrun.com/api/v1"
GAME_ID = "v1p527d8"
PAGE_SIZE = 200 # the maximum (speedrun.com's limit)


def get_json(url):
    request = Request(url, headers={"User-Agent": "5b-level-runs-downloader"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)

def decode_categories(values, category):
  # Assumes that the run is RTA
  if category == "rklegln2":
    return "Any%"
  elif category == "7kjzvy3d":
    return "100%"
  elif category == "5dwwmnld":
    return "Any%-Skipless"
  elif category == "7kjm5onk":
    # Large Segments category need more inspection
    # what segment?
    segment_id = values["wle4e0xn"]
    if segment_id == "192kpjyq":
      segment = "Book"
    elif segment_id == "12vp06dq":
      segment = "Match"
    elif segment_id == "1py253v1":
      segment = "Ice Cube"
    else:
      return False

    # what scope?
    scope_id = values["0nwdwvd8"]
    if scope_id == "1gn65v8l":
      scope = "Any%"
    elif scope_id == "qznw988q":
      scope = "100%"
    else:
      return False

    # Combine segment and scope
    return f"{segment} Segment {scope}"
  return False

def get_username(id):
  if id in username_dict:
    return username_dict[id]

  user_json = get_json(f"https://www.speedrun.com/api/v1/users/{id}")
  username = user_json.get("data").get("names").get("international")
  username_dict[id] = username
  return username

def fetch_fullgame_runs():
    # fetch every run first
    next_url = f"{API_URL}/runs?game={GAME_ID}&max={PAGE_SIZE}"
    runs = []
    seen_urls = set()

    while next_url:
        if next_url in seen_urls:
            raise RuntimeError(f"URL already seen: {next_url}")
        seen_urls.add(next_url)

        page = get_json(next_url)
        for run in page["data"]:
            # filter out all IL's;
            if not(run.get("level") is None):
              continue
            # filter out rejected/pending runs
            if run.get("status", {}).get("status") != "verified":
              continue
            # filter out non-RTA runs
            if run.get("values").get("onv6e958", {}) != "810785ol":
              continue

            # pre-check categories
            values = run.get("values")
            category = run.get("category")
            decoded_category = decode_categories(run.get("values"), run.get("category"))

            if not(decoded_category):
              # If: some weird category from 2019, skip it
              continue

            # Filter attributes that we need
            filtered_run = {
                "player": get_username(run.get("players")[0].get("id")),
                "date-time": run.get("date-time"),
                "RTA_time": int(float(run.get("times", {}).get("realtime_t"))*1000),
                # uncomment these three when debugging
                # "weblink": run.get("weblink"),
                # "values": values,
                # "level_one_category": category,
                "category": decoded_category
            }

            runs.append(filtered_run)

        # because we can only pull 200 runs at a time, we have to update the URL to pull the next series of runs until we read all of them
        next_url = next(
            (
                link["uri"]
                for link in page["pagination"]["links"]
                if link.get("rel") == "next"
            ),
            None,
        )

    return runs

# Storing known users in a global dict
username_dict = dict() # keys = id, values = username

def main():
    runs = fetch_fullgame_runs()
    with open("runs.json", 'w') as f:
      json.dump(runs, f, indent=4)


if __name__ == "__main__":
    main()
