#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
from marshmallow import Schema, fields, ValidationError
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

@app.before_first_request
def create_tables():
    db.create_all()

class RestaurantPizzaSchema(Schema):
    price = fields.Float(required=True, validate=lambda p: 1 <= p <= 30, error_messages={"validator_failed": "Price must be between 1 and 30."})
    pizza_id = fields.Int(required=True)
    restaurant_id = fields.Int(required=True)

@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class RestaurantList(Resource):
    def get(self):
        try:
            restaurants = Restaurant.query.all()
            return [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants], 200
        except Exception as e:
            return {"error": f"Error fetching restaurants: {str(e)}"}, 500

class RestaurantDetails(Resource):
    def get(self, id):
        try:
            restaurant = db.session.get(Restaurant, id)
            if restaurant:
                return restaurant.to_dict(), 200
            return {"error": "Restaurant not found"}, 404
        except Exception as e:
            return {"error": f"Error fetching restaurant: {str(e)}"}, 500
    
    def delete(self, id):
        try:
            restaurant = db.session.get(Restaurant, id)
            if restaurant:
                db.session.delete(restaurant)
                db.session.commit()
                return {}, 204
            return {"error": "Restaurant not found"}, 404
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error deleting restaurant: {str(e)}"}, 500

class PizzaList(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas], 200

class RestaurantPizzaList(Resource):
    def post(self):
        schema = RestaurantPizzaSchema()
        try:
            data = schema.load(request.get_json())
            
            
            restaurant = db.session.get(Restaurant, data["restaurant_id"])
            pizza = db.session.get(Pizza, data["pizza_id"])
            if not restaurant:
                return {"errors": ["Restaurant does not exist"]}, 404
            if not pizza:
                return {"errors": ["Pizza does not exist"]}, 404
            
            new_restaurant_pizza = RestaurantPizza(
                price=data["price"],
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )
            db.session.add(new_restaurant_pizza)
            db.session.commit()
            return new_restaurant_pizza.to_dict(), 201
        except ValidationError as err:
           
            return {"errors": ["validation errors"]}, 400
        except ValueError as e:
            return {"errors": str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {"errors": f"Unexpected error: {str(e)}"}, 500


api.add_resource(RestaurantList, '/restaurants')
api.add_resource(RestaurantDetails, '/restaurants/<int:id>')
api.add_resource(PizzaList, '/pizzas')
api.add_resource(RestaurantPizzaList, '/restaurant_pizzas')


if __name__ == "__main__":
    app.run(port=5555, debug=True)
