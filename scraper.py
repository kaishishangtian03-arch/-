import json
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=+9), "JST")

TARGET_ROUTES = [
    {
        "route_name": "34号系統（大阪駅前 ➔ 守口車庫前）",
        "from_cd": "344",
        "to_cd": "119",
        "target_num": "34号",
    },
    {
        "route_name": "36号系統（大阪駅前 ➔ 地下鉄門真南）",
        "from_cd": "344",
        "to_cd": "820",
        "target_num": "36号",
    },
]


def fetch_live_data():
    route_results = []

    for r in TARGET_ROUTES:
        url = f"https://oc.bus-vision.jp/osakacitybus/view/approach.html?stopCdFrom={r['from_cd']}&stopCdTo={r['to_cd']}&lang=0"
        buses = []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            route_elems = soup.find_all("span", id="routeNm")

            for route_elem in route_elems:
                route_text = route_elem.get_text(strip=True)

                if r["target_num"] not in route_text:
                    continue

                item_container = route_elem.parent
                while (
                    item_container.parent
                    and len(
                        item_container.parent.find_all("span", id="routeNm")
                    )
                    == 1
                ):
                    item_container = item_container.parent

                dep_elem = item_container.find("span", id="passTimeFromText")
                arr_elem = item_container.find("span", id="passTimeToText")
                status_elem = item_container.find("span", id="passInfo")
                id_elem = item_container.find(
                    "input", id="planForecastResultCd"
                )

                buses.append(
                    {
                        "plan_cd": id_elem.get("value", "") if id_elem else "",
                        "route": route_text,
                        "dep_time": dep_elem.get_text(strip=True)
                        if dep_elem
                        else "",
                        "arr_time": arr_elem.get_text(strip=True)
                        if arr_elem
                        else "",
                        "status": status_elem.get_text(strip=True)
                        if status_elem
                        else "発車前",
                    }
                )

        except Exception as e:
            print(f"取得エラー ({r['route_name']}): {e}")

        route_results.append({"route_name": r["route_name"], "buses": buses})

    web_data = {
        "updated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S"),
        "routes": route_results,
    }

    # data.js ファイルに書き出し
    with open("data.js", "w", encoding="utf-8") as f:
        f.write(
            f"const data = {json.dumps(web_data, ensure_ascii=False, indent=4)};"
        )


if __name__ == "__main__":
    fetch_live_data()