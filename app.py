from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask import Flask, request, jsonify
from flask_marshmallow import Marshmallow
from marshmallow import fields
from datetime import datetime

# Init app
app = Flask(__name__)

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///park.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app)

# Init ma
ma = Marshmallow(app)


# Driver Class/Model
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=func.now())

    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        return f"<driver{self.id}>"


# Driver Schema
class DriverSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'created_at', 'updated_at')
        datetimeformat = '%d-%m-%YT%H:%M:%S%z'


# Init schema
driver_schema = DriverSchema()
drivers_schema = DriverSchema(many=True)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    plate_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=func.now())
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    driver = db.relationship("Driver", backref="vehicles")

    def __init__(self, make, model, plate_number, driver_id):
        self.make = make
        self.model = model
        self.plate_number = plate_number
        self.driver_id = driver_id

    def __repr__(self):
        return f"<vehicle{self.id}>"



# Vehicle Schema
class VehicleSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    driver_id = fields.Int(dump_only=True)

    class Meta:
        fields = ('id', 'make', 'model', 'plate_number', 'created_at', 'updated_at', 'driver_id')
        dateformat = '%Y-%Y-%m-%dT%H:%M:%S%z'

# Init schema
vehicle_schema = VehicleSchema()
vehicles_schema = VehicleSchema(many=True)


# Get all drivers
@app.get('/drivers/driver')
def get_drivers():
    drivers = Driver.query.all()
    if created_at_gte := request.args.get("created_at_gte"):
        drivers = drivers.filter(Driver.created_at >= created_at_gte)
    if created_at_lte := request.args.get("created_at_lte"):
        drivers = drivers.filter(Driver.created_at <= created_at_lte)
    return jsonify(drivers_schema.dump(drivers))

# Get the single driver
@app.route('/drivers/driver/<id>', methods=['GET'])
def get_driver(id):
    driver = Driver.query.get(id)
    result = driver_schema.dump(driver)
    return jsonify(result)


# Add a driver
@app.route("/drivers/driver", methods=["POST"])
def add_driver():
    try:
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        new_driver = Driver(first_name, last_name)
        db.session.add(new_driver)
        db.session.flush()
        db.session.commit()
        return driver_schema.jsonify(new_driver)
    except:
        db.session.rollback()
        return "error of adding to DB"


# Update the driver
@app.route('/drivers/driver/<id>', methods=['PUT'])
def update_driver(id):
    driver = Driver.query.get(id)
    first_name = request.json['first_name']
    last_name = request.json['last_name']

    driver.first_name = first_name
    driver.last_name = last_name

    db.session.commit()

    return driver_schema.jsonify(driver)


# Delete the driver
@app.route('/drivers/driver/<id>', methods=['DELETE'])
def delete_driver(id):
    driver = Driver.query.get(id)
    db.session.delete(driver)
    db.session.commit()
    return driver_schema.jsonify(driver)

# ///////////////////////////////////////////////////////////////////////////////////////


# Get all vehicles
@app.route('/vehicles/vehicle', methods=['GET'])
def get_vehicles():
    vehicles = Vehicle.query
    if request.args.get("with_drivers") == "yes":
        vehicles = vehicles.filter(Vehicle.driver_id.isnot(None))
    if request.args.get("with_drivers") == "no":
        vehicles = vehicles.filter(Vehicle.driver_id.is_(None))
    return jsonify(vehicles_schema.dump(vehicles.all()))

# Get the single vehicle
@app.route('/vehicles/vehicle/<id>', methods=['GET'])
def get_vehicle(id):
    vehicle = Vehicle.query.get(id)
    result = vehicle_schema.dump(vehicle)
    return jsonify(result)


# Add a vehicle
@app.route("/vehicles/vehicle", methods=["POST"])
def add_vehicle():
    try:
        make = request.json['make']
        model = request.json['model']
        plate_number = request.json['plate_number']
        driver_id = request.json['driver_id']
        new_vehicle = Vehicle(make, model, plate_number, driver_id)
        db.session.add(new_vehicle)
        db.session.flush()
        db.session.commit()
        return vehicle_schema.jsonify(new_vehicle)
    except:
        db.session.rollback()
        return "error of adding to DB"


# Update the vehicle
@app.route('/vehicles/vehicle/<id>', methods=['PUT'])
def update_vehicle(id):
    vehicle = Vehicle.query.get(id)
    make = request.json['make']
    model = request.json['model']
    plate_number = request.json['plate_number']
    driver_id = request.json['driver_id']

    vehicle.make = make
    vehicle.model = model
    vehicle.plate_number = plate_number
    vehicle.driver_id = driver_id

    db.session.commit()
    return vehicle_schema.jsonify(vehicle)


@app.route('/vehicles/set_driver/<vehicle_id>/', methods=['POST'])
def set_vehicle(vehicle_id):
    driver_id = request.json['driver_id']
    vehicle = Vehicle.query.get(vehicle_id)
    if bool(vehicle.driver_id) == bool(driver_id):
        return jsonify(success=False)
    if driver_id is not None and not bool(Driver.query.filter_by(id=driver_id).first()):
        return jsonify(success=False)

    vehicle.driver_id = driver_id
    db.session.commit()
    resp = jsonify(success=True)
    resp.status_code = 200
    return resp

# Delete the vehicle
@app.route('/vehicles/vehicle/<id>', methods=['DELETE'])
def delete_vehicle(id):
    vehicle = Vehicle.query.get(id)
    db.session.delete(vehicle)
    db.session.commit()
    return vehicle_schema.jsonify(vehicle)


# Run Server
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
