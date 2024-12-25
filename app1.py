from flask import Flask, request, jsonify, render_template, send_from_directory
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
import time
import os

app = Flask(__name__)

# Initialize IBM Quantum account
service = QiskitRuntimeService(
    channel="ibm_quantum",
    token="Enter your api token from quantum.ibm.com"
)

# Restricted special characters
allowed_special_chars = "#_$@!"

def binary_to_password(binary_string, length):
    printable_range = list(range(33, 127))  # Printable ASCII range ('!' to '~')
    password = ''
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i + 8]
        char_code = int(byte, 2)
        if 33 <= char_code <= 126:
            char = chr(char_code)
            # Restrict special characters to allowed ones
            if char.isalnum() or char in allowed_special_chars:
                password += char
            else:
                password += "#"  # Default to '#' if the character is not allowed
        else:
            mapped_char = chr(printable_range[char_code % len(printable_range)])
            password += mapped_char
    return password[:length]

def generate_random_bits(num_bits):
    num_qubits = num_bits
    qc = QuantumCircuit(num_qubits, num_qubits)
    for qubit in range(num_qubits):
        qc.h(qubit)
    qc.measure(range(num_qubits), range(num_qubits))
    backend = service.backends()[1]
    transpiled_qc = transpile(qc, backend)
    job = Sampler(backend).run([transpiled_qc])
    result = job.result()
    counts = result[0].data[qc.cregs[0].name].get_counts()
    return counts

def generate_password(length):
    counts = generate_random_bits(length * 8)
    bit_string = max(counts, key=counts.get)
    return binary_to_password(bit_string, length)

@app.route("/")
def index():
    return render_template("password_generator.html")

@app.route("/generate-password", methods=["POST"])
def generate_password_route():
    try:
        length = int(request.form.get("length", 16))
        include_uppercase = request.form.get("options") == "uppercase"
        include_numbers = request.form.get("options") == "numbers"
        include_symbols = request.form.get("options") == "symbols"
        password = generate_password(length)
        if include_uppercase:
            password = ''.join(char.upper() if i % 2 == 0 else char for i, char in enumerate(password))
        if include_numbers:
            password = password[:-1] + str(ord(password[-1]) % 10)
        if include_symbols:
            password = password[:-1] + allowed_special_chars[ord(password[-1]) % 4]  # Use only restricted special characters
        return jsonify({"password": password})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
