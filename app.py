from flask import Flask, Response, jsonify

from config import (
    BASELINKER_TOKEN,
    BASELINKER_URL,
    MULTIPLIER,
    PRESTA_TOKEN,
    PRESTA_URL,
)
from utils import (
    BaseLinkerApiError,
    PrestaError,
    get_product_buy_price,
    get_products,
    update_price,
)

app = Flask(__name__)


@app.route("/order/<order_id>")
def hello_world(order_id: str):
    try:
        products_dict = get_products(BASELINKER_URL, BASELINKER_TOKEN, order_id)
    except BaseLinkerApiError as e:
        return Response(
            f"Unable to get products for order with ID: {order_id}</br>"
            f"Error message: {str(e)}",
            status=400,
        )

    prices_to_update = {}

    for order_product_id, product_id in products_dict.items():
        try:
            new_price = get_product_buy_price(
                PRESTA_URL, PRESTA_TOKEN, product_id, MULTIPLIER
            )
            prices_to_update[order_product_id] = new_price
        except PrestaError as e:
            return Response(
                f"Error while collecting new prices from presta for product ID: {product_id}</br>"
                f"Error message: {str(e)}",
                status=400,
            )

    for order_product_id, new_price in prices_to_update.items():
        try:
            update_price(
                BASELINKER_URL, BASELINKER_TOKEN, order_id, order_product_id, new_price
            )
        except PrestaError as e:
            return Response(
                f"Error while updating price for order product ID: {order_product_id}</br>"
                f"Error message: {str(e)}",
                status=400,
            )
    response = jsonify(prices_to_update)
    response.status_code = 200
    return response


if __name__ == "__main__":
    app.run()
