def predict_queue(current_queue, entry_rate, service_rate, minutes):
    growth_rate = entry_rate - service_rate
    predicted_queue = current_queue + growth_rate * minutes
    return max(0, predicted_queue)


current_queue = int(input("Enter current queue size: "))
entry_rate = float(input("Enter entry rate per minute: "))
service_rate = float(input("Enter service rate per minute: "))
minutes = int(input("Enter prediction time in minutes: "))

print("\nQueue prediction over time:")
queue_sizes = []
for minute in range(minutes + 1):
    result = predict_queue(
        current_queue,
        entry_rate,
        service_rate,
        minute
    )
    queue_sizes.append(result)
    print("Minute", minute, ":", result, "people")
print("All predicted queue sizes:",queue_sizes)

import matplotlib.pyplot as plt

time_points = list(range(minutes + 1))

plt.plot(time_points, queue_sizes, marker='o')
plt.xlabel("Time (minutes)")
plt.ylabel("Queue Size (people)")
plt.title("Queue Size vs Time")
plt.grid(True)
plt.show()
