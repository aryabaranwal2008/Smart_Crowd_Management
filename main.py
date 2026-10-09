def predict_queue(current_queue, entry_rate, service_rate, minutes):
    growth_rate = entry_rate - service_rate
    predicted_queue = current_queue + growth_rate * minutes
    return max(0, predicted_queue)


current_queue = int(input("Enter current queue size: "))
entry_rate = float(input("Enter entry rate per minute: "))
service_rate = float(input("Enter service rate per minute: "))
minutes = int(input("Enter prediction time in minutes: "))

result = predict_queue(current_queue, entry_rate, service_rate, minutes)

print("Predicted queue size:", result)