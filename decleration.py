import numpy as np
import matplotlib.pyplot as plt

theta = np.linspace(0, 2*np.pi, 500)
# Circle (pi domain)
x_circle = np.cos(theta)
y_circle = np.sin(theta)

# Golden spiral (phi domain)
phi = (1 + np.sqrt(5)) / 2
theta_spiral = np.linspace(0, 4*np.pi, 1000)
r_spiral = (phi ** (theta_spiral / (2*np.pi))) * 0.05
x_spiral = r_spiral * np.cos(theta_spiral)
y_spiral = r_spiral * np.sin(theta_spiral)

# Plot
fig, ax = plt.subplots(figsize=(6,6))
ax.plot(x_circle, y_circle, 'b-', lw=2, label='π')
ax.plot(x_spiral, y_spiral, 'g-', lw=2, label='φ')
ax.scatter([0],[0], c='red', s=80, marker='o')  # the seal dot
ax.set_aspect('equal')
ax.axis('off')
plt.show()