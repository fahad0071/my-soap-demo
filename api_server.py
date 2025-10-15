from flask import Flask, request, jsonify
from zeep import Client
from zeep.exceptions import Fault
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow all origins



CUSTOM_SOAP_WSDL = 'http://localhost:8000/?wsdl'
TEMP_THIRD_PARTY_WSDL = 'https://www.w3schools.com/xml/tempconvert.asmx?WSDL'
CALC_THIRD_PARTY_WSDL = 'http://www.dneonline.com/calculator.asmx?WSDL'
custom_client = Client(CUSTOM_SOAP_WSDL)
temp_third_party_client = Client(TEMP_THIRD_PARTY_WSDL)
calc_third_party_client = Client(CALC_THIRD_PARTY_WSDL)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    if not data or 'from_currency' not in data or 'to_currency' not in data or 'amount' not in data:
        return jsonify({'error': 'Invalid JSON or missing fields'}), 400
    try:
        from_currency = data['from_currency'].upper()
        to_currency = data['to_currency'].upper()
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400

        # Fallback to custom SOAP (no third-party currency for now)
        result = custom_client.service.convert_currency(from_currency, to_currency, amount)
        rate = result / amount if amount > 0 else 0
        return jsonify({
            'result': result,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'amount': amount,
            'rate': rate,
            'source': 'custom'
        })

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Fault as f:
        return jsonify({'error': f.message, 'source': 'both failed'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal error: ' + str(e)}), 500

@app.route('/rates', methods=['GET'])
def rates():
    base_currency = request.args.get('base_currency', 'USD').upper()
    try:
        rates_list = custom_client.service.get_rates(base_currency)
        rates_dict = {rate['currency']: rate['rate'] for rate in rates_list}
        return jsonify({
            'base_currency': base_currency,
            'rates': rates_dict,
            'source': 'custom'
        })

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Fault as f:
        return jsonify({'error': f.message, 'source': 'both failed'}), 404
    except Exception as e:
        return jsonify({'error': 'Internal error: ' + str(e)}), 500

@app.route('/convert_temp', methods=['POST'])
def convert_temp():
    data = request.json
    if not data or 'from_unit' not in data or 'to_unit' not in data or 'value' not in data:
        return jsonify({'error': 'Invalid JSON or missing fields'}), 400
    try:
        from_unit = data['from_unit'].upper()
        to_unit = data['to_unit'].upper()
        value = float(data['value'])
        if from_unit not in ['C', 'F'] or to_unit not in ['C', 'F']:
            return jsonify({'error': 'Invalid unit (use C or F)'}), 400
        if from_unit == to_unit:
            return jsonify({'error': 'From and to units must differ'}), 400

        try:
            if from_unit == 'C' and to_unit == 'F':
                result = temp_third_party_client.service.CelsiusToFahrenheit(value)
            elif from_unit == 'F' and to_unit == 'C':
                result = temp_third_party_client.service.FahrenheitToCelsius(value)
            else:
                raise ValueError("Unsupported conversion")
            return jsonify({
                'result': result,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'value': value,
                'source': 'third-party'
            })
        except Fault as f:
            return jsonify({'error': f.message, 'source': 'third-party failed'}), 500

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal error: ' + str(e)}), 500

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    if not data or 'operation' not in data or 'intA' not in data or 'intB' not in data:
        return jsonify({'error': 'Invalid JSON or missing fields'}), 400
    try:
        operation = data['operation'].lower()
        intA = int(data['intA'])
        intB = int(data['intB'])
        if operation not in ['add', 'subtract', 'multiply', 'divide']:
            return jsonify({'error': 'Invalid operation (use add, subtract, multiply, divide)'}), 400
        if operation == 'divide' and intB == 0:
            return jsonify({'error': 'Division by zero'}), 400

        try:
            if operation == 'add':
                result = calc_third_party_client.service.Add(intA, intB)
            elif operation == 'subtract':
                result = calc_third_party_client.service.Subtract(intA, intB)
            elif operation == 'multiply':
                result = calc_third_party_client.service.Multiply(intA, intB)
            elif operation == 'divide':
                result = calc_third_party_client.service.Divide(intA, intB)
            return jsonify({
                'result': result,
                'operation': operation,
                'intA': intA,
                'intB': intB,
                'source': 'third-party'
            })
        except Fault as f:
            return jsonify({'error': f.message, 'source': 'third-party failed'}), 500

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal error: ' + str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)