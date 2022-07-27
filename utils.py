import json
import logging
import re
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup

from config import BASELINKER_TOKEN, MULTIPLIER, PRESTA_TOKEN


class BaseLinkerApiError(Exception):
    pass


class PrestaError(Exception):
    pass


def get_product_buy_price(
    presta_token: str, product_id: str, multiplier: float
) -> Optional[float]:
    if not product_id:
        return 0.0
    endpoint = f"products/{product_id}"
    url = f"https://homescreen.pl/api/{endpoint}?ws_key={presta_token}"

    response = requests.request("GET", url)

    soup = BeautifulSoup(response.content, features="xml")

    try:
        tag = soup.find("wholesale_price")
        buy_price = tag.text
        buy_price_float = re.findall("\d+\.\d+", buy_price)
        buy_price_float = buy_price_float[0]
        buy_price_with_multipier = float(buy_price_float) * multiplier
        buy_price_with_multipier = round(float(buy_price_with_multipier), 2)
    except AttributeError:
        raise PrestaError(f"Unable to find wholesale_price for product {product_id}")

    return buy_price_with_multipier


def get_products(baselinker_token: str, order_id: str) -> Union[str, dict]:
    params = {"order_id": order_id}
    method = "getOrders"

    payload = {"method": method, "parameters": json.dumps(params)}
    headers = {"X-BLToken": baselinker_token}

    url = "https://api.baselinker.com/connector.php"
    response = requests.request("POST", url, headers=headers, data=payload)
    if not response.ok:
        raise BaseLinkerApiError(
            f"BaseLinker API responded with code {response.status_code}"
        )
    order = response.json()
    if order["status"].lower() != "success":
        raise BaseLinkerApiError(
            f"POST request to BaseLinker API returned error message: "
            f"{order['error_message']}"
        )

    if not order["orders"]:
        raise BaseLinkerApiError(f"No order with ID: {order_id}")

    products_dict = {}

    for product in order["orders"][0]["products"]:
        products_dict[product["order_product_id"]] = product["product_id"]

    return products_dict


def update_price(
    baselinker_token: str, order_id: str, order_product_id: str, new_price: float
) -> None:
    params = {
        "order_id": order_id,
        "order_product_id": order_product_id,
        "price_brutto": new_price,
    }
    meth = "setOrderProductFields"

    payload = {}
    payload.update({"method": meth, "parameters": json.dumps(params)})
    headers = {"X-BLToken": baselinker_token}

    url = "https://api.baselinker.com/connector.php"
    response = requests.request("POST", url, headers=headers, data=payload)
    if not response.ok:
        raise PrestaError(response.text)
    response = response.json()
    if response["status"].lower() != "success":
        raise PrestaError(response["error_message"])
