from flask import Flask, request, jsonify, send_from_directory
from zeep import Client
from zeep.exceptions import Fault
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# 👇 After deploying the SOAP service, update this URL with your Render SOAP endpoint
CUSTOM_SOAP_WSDL = 'https://your-soap-service-name.onrender.com/?wsdl'
TEMP_THIRD_PARTY_WSDL = 'https://www.w3schools.com/xml/tempconvert.asmx?WSDL'
CALC_THIRD_PARTY_WSDL = 'http://www.dneonline.com/calculator.asmx?WSDL'

custom_client = Client(CUSTOM_SOAP_WSDL)
temp_client = Client(TEMP_THIRD_PARTY_WSDL)
calc_client = Client(CALC_THIRD_PARTY_WSDL)


@app.route('/')
def home():
    return send_from_directory('.', 'index.html')


@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    try:
        result = custom_client.service.convert_currency(
            data['from_currency'], data['to_currency'], float(data['amount'])
        )
        return jsonify({
            'from_currency': data['from_currency'],
            'to_currency': data['to_currency'],
            'amount': data['amount'],
            'result': result
        })
    except Fault as fault:
        return jsonify({'error': str(fault)}), 500


@app.route('/rates', methods=['GET'])
def get_rates():
    base_currency = request.args.get('base_currency', 'USD')
    try:
        rates = custom_client.service.get_rates(base_currency)
        result = {rate.currency: rate.rate for rate in rates}
        return jsonify({'base_currency': base_currency, 'rates': result})
    except Fault as fault:
        return jsonify({'error': str(fault)}), 500


@app.route('/convert_temp', methods=['POST'])
def convert_temp():
    data = request.json
    from_unit = data['from_unit']
    to_unit = data['to_unit']
    value = float(data['value'])

    try:
        if from_unit == 'C' and to_unit == 'F':
            result = temp_client.service.CelsiusToFahrenheit(str(value))
        elif from_unit == 'F' and to_unit == 'C':
            result = temp_client.service.FahrenheitToCelsius(str(value))
        else:
            return jsonify({'error': 'Invalid conversion units'}), 400

        return jsonify({'from_unit': from_unit, 'to_unit': to_unit, 'value': value, 'result': result})
    except Fault as fault:
        return jsonify({'error': str(fault)}), 500


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    op = data['operation']
    a = int(data['intA'])
    b = int(data['intB'])

    try:
        if op == 'add':
            result = calc_client.service.Add(a, b)
        elif op == 'subtract':
            result = calc_client.service.Subtract(a, b)
        elif op == 'multiply':
            result = calc_client.service.Multiply(a, b)
        elif op == 'divide':
            result = calc_client.service.Divide(a, b)
        else:
            return jsonify({'error': 'Invalid operation'}), 400

        return jsonify({'operation': op, 'intA': a, 'intB': b, 'result': result})
    except Fault as fault:
        return jsonify({'error': str(fault)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 API server running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)
