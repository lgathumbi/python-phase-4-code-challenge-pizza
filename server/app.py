#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    restaurants = Restaurant.query.all()
    restaurants_dict = [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in restaurants]

    return make_response(restaurants_dict, 200)

@app.route('/restaurants/<int:id>', methods=['GET', 'DELETE'])
def get_restaurant_by_id(id):
    restaurant = Restaurant.query.filter(Restaurant.id==id).first()
    if request.method == 'GET':
        if restaurant:
            restaurant_dict = restaurant.to_dict(
                only=('id', 'name', 'address', 'restaurant_pizzas.id', 'restaurant_pizzas.price', 'restaurant_pizzas.pizza_id', 'restaurant_pizzas.restaurant_id', 'restaurant_pizzas.pizza.id', 'restaurant_pizzas.pizza.name', 'restaurant_pizzas.pizza.ingredients')
            )
            return make_response(restaurant_dict, 200)
        else:
            return make_response( {"error": "Restaurant not found"}, 404 )
    elif request.method == 'DELETE':
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return make_response( {'deleted': True}, 204)
        else:
            return make_response( '', 404)

@app.route('/pizzas', methods=['GET'])
def get_pizzas():
    pizzas = Pizza.query.all()
    pizzas_dict = [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in pizzas]

    return make_response(pizzas_dict, 200)    

@app.route('/restaurant_pizzas', methods=['POST'])
def add_restaurant_pizza():
    data = request.get_json()
    
    # Validate input data
    price = data.get('price')
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    if not (price and pizza_id and restaurant_id):
        return make_response( {"errors": ["validation errors"]}, 400)

    try:
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()

        restaurant = Restaurant.query.filter(Restaurant.id==restaurant_id).first()
        pizza = Pizza.query.filter(Pizza.id==pizza_id).first()
        response_data = {
            "id": new_restaurant_pizza.id,
            "price": new_restaurant_pizza.price,
            "pizza_id": new_restaurant_pizza.pizza_id,
            "restaurant_id": new_restaurant_pizza.restaurant_id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            }
        }
        return make_response(response_data, 201)
    except ValueError as e:
        return make_response( {"errors": ["validation errors"]}, 400)

if __name__ == "__main__":
    app.run(port=5555, debug=True)
