import numpy as np
# import matplotlib.pyplot as plt


# This is the new one. It's a decreasing exponential multiplied by a straight line.
def lin_over_ex(x, cumulative=10, x_peak=1):
    b = 1 / x_peak
    a = b ** 2 * cumulative
    density = (a * x) / np.exp(b * x)
    return density


# This is the simple exponential decreasing
def exp_decreasing(x, cumulative=10., starting=1., draw=False):
    a = starting
    b = a / cumulative
    if not draw:
        density = a / np.exp(b * x)
        return density
    chosen_time = np.log(cumulative / (cumulative - x)) / b
    return chosen_time


def fixed_single(x, wait_time):
    if x > wait_time:
        reward = 1
    else:
        reward = 0
    return reward


# if __name__ == '__main__':
#     samples = 100000
#     x = np.random.random(samples)
#     c = 0.5994974874371859
#     times = exp_decreasing(x, cumulative=c, starting=0.1301005025125628, draw=True)
#     plt.hist(times, 50)
#     x2 = np.linspace(0, 30)
#     probs = exp_decreasing(x2, cumulative=c, starting=0.1301005025125628, draw=False)
#     plt.plot(x2, probs*samples)
#     plt.title(f'{np.sum(~np.isnan(times)) / samples * 100}% of samples give reward ({c * 100:.2f}% expected)')
#     plt.show()
